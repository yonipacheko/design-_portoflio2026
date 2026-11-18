"""Hosted Supabase-backed Store-compatible adapter for the CMS."""
import json
import secrets
import time
from copy import deepcopy
from supabase_client import SupabaseClient, SupabaseError
from store import Conflict, rendering


class RemoteVersionStore:
    def __init__(self, seed):
        self.client = SupabaseClient()
        self.seed = seed

    @staticmethod
    def _record(row):
        draft = row.get('draft') or {k: row[k] for k in ('slug', 'internal_name', 'headline', 'intro', 'project_ids')}
        published = row.get('published') or deepcopy(draft)
        return {'slug': row['slug'], 'draft': draft, 'published': published,
                'revision': row.get('revision', 1), 'status': row.get('status', 'draft'),
                'has_changes': draft != published}

    def get(self, slug):
        row = self.client.get_version(slug)
        if not row:
            raise KeyError(slug)
        return self._record(row)

    def list(self):
        return [self._record(row) for row in self.client.list_versions()]

    def healthcheck(self):
        return self.client.healthcheck()

    def _patch(self, slug, revision, values):
        path = '/rest/v1/portfolio_versions?slug=eq.' + slug + '&revision=eq.' + str(revision)
        rows = self.client._request('PATCH', path, {**values, 'revision': revision + 1}, {'Prefer': 'return=representation'})
        if not rows:
            raise Conflict('This version changed in another tab. Reload before saving.')
        return self._record(rows[0])

    def save_draft(self, slug, draft, revision):
        return self._patch(slug, revision, {'draft': draft})

    def publish(self, slug, revision):
        current = self.get(slug)
        return self._patch(slug, revision, {'published': current['draft'], 'status': 'live'})

    def set_status(self, slug, status, revision):
        if status not in {'live', 'offline', 'archived'}:
            raise ValueError('Invalid version status')
        return self._patch(slug, revision, {'status': status})

    def create_session(self, sid, user_id, csrf, expires):
        return self.client.create_session({'sid': sid, 'user_id': user_id, 'csrf': csrf, 'expires': expires})

    def get_session(self, sid):
        return self.client.get_session(sid)

    def delete_session(self, sid):
        self.client.delete_session(sid)

    def session(self, user_id):
        sid, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        self.create_session(sid, user_id, csrf, int(time.time()) + 3600)
        return sid

    def identity(self, sid):
        row = self.get_session(sid)
        if not row or row['expires'] <= int(time.time()):
            return None
        return {'id': row['user_id'], 'csrf': row['csrf']}

    def logout(self, sid):
        self.delete_session(sid)

    def duplicate(self, source_slug, new_slug, internal_name):
        if not isinstance(new_slug, str) or not new_slug.strip() or not new_slug.replace('-', '').isalnum():
            raise ValueError('Use a short link name with letters, numbers or hyphens')
        if not isinstance(internal_name, str) or not internal_name.strip():
            raise ValueError('Enter an internal name')
        if self.client.get_version(new_slug):
            raise ValueError('That version link already exists')
        source = self.get(source_slug)
        draft = deepcopy(source['draft'])
        draft['slug'], draft['internal_name'] = new_slug, internal_name.strip()[:80]
        row = {'slug': new_slug, 'internal_name': draft['internal_name'], 'headline': draft['headline'],
               'intro': draft['intro'], 'project_ids': draft['project_ids'], 'draft': draft,
               'published': draft, 'status': 'draft', 'revision': 1}
        return self._record(self.client.create_version(row))

    def save(self, slug, draft, revision):
        if not isinstance(draft, dict) or set(draft) != set(rendering.SEED):
            raise ValueError('Unexpected content fields')
        if draft['slug'] != slug or not isinstance(draft['internal_name'], str) or not 1 <= len(draft['internal_name'].strip()) <= 80:
            raise ValueError('Published link names cannot change; enter an internal name up to 80 characters')
        rendering.validate(draft)
        return self._patch(slug, revision, {'draft': draft, 'headline': draft['headline'], 'intro': draft['intro'], 'project_ids': draft['project_ids'], 'internal_name': draft['internal_name']})

    def archive(self, slug):
        if slug == 'fintech':
            raise ValueError('The protected baseline cannot be archived')
        current = self.get(slug)
        return self.set_status(slug, 'archived', current['revision'])

    def unpublish(self, slug):
        current = self.get(slug)
        return self.set_status(slug, 'offline', current['revision'])

    def restore(self, slug):
        current = self.get(slug)
        return self.set_status(slug, 'live', current['revision'])
