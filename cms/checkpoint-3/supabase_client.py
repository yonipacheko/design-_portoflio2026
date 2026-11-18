"""Small server-side Supabase REST client for CMS version records.

The service-role key is read only from the environment and is never returned
to callers or sent to browser code.
"""
import json
import os
from urllib import request
from urllib.error import HTTPError, URLError


class SupabaseError(RuntimeError):
    pass


class SupabaseClient:
    def __init__(self, url=None, service_key=None):
        self.url = (url or os.environ.get('SUPABASE_URL', '')).rstrip('/')
        self.service_key = service_key or os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
        if not self.url or not self.service_key:
            raise SupabaseError('Supabase environment is not configured')

    def _request(self, method, path, payload=None, headers=None):
        body = None if payload is None else json.dumps(payload).encode()
        req = request.Request(self.url + path, data=body, method=method)
        req.add_header('apikey', self.service_key)
        req.add_header('Authorization', 'Bearer ' + self.service_key)
        req.add_header('Content-Type', 'application/json')
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        try:
            with request.urlopen(req, timeout=10) as response:
                raw = response.read()
        except (HTTPError, URLError) as exc:
            raise SupabaseError('Supabase request failed') from exc
        return json.loads(raw) if raw else None

    def list_versions(self):
        return self._request('GET', '/rest/v1/portfolio_versions?select=*&order=slug.asc')

    def get_version(self, slug):
        rows = self._request('GET', '/rest/v1/portfolio_versions?select=*&slug=eq.' + slug)
        return rows[0] if rows else None

    def create_version(self, record):
        rows = self._request('POST', '/rest/v1/portfolio_versions', record, {'Prefer': 'return=representation'})
        return rows[0]

    def update_version(self, slug, record, revision):
        path = '/rest/v1/portfolio_versions?slug=eq.' + slug + '&revision=eq.' + str(revision)
        rows = self._request('PATCH', path, record, {'Prefer': 'return=representation'})
        if not rows:
            raise SupabaseError('Version changed or no longer exists')
        return rows[0]

    def healthcheck(self):
        self._request('GET', '/rest/v1/portfolio_versions?select=slug&limit=1')
        return True

    def create_session(self, session):
        rows = self._request('POST', '/rest/v1/cms_sessions', session, {'Prefer': 'return=representation'})
        return rows[0]

    def get_session(self, sid):
        rows = self._request('GET', '/rest/v1/cms_sessions?select=*&sid=eq.' + sid)
        return rows[0] if rows else None

    def delete_session(self, sid):
        self._request('DELETE', '/rest/v1/cms_sessions?sid=eq.' + sid)
