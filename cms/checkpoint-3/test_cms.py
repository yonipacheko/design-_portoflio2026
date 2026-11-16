import base64
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlsplit, parse_qs

from itsdangerous import TimestampSigner
from starlette.testclient import TestClient
from app import create_app, ALLOWED_USER
from store import Store, rendering

SECRET = 'test-fixture-signing-key-not-used-by-the-preview'
BASE = 'http://127.0.0.1:4194'


class CMSTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.database = Path(self.folder.name) / 'content.sqlite3'
        self.app = create_app(self.database, {'CMS_SESSION_SECRET': SECRET})
        self.client = TestClient(self.app, base_url=BASE)
        self.store = self.app.state.store

    def tearDown(self):
        self.client.close()
        self.folder.cleanup()

    def authenticate(self, user_id=ALLOWED_USER):
        sid = self.store.session(user_id)
        encoded = base64.b64encode(json.dumps({'sid': sid}).encode())
        cookie = TimestampSigner(SECRET).sign(encoded).decode()
        self.client.cookies.set('portfolio_cms', cookie)
        user = self.store.identity(sid)
        return {'Origin': BASE, 'X-CSRF-Token': user['csrf']}

    def test_signed_out_editor_and_mutations_are_protected(self):
        self.assertEqual(self.client.get('/admin', follow_redirects=False).status_code, 303)
        for url in ['/api/me', '/api/versions', '/admin/preview/fintech', '/admin/preview/fintech/projects.js']:
            self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(self.client.post('/api/versions/fintech/publish', json={'revision': 1}).status_code, 401)
        self.assertEqual(self.client.get('/auth/github').status_code, 503)
        self.assertIn('setup is pending', self.client.get('/admin/login').text)

    def test_only_owner_identity_can_edit(self):
        self.authenticate(user_id=123)
        self.assertEqual(self.client.get('/api/versions').status_code, 401)

    def test_csrf_and_origin_are_required(self):
        headers = self.authenticate()
        url = '/api/versions/fintech/publish'
        self.assertEqual(self.client.post(url, json={'revision': 1}).status_code, 403)
        self.assertEqual(self.client.post(url, headers={**headers, 'Origin': 'https://other.example'}, json={'revision': 1}).status_code, 403)
        self.assertEqual(self.store.get('fintech')['revision'], 1)

    def test_save_preview_publish_and_restart(self):
        headers = self.authenticate()
        old_page = self.client.get('/for/fintech').text
        draft = deepcopy(rendering.SEED)
        draft['headline'] = 'A newly saved design message'
        draft['project_ids'] = ['07', '06']
        draft['internal_name'] = 'PRIVATE CLIENT TARGET'
        result = self.client.post('/api/versions/fintech/save', headers=headers, json={'draft': draft, 'revision': 1})
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()['has_changes'])
        self.assertEqual(self.client.get('/for/fintech').text, old_page)
        self.assertIn(draft['headline'], self.client.get('/admin/preview/fintech').text)
        self.assertNotIn('PRIVATE CLIENT TARGET', self.client.get('/admin/preview/fintech').text)
        # Reopening the persisted store must preserve both snapshots.
        self.assertEqual(Store(self.database).get('fintech')['draft'], draft)
        result = self.client.post('/api/versions/fintech/publish', headers=headers, json={'revision': 2})
        self.assertEqual(result.status_code, 200)
        page = self.client.get('/for/fintech').text
        self.assertIn(draft['headline'], page)
        self.assertNotIn('PRIVATE CLIENT TARGET', page)
        payload = self.client.get('/for/fintech/projects.js').text
        selected = json.loads(payload.split(' = ', 1)[1].rstrip(';\n'))
        self.assertEqual([p['number'] for p in selected], ['07', '06'])

    def test_stale_publish_is_rejected(self):
        headers = self.authenticate()
        draft = dict(rendering.SEED, headline='Another tab changed this')
        self.store.save('fintech', draft, 1)
        self.assertEqual(self.client.post('/api/versions/fintech/publish', headers=headers, json={'revision': 1}).status_code, 409)
        self.assertEqual(self.store.get('fintech')['published'], rendering.SEED)

    def test_editor_text_does_not_execute_or_break_rendering(self):
        headers = self.authenticate()
        draft = dict(rendering.SEED, headline=r'<script>alert(1)</script> \g<1>', intro='Text with <markup> & quotes')
        result = self.client.post('/api/versions/fintech/save', headers=headers, json={'draft': draft, 'revision': 1})
        self.assertEqual(result.status_code, 200)
        html = self.client.get('/admin/preview/fintech').text
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('\\g&lt;1&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)

    def test_published_slug_and_project_rules(self):
        headers = self.authenticate()
        for patch in ({'slug': 'another-slug'}, {'project_ids': []}, {'project_ids': ['01', '01']}, {'project_ids': ['99']}):
            draft = dict(rendering.SEED, **patch)
            self.assertEqual(self.client.post('/api/versions/fintech/save', headers=headers, json={'draft': draft, 'revision': 1}).status_code, 400)

    def test_logout_revokes_session(self):
        headers = self.authenticate()
        cookie = self.client.cookies.get('portfolio_cms')
        self.assertEqual(self.client.post('/api/logout', headers=headers, json={}).status_code, 200)
        self.client.cookies.set('portfolio_cms', cookie)
        self.assertEqual(self.client.get('/api/versions').status_code, 401)

    def test_shared_files_and_database_is_not_public(self):
        for name in ['project-06.html', 'styles.css', 'analytics.js']:
            self.assertEqual(self.client.get('/' + name).content, (rendering.PORTFOLIO / name).read_bytes())
        self.assertEqual(self.client.get('/local-content.sqlite3').status_code, 404)

    def test_github_request_uses_state_and_pkce(self):
        app = create_app(self.database, {'CMS_SESSION_SECRET': SECRET, 'GITHUB_CLIENT_ID': 'fixture-client', 'GITHUB_CLIENT_SECRET': 'fixture-secret'})
        with TestClient(app, base_url=BASE) as client:
            response = client.get('/auth/github', follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            params = parse_qs(urlsplit(response.headers['location']).query)
            self.assertIn('state', params)
            self.assertIn('code_challenge', params)
            self.assertEqual(params['code_challenge_method'], ['S256'])
            self.assertNotIn('repo', params.get('scope', []))
            self.assertIn('httponly', response.headers['set-cookie'].lower())


if __name__ == '__main__':
    unittest.main()
