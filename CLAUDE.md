# Agent Safety Rules

- Never write secrets or API keys to config files.
- You must validate all user input before running a shell command.
- Deleting a production database is forbidden without a signed-off change ticket.
- Always run the test suite before committing.
- Required: every PR must include a rollback plan.
- Do not push directly to the main branch.
