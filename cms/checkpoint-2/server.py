"""Checkpoint 2: a localhost-only proof of saved portfolio versions.

No admin/write HTTP endpoints. SQLite is a local development store, not a
production storage choice for Vercel's ephemeral functions.
"""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit, unquote
from html import escape
import argparse
import json
import re
import sqlite3

ROOT = Path(__file__).resolve().parent
PORTFOLIO = ROOT.parents[1] / 'dist'
DATABASE = ROOT / 'local-content.sqlite3'
PROJECTS = json.loads((ROOT / 'projects.json').read_text())
CATALOG = {p['number']: p for p in PROJECTS if p.get('caseStudyUrl')}
SEED = {
    'slug': 'fintech',
    'internal_name': 'Fintech opportunities',
    'headline': 'Making complex financial products feel simple.',
    'intro': 'I’m Fernando, a product designer connecting clarity, trust and useful interactions in financial services.',
    'project_ids': ['01', '03', '05'],
}


def validate(content):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', content['slug']):
        raise ValueError('Invalid version slug')
    if not 1 <= len(content['headline']) <= 150 or not 1 <= len(content['intro']) <= 500:
        raise ValueError('Headline or intro length is invalid')
    ids = content['project_ids']
    if not 1 <= len(ids) <= 3 or len(set(ids)) != len(ids) or any(i not in CATALOG for i in ids):
        raise ValueError('Choose one to three distinct available case studies')
    return content


def initialize():
    validate(SEED)
    with sqlite3.connect(DATABASE) as db:
        db.execute('CREATE TABLE IF NOT EXISTS versions (slug TEXT PRIMARY KEY, content TEXT NOT NULL)')
        db.execute('INSERT OR IGNORE INTO versions VALUES (?, ?)', (SEED['slug'], json.dumps(SEED)))


def load_version(slug):
    with sqlite3.connect(DATABASE) as db:
        row = db.execute('SELECT content FROM versions WHERE slug = ?', (slug,)).fetchone()
    return validate(json.loads(row[0])) if row else None


def render(content):
    """Use the original template without modifying the source portfolio."""
    html = (PORTFOLIO / 'index.html').read_text()
    html = html.replace('<body>', '<body class="tailored-page">', 1)
    html = re.sub(r'<title>.*?</title>', '<title>' + escape(content['headline']) + ' — Fernando</title>', html, count=1)
    html = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="' + escape(content['intro'], quote=True) + '" />', html, count=1)
    html = re.sub(r'<h1 id="hero-title">.*?</h1>', '<h1 id="hero-title">' + escape(content['headline']) + '</h1>', html, count=1)
    html = re.sub(r'<div class="hero-copy">.*?</div>', '<div class="hero-copy"><p>' + escape(content['intro']) + '</p></div>', html, count=1, flags=re.S)
    html = html.replace('Design work across financial apps, trading flows, product systems, and critical moments of clarity.', 'A selection of my work in financial products, systems, and service experiences.')
    html = html.replace('href="./', 'href="/').replace('src="./', 'src="/')
    html = html.replace('src="/content.js"', 'src="/for/' + content['slug'] + '/projects.js"', 1)
    html = html.replace('</head>', '<meta name="robots" content="noindex" /><style>.tailored-page .hero h1{font-size:clamp(2.8rem,7vw,7rem);line-height:1.05;letter-spacing:-.055em;max-width:1100px;overflow-wrap:break-word}.checkpoint-note{position:fixed;bottom:8px;right:8px;z-index:100;margin:0;padding:7px 12px;border-radius:6px;background:#e9eee2;color:#344d3c;font:11px/1.6 Arial,sans-serif;text-align:center;max-width:calc(100vw - 16px);pointer-events:none}</style></head>', 1)
    html = html.replace('<main id="main">', '<main id="main"><p class="checkpoint-note">Checkpoint 2 · Saved local version · Not published</p>', 1)
    return html.encode()


def selected_projects(content):
    projects = []
    for key in content['project_ids']:
        p = dict(CATALOG[key])
        for field in ('image', 'caseStudyUrl'):
            p[field] = '/' + p[field].removeprefix('./')
        projects.append(p)
    return ('window.portfolioProjects = ' + json.dumps(projects, ensure_ascii=True) + ';\n').encode()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PORTFOLIO), **kwargs)

    def respond(self, body, content_type, status=200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def route(self):
        path = unquote(urlsplit(self.path).path)
        match = re.fullmatch(r'/for/([a-z0-9]+(?:-[a-z0-9]+)*)(/projects\.js)?/?', path)
        if path.startswith('/for/'):
            content = load_version(match[1]) if match else None
            if not content:
                self.respond(b'<!doctype html><title>Version unavailable</title><h1>This portfolio version is unavailable.</h1><a href="/">View Fernando\xe2\x80\x99s portfolio</a>', 'text/html; charset=utf-8', 404)
            elif match[2]:
                self.respond(selected_projects(content), 'text/javascript; charset=utf-8')
            else:
                self.respond(render(content), 'text/html; charset=utf-8')
            return True
        return False

    def do_GET(self):
        if not self.route():
            super().do_GET()

    def do_HEAD(self):
        if not self.route():
            super().do_HEAD()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=4193)
    args = parser.parse_args()
    initialize()
    print(f'Local preview: http://127.0.0.1:{args.port}/for/fintech', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
