# Auto Git Push Rule

## Rule

After completing any file modification or code change, you MUST automatically perform the following git workflow:

1. **Check status**: Run `git status` to identify changed files
2. **Stage changes**: Run `git add` for all relevant modified/new files
3. **Commit changes**: Run `git commit -m` with a descriptive commit message following conventional commits format (e.g., `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`)
4. **Push to remote**: Run `git push origin <current-branch>` to push the commit

## Trigger

This rule activates AUTOMATICALLY whenever:
- A file is created, modified, or deleted by the agent
- Any code change or configuration update is completed
- The user explicitly requests a file modification

## Exceptions

- Do NOT push if the user explicitly asks NOT to push
- Do NOT push if there are no actual changes to commit
- Do NOT push if the working directory is clean
- Do NOT commit files that may contain secrets or credentials (.env, credentials.json, etc.)

## Commit Message Format

Use conventional commit prefixes:
- `feat:` - New feature or enhancement
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks
- `style:` - Formatting changes

Keep commit messages concise, in the same language as the changes being committed.
