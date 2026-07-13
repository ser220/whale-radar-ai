# Whale Radar AI engineering instructions

These instructions apply to the entire repository.

1. Inspect the actual repository before every task; archived conversations are context, not proof of repository state.
2. Respect the repository's real Python version and installed dependencies.
3. Preserve backward compatibility.
4. Do not replace or redesign working production paths unless explicitly authorized.
5. Add new architecture alongside working code by default.
6. Run compilation and required tests before committing.
7. Never commit when a required check fails.
8. Never merge directly into `main`.
9. Never force-push.
10. Never delete, reset, stash, overwrite, or commit unrelated user files without explicit approval.
11. Never commit secrets, tokens, `.env` files, credentials, database dumps, caches, logs, or virtual environments.
12. Every WR task must create or update `docs/reports/WR-XXXX_REPORT.md`.
13. Architecture tasks must use a dedicated feature branch and await Architecture Review before merge.
14. Do not begin the next WR task automatically.
15. Ask for permission before destructive, privileged, remote, or ambiguous operations when the environment requires approval.
