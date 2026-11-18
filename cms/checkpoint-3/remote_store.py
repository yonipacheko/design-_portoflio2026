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
