import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import server


class VersionsTest(unittest.TestCase):
    def test_seed_preserves_saved_data_on_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'content.sqlite3'
            with patch.object(server, 'DATABASE', database):
                server.initialize()
                updated = dict(server.SEED, headline='Saved headline')
                with sqlite3.connect(database) as db:
                    db.execute('UPDATE versions SET content=? WHERE slug=?', (json.dumps(updated), 'fintech'))
                server.initialize()
                self.assertEqual(server.load_version('fintech')['headline'], 'Saved headline')
                self.assertIsNone(server.load_version("' OR 1=1 --"))

    def test_project_selection_is_exact_and_ordered(self):
        projects = json.loads(server.selected_projects(server.SEED).decode().split(' = ', 1)[1].rstrip(';\n'))
        self.assertEqual([p['number'] for p in projects], ['01', '03', '05'])
        self.assertTrue(all(p['caseStudyUrl'].startswith('/project-') for p in projects))

    def test_invalid_selections_are_rejected(self):
        for ids in ([], ['01', '01'], ['99'], ['01', '02', '03', '05']):
            with self.assertRaises(ValueError):
                server.validate(dict(server.SEED, project_ids=ids))

    def test_content_escapes_markup_and_omits_private_name(self):
        content = dict(server.SEED, headline='<script>alert(1)</script>', internal_name='PRIVATE TARGET LABEL')
        html = server.render(content).decode()
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertNotIn('PRIVATE TARGET LABEL', html)
        self.assertIn('src="/for/fintech/projects.js"', html)


if __name__ == '__main__':
    unittest.main()
