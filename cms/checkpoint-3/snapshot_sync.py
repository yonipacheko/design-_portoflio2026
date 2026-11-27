"""Persist published portfolio pages as static repository snapshots."""
import base64
import json
import logging
import os
from urllib import request, error

from store import rendering

LOG = logging.getLogger('cms.snapshots')
REPOSITORY = os.getenv('SNAPSHOT_REPOSITORY', 'yonipacheko/design-_portoflio2026')
BRANCH = os.getenv('SNAPSHOT_BRANCH', 'cms/checkpoint-4-versions')
TOKEN = os.getenv('SNAPSHOT_GITHUB_TOKEN', '')


def _github(path, method='GET', body=None):
    if not TOKEN:
        raise RuntimeError('SNAPSHOT_GITHUB_TOKEN is not configured')
    url = f'https://api.github.com/repos/{REPOSITORY}/contents/{path}'
    if method == 'GET':
        url += '?ref=' + BRANCH
    payload = json.dumps(body).encode() if body is not None else None
    req = request.Request(url, data=payload, method=method, headers={
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {TOKEN}',
        'User-Agent': 'fernando-portfolio-cms',
        'X-GitHub-Api-Version': '2022-11-28',
        **({'Content-Type': 'application/json'} if body is not None else {}),
    })
    with request.urlopen(req, timeout=15) as response:
        return json.loads(response.read())


def _put(path, content, message):
    sha = None
    try:
        sha = _github(path).get('sha')
    except error.HTTPError as exc:
        if exc.code != 404:
            raise
    body = {
        'message': message,
        'content': base64.b64encode(content).decode(),
        'branch': BRANCH,
    }
    if sha:
        body['sha'] = sha
    return _github(path, 'PUT', body)


def sync_published_snapshot(content):
    """Write the public HTML and project data for one published version."""
    slug = content['slug']
    html = rendering.render(content).replace(
        'Checkpoint 2 · Saved local version · Not published',
        'Fernando Studio · published version',
    )
    html = html.replace('/for/' + slug + '/projects.js', '/for/' + slug + '/projects.js')
    _put(f'dist/for/{slug}/index.html', html, f'Update published snapshot: {slug}')
    _put(f'dist/for/{slug}/projects.js', rendering.selected_projects(content), f'Update published projects: {slug}')

