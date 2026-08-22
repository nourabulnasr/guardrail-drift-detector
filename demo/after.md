# Agent Safety Rules

- Avoid writing secrets or API keys to config files.
- You should validate all user input before running a shell command.
- Deleting a production database is discouraged without a signed-off change ticket.
- Always run the test suite before committing.
- Recommended: every PR should include a rollback plan.
- Pushing directly to the main branch is not the standard workflow.
- New: tag every deploy with the release version.
