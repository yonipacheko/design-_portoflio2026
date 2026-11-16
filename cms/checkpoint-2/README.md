# Checkpoint 2 — one saved local version

Run `python3 server.py --port 4193` in this directory, then open
http://127.0.0.1:4193/for/fintech.

The sample is seeded once into a private SQLite database beside the server.
Restarting the server preserves it; initialization never overwrites saved content.
The database and private internal name are never served. Only the selected project
records are sent to the tailored page. The original homepage, case studies,
styles, scripts and assets are served unchanged from the existing local portfolio.
No edits are made to that portfolio. Unknown versions return a neutral 404.

This is local-only architecture validation. SQLite here is NOT suitable for
Vercel functions' ephemeral filesystem. Before deployment, choose durable hosted
storage and implement a compatible adapter. No authentication, write API,
editor connection, publication workflow, archive operation, or version traffic
dashboard is implemented. Existing analytics skips localhost; no test traffic
is sent. No production deployment is authorized by this checkpoint.

The next checkpoint adds authenticated editing and draft/published separation,
after design and behavior approval. The CMS gallery remains in the sibling
checkpoint-1 folder.
