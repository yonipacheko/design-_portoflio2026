# Checkpoint 4 — portfolio versions

This branch is the starting point for the approved versions workflow. Production remains unchanged.

The implementation will add:

- a private gallery of saved versions with thumbnail, internal name and status;
- duplicate as a new draft with a new slug;
- editable landing-page headline, introduction and ordered selection of up to three shared projects;
- publish and archive actions with confirmation and clear live/draft status;
- public `/for/<slug>` links that share the existing case studies;
- per-version local preview and no deployment for content edits.

The existing `fintech` version remains the protected baseline while the new flow is developed. The first review will cover create, duplicate and preview only; publishing and archive behavior will follow as a separate review step.
