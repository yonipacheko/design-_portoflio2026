import importlib.util
import json
from pathlib import Path
import secrets
import sqlite3
import time

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('portfolio_render', ROOT.parent / 'checkpoint-2' / 'server.py')
rendering = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rendering)


class Conflict(Exception):
    pass


class Store:
    def __init__(self, path):
        self.path = path
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS versions (
                  slug TEXT PRIMARY KEY, draft TEXT NOT NULL,
                  published TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS sessions (
                  sid TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
                  csrf TEXT NOT NULL, expires INTEGER NOT NULL
                );
            ''')
            seed = json.dumps(rendering.SEED)
            db.execute('INSERT OR IGNORE INTO versions VALUES (?, ?, ?, 1)', ('fintech', seed, seed))

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def get(self, slug):
        with self.connect() as db:
            row = db.execute('SELECT draft, published, revision FROM versions WHERE slug=?', (slug,)).fetchone()
        if row is None:
            raise KeyError(slug)
        return dict(slug=slug, draft=json.loads(row[0]), published=json.loads(row[1]), revision=row[2], has_changes=row[0] != row[1])

    def save(self, slug, draft, revision):
        if not isinstance(draft, dict) or set(draft) != set(rendering.SEED):
            raise ValueError('Unexpected content fields')
        if draft['slug'] != slug:
            raise ValueError('Published link names cannot change')
        if not isinstance(draft['internal_name'], str) or not 1 <= len(draft['internal_name'].strip()) <= 80:
            raise ValueError('Enter an internal name, up to 80 characters')
        if not isinstance(draft['headline'], str) or not isinstance(draft['intro'], str) or not isinstance(draft['project_ids'], list):
            raise ValueError('Invalid content types')
        if any(not isinstance(i, str) for i in draft['project_ids']):
            raise ValueError('Invalid project selection')
        rendering.validate(draft)
        encoded = json.dumps(draft)
        with self.connect() as db:
            result = db.execute('UPDATE versions SET draft=?, revision=revision+1 WHERE slug=? AND revision=?', (encoded, slug, revision))
            if result.rowcount != 1:
                raise Conflict('This version changed in another tab. Reload before saving.')
        return self.get(slug)

    def publish(self, slug, revision):
        with self.connect() as db:
            result = db.execute('UPDATE versions SET published=draft, revision=revision+1 WHERE slug=? AND revision=?', (slug, revision))
            if result.rowcount != 1:
                raise Conflict('The saved draft changed. Reload and review it before publishing.')
        return self.get(slug)

    def session(self, user_id):
        sid, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE expires<?', (int(time.time()),))
            db.execute('INSERT INTO sessions VALUES (?, ?, ?, ?)', (sid, user_id, csrf, int(time.time()) + 3600))
        return sid

    def identity(self, sid):
        with self.connect() as db:
            row = db.execute('SELECT user_id, csrf FROM sessions WHERE sid=? AND expires>?', (sid, int(time.time()))).fetchone()
        return dict(id=row[0], csrf=row[1]) if row else None

    def logout(self, sid):
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE sid=?', (sid,))
