"""Checkpoint-three local CMS. No production deployment or auth bypass."""
from pathlib import Path
from urllib.parse import urlsplit
import json
import secrets
import logging

from authlib.integrations.starlette_client import OAuth
from starlette.applications import Starlette
from starlette.config import Config
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response, FileResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from store import Store, Conflict, rendering
from remote_store import RemoteVersionStore

ROOT = Path(__file__).resolve().parent
ALLOWED_USER = 3479404  # Public GitHub numeric account ID for yonipacheko.


class ResponseHeaders(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Robots-Tag'] = 'noindex'
        return response


def create_app(database=None, settings=None):
    config = settings if settings is not None else Config(str(ROOT / '.env') if (ROOT / '.env').exists() else None)
    get = lambda key, default='': config.get(key, default) if isinstance(config, dict) else config(key, default=default)
    base = get('CMS_BASE_URL', 'http://127.0.0.1:4194').rstrip('/')
    storage_mode = get('CMS_STORAGE', 'sqlite').lower()
    if storage_mode not in {'sqlite', 'supabase'}:
        raise RuntimeError('CMS_STORAGE must be sqlite or supabase')
    secret = get('CMS_SESSION_SECRET')
    if not secret:
        # An ignored, local signing key persists across restarts; never printed.
        key_file = ROOT / '.session-key'
        if not key_file.exists():
            with key_file.open('x') as f:
                f.write(secrets.token_urlsafe(48))
            key_file.chmod(0o600)
        secret = key_file.read_text()
    store = RemoteVersionStore(rendering.SEED) if storage_mode == 'supabase' else Store(database or ROOT / 'local-content.sqlite3')
    oauth = OAuth()
    client_id, client_secret = get('GITHUB_CLIENT_ID'), get('GITHUB_CLIENT_SECRET')
    ready = bool(client_id and client_secret)
    oauth.register('github', client_id=client_id, client_secret=client_secret,
                   authorize_url='https://github.com/login/oauth/authorize',
                   access_token_url='https://github.com/login/oauth/access_token',
                   api_base_url='https://api.github.com/',
                   client_kwargs={'scope': '', 'code_challenge_method': 'S256'})

    def identity(request):
        user = store.identity(request.session.get('sid', ''))
        if not user or user['id'] != ALLOWED_USER:
            raise HTTPException(401, 'Sign in required')
        return user

    def mutation(request):
        user = identity(request)
        if request.headers.get('origin') != base or not secrets.compare_digest(request.headers.get('x-csrf-token', ''), user['csrf']):
            raise HTTPException(403, 'Request verification failed')
        return user

    async def home(request):
        try:
            identity(request)
        except HTTPException:
            return RedirectResponse('/admin/login', 303)
        return FileResponse(ROOT / 'static' / 'index.html')

    async def versions_page(request):
        identity(request)
        return FileResponse(ROOT / 'static' / 'versions.html')

    async def login(request):
        extra = '<a class="primary button" href="/auth/github">Continue with GitHub</a>' if ready else '<p><strong>GitHub setup is pending.</strong> The editor stays locked until the local OAuth application is configured.</p><p>No password or secret should be entered into this page.</p>'
        return HTMLResponse('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Portfolio CMS sign-in</title><link rel="stylesheet" href="/admin/static/style.css"><main><p class="eyebrow">CHECKPOINT 3 · LOCAL ONLY</p><h1>Your portfolio studio.</h1><p>Private editing for yonipacheko. Visitors never need to sign in.</p>' + extra + '<p style="margin-top:24px"><a href="/for/fintech">View the local published version</a></p></main></html>')

    async def github(request):
        if not ready:
            raise HTTPException(503, 'GitHub OAuth is not configured')
        return await oauth.github.authorize_redirect(request, base + '/auth/github/callback', login='yonipacheko', allow_signup='false')

    async def callback(request):
        if not ready:
            raise HTTPException(503, 'GitHub OAuth is not configured')
        stage = 'token exchange'
        try:
            token = await oauth.github.authorize_access_token(request)
            stage = 'profile lookup'
            profile_response = await oauth.github.get('user', token=token)
            profile_response.raise_for_status()
            profile = profile_response.json()
        except Exception as exc:
            # Never log exception messages, URLs, tokens or callback parameters.
            logging.getLogger('cms.auth').warning('GitHub sign-in failed during %s (%s)', stage, type(exc).__name__)
            request.session.clear()
            raise HTTPException(401, 'GitHub sign-in failed. Try signing in again.')
        if profile.get('id') != ALLOWED_USER:
            request.session.clear()
            raise HTTPException(403, 'This GitHub account cannot edit this portfolio')
        old = request.session.get('sid')
        if old:
            store.logout(old)
        request.session.clear()
        request.session['sid'] = store.session(profile['id'])
        # GitHub access tokens are not kept in the browser cookie or database.
        return RedirectResponse('/admin', 303)

    async def me(request):
        user = identity(request)
        return JSONResponse({'login': 'yonipacheko', 'csrf': user['csrf']})

    async def logout(request):
        mutation(request)
        store.logout(request.session.get('sid', ''))
        request.session.clear()
        return JSONResponse({'ok': True})

    async def versions(request):
        identity(request)
        return JSONResponse({'versions': store.list(), 'projects': list(rendering.CATALOG.values())})

    async def duplicate(request):
        mutation(request)
        try:
            data = await request.json()
            value = store.duplicate(data['source_slug'], data['slug'], data['internal_name'])
        except (ValueError, KeyError, TypeError):
            raise HTTPException(400, 'Choose a unique link and internal name.')
        return JSONResponse(value, status_code=201)

    async def archive(request):
        mutation(request)
        try:
            return JSONResponse(store.archive(request.path_params['slug']))
        except (ValueError, KeyError) as e:
            raise HTTPException(400, str(e))

    async def lifecycle(request):
        mutation(request)
        try:
            fn = store.unpublish if request.url.path.endswith('/unpublish') else store.restore
            return JSONResponse(fn(request.path_params['slug']))
        except (ValueError, KeyError) as e:
            raise HTTPException(400, str(e))

    async def change(request):
        mutation(request)
        if request.headers.get('content-type', '').split(';')[0] != 'application/json':
            raise HTTPException(415, 'JSON required')
        body = b''
        async for chunk in request.stream():
            body += chunk
            if len(body) > 12000:
                raise HTTPException(413, 'Content is too large')
        try:
            data = json.loads(body)
            revision = data['revision']
            if type(revision) is not int:
                raise ValueError('Invalid revision')
            if request.path_params['action'] == 'save':
                value = store.save(request.path_params['slug'], data['draft'], revision)
            elif request.path_params['action'] == 'publish':
                value = store.publish(request.path_params['slug'], revision)
            else:
                raise HTTPException(404)
        except Conflict as e:
            raise HTTPException(409, str(e))
        except (ValueError, KeyError, TypeError):
            raise HTTPException(400, 'Invalid content. Use one to three available projects and valid text fields.')
        return JSONResponse(value)

    async def version(request):
        is_preview = request.url.path.startswith('/admin/preview/')
        if is_preview:
            identity(request)
        try:
            record = store.get(request.path_params['slug'])
        except KeyError:
            return HTMLResponse('<h1>This portfolio version is unavailable.</h1><a href="/">View the general portfolio</a>', 404)
        if not is_preview and record['status'] != 'live':
            return HTMLResponse('<h1>This portfolio version is unavailable.</h1><a href="/">View the general portfolio</a>', 404)
        content = record['draft' if is_preview else 'published']
        if request.path_params.get('asset') == 'projects.js':
            return Response(rendering.selected_projects(content), media_type='text/javascript')
        html = rendering.render(content).decode().replace('Checkpoint 2 · Saved local version · Not published', 'Checkpoint 3 · Local ' + ('draft preview' if is_preview else 'published version') + ' · Not on production')
        if is_preview:
            html = html.replace('/for/' + content['slug'] + '/projects.js', '/admin/preview/' + content['slug'] + '/projects.js')
        return HTMLResponse(html)

    async def http_error(request, exception):
        return JSONResponse({'error': exception.detail}, status_code=exception.status_code)

    routes = [Route('/admin', home), Route('/admin/', home), Route('/admin/versions', versions_page), Route('/admin/login', login),
              Route('/auth/github', github), Route('/auth/github/callback', callback),
              Route('/api/me', me), Route('/api/logout', logout, methods=['POST']),
              Route('/api/versions', versions), Route('/api/versions/duplicate', duplicate, methods=['POST']),
              Route('/api/versions/{slug}/archive', archive, methods=['POST']),
              Route('/api/versions/{slug}/unpublish', lifecycle, methods=['POST']),
              Route('/api/versions/{slug}/restore', lifecycle, methods=['POST']),
              Route('/api/versions/{slug}/{action}', change, methods=['POST']),
              Route('/admin/preview/{slug}', version), Route('/admin/preview/{slug}/{asset}', version),
              Mount('/admin/static', app=StaticFiles(directory=ROOT / 'static')),
              Route('/for/{slug}', version), Route('/for/{slug}/{asset}', version),
              Mount('/', app=StaticFiles(directory=rendering.PORTFOLIO, html=True))]
    host = urlsplit(base).hostname or '127.0.0.1'
    allowed_hosts = [host, '127.0.0.1', 'localhost']
    middleware = [Middleware(ResponseHeaders), Middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts),
                  Middleware(SessionMiddleware, secret_key=secret, session_cookie='portfolio_cms', same_site='lax', https_only=urlsplit(base).scheme == 'https', max_age=3600)]
    app = Starlette(routes=routes, middleware=middleware, exception_handlers={HTTPException: http_error})

    app.state.store, app.state.oauth = store, oauth
    return app


app = create_app()
