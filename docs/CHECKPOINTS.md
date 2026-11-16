# Portfolio and CMS checkpoint workflow

## Baseline

The deployed portfolio was reconciled on 2026-11-16 against Vercel deployment
the then-current production release. All 96 editable source/assets in `dist/`
matched the uploaded SHA-1 identifiers. This includes analytics, project order,
HAKI approach content and the optional prototype CTA. No deployment was made
as part of this repository organization.

The existing `main` contains the initial README rather than the deployed site.
Do not merge or enable automatic production deployments until that difference
has been reviewed. Existing branches/history are preserved.

## Review sequence

1. `portfolio-baseline-2026-11-16`: reconcile already deployed source.
2. `cms/checkpoint-1-design`: gallery/editor sample preview, based on baseline.
3. `cms/checkpoint-2-content`: one persisted local version, based on checkpoint 1.
4. `cms/checkpoint-3-auth-drafts`: private editor and draft/publish logic, based
   on checkpoint 2. **Incomplete: real GitHub OAuth is not configured/tested.**

Each checkpoint gets its own branch and draft pull request targeting its
predecessor. Do not merge checkpoint 3 or call it approved just because its
automated tests pass. User approval is required before the next checkpoint and
before production release. No new CMS features during organization.

## Safe development

- Use the checkpoint's isolated checkout; keep the earlier previews intact.
- Commit a focused change, record relevant checks and limitations, and update
  the matching pull request. Do not reset, force-push or delete earlier work.
- Keep `.env`, session signing keys, databases, virtual environments, caches,
  logs and credentials out of Git. `.env.example` contains blank placeholders.
- The local databases and existing private files remain at their original
  preview locations. Version-controlled copies contain source only.
- Tags name saved review points, not evidence of approval. Checkpoint 3 is a
  work-in-progress snapshot, not a release.

## Rollback

Before a code rollback, preserve local changes and check out a saved checkpoint
in an isolated worktree. Revert specific commits for shared branches rather
than rewriting history. A code rollback alone does not restore content data.

Before changing database schema or stored data, take a consistent SQLite backup
using the SQLite backup API and record the schema version. Keep the private
backup outside Git. Test restoration against a temporary copy before replacing
any active data. Hosted storage and production migrations are not yet selected.
Restore data only with an explicit, reviewed recovery plan.

## Hosting

The CMS is localhost-only and its SQLite files are development storage. It
must not be deployed to Vercel functions unchanged. Public links and publishing
are future production capabilities after hosted storage/auth integration and
release approval. The original static portfolio remains the production site.
