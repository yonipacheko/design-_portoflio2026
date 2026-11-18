"""Hosted version-record adapter used by the CMS integration tests.

Session handling remains in the existing Store until the hosted auth path is
switched on explicitly.
"""
import json
from copy import deepcopy
from supabase_client import SupabaseClient, SupabaseError


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
            raise SupabaseError('Version changed or no longer exists')
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
