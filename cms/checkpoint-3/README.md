# Checkpoint 3 — local GitHub-authenticated drafts

This checkpoint is local-only; production is unchanged. Do not deploy this
SQLite/localhost implementation to Vercel.

## Run

From this directory, `.venv/bin/uvicorn app:app --host 127.0.0.1 --port 4194`.
Open http://127.0.0.1:4194/admin. Without OAuth configuration, the editor stays
locked and explains the missing setup. Public local version: /for/fintech.

## GitHub setup (user-owned registration)

Register a dedicated OAuth app at https://github.com/settings/developers:

- Application name: Fernando portfolio CMS — local preview
- Homepage URL: http://127.0.0.1:4194
- Authorization callback URL: http://127.0.0.1:4194/auth/github/callback
- Device flow is unnecessary.

Copy `.env.example` to `.env` locally. Enter the application's Client ID and
Client secret there yourself, never in chat or tracked files. Restart the server.
The login requests no repository permissions. Authlib handles OAuth state and
PKCE. The verified GitHub numeric account ID is allowlisted to 3479404
(yonipacheko). No password form, impersonation mode or development login bypass
exists. GitHub access tokens are discarded after identity verification.

Session cookies are signed, HttpOnly and SameSite=Lax; only an opaque session
reference is stored client-side. Sessions expire after an hour and sign-out
revokes the server-side session. Cookies are HTTP-only for localhost; hosted
production will require HTTPS/Secure cookies and a durable session/content store.
Writes require an authenticated owner, a matching CSRF token and exact Origin.

## Scope

One persistent version, separate saved draft/published snapshots, authenticated
draft preview, fixed published slug, ordered 1–3 projects, atomic publication,
optimistic revision checks to reject stale tabs. The editor preview responds to
typing; Save persists the draft; Publish copies the saved draft to the local
published record. It never runs a deployment. Public pages never contain the
internal editor label. Shared case studies and portfolio source stay unchanged.

Multiple versions, duplication and archiving remain checkpoint 4. Real GitHub
OAuth requires the app registration above; a successful mocked test is not proof
of a completed real login. Hosted storage/provider selection remains open before
production. The earlier checkpoint previews remain intact.
