# Preauthorized Services

The following services are pre-configured and ready to use:

## GitHub CLI (gh)
Git operations and GitHub API access via authenticated gh CLI
- Git credentials configured for seamless push/pull
- **Usage**: Use `gh` commands directly, git push/pull work automatically

## Claude Code OAuth
Claude Code CLI is pre-authenticated with your account
- CLAUDE_CODE_OAUTH_TOKEN environment variable set
- **Usage**: Run `claude` to start Claude Code (auto-starts on first login if enabled)

## Dev Environment MCP
Manage repository secrets, init scripts, and CLAUDE.md via MCP tools
- Available tools:
- `list_secrets` - List configured secrets
- `add_secret` - Add/update a secret
- `delete_secret` - Remove a secret
- `get_init_script` / `update_init_script` - Manage VM startup script
- `get_claude_md_additions` / `update_claude_md_additions` - Manage CLAUDE.md
- `set_gcloud_credentials` - Set GCP service account
- `get_repository_info` - View repository config
- **Usage**: Changes take effect on next VM start. Agent can apply immediately.

## Emergency Mayday Endpoint
Report critical failures when MCP tools or document review aren't working
- **IMPORTANT**: Use `http://10.128.0.2:5001/api/internal/mayday` (internal GCP network only)
- Required fields: `agent_type`, `error_type`, `error_message`
- Optional fields: `session_id`, `context`, `attempted_actions`
- Error types: `mcp_unreachable`, `document_review_failed`, `tool_unavailable`, `critical_error`
- **Usage**: curl -X POST http://10.128.0.2:5001/api/internal/mayday -H 'Content-Type: application/json' -d '{"agent_type": "claude-code", "error_type": "mcp_unreachable", "error_message": "Description of the issue"}'


# Knowledge Bank Usage

You have access to a Knowledge Bank via MCP tools. Use it frequently throughout your work.

## Query the Knowledge Bank (`query_knowledge_bank`)
**Use BEFORE taking action** - not just when you have problems:
- Before running shell commands
- Before editing or creating files
- Before making architectural decisions
- When starting a new subtask or phase
- When encountering errors or unexpected behavior

**Expected frequency**: Query the KB every 1-2 tool calls.

## Report Learnings (`report_learning`)
**Store discoveries for future agents**:
- Information found in files/docs that wasn't in KB
- Solutions discovered through trial-and-error
- Gotchas or unexpected behaviors
- How systems work
- Useful patterns or conventions

Frame as facts: "X works by..." not "I changed..."


# Dev Environment Context

## Important: You are working in an ISOLATED DEV ENVIRONMENT

- You are NOT on the production server
- You are NOT on the user's local machine
- You are in a dedicated VM with its own resources
- Your changes affect only this isolated environment until you create a PR

## Available Tools & Testing

### Local Testing
- Docker Compose is available - start containers with `docker compose up -d`
- The app runs at http://localhost:5001 (or configured port)
- You have the **Playwright MCP** available for browser automation testing
- For E2E testing, use Playwright to interact with your local deployment

### Type Checking
- **Pyright** must pass for all Python code changes
- Run: `docker compose exec api pipenv run pyright` (or equivalent)
- If Pyright is not installed, install it first
- Strong type checking is REQUIRED before committing

### Testing Protocols
1. **Unit Tests**: Write comprehensive unit tests for all new functionality
2. **E2E Tests**: When mechanically implementable, create E2E tests
3. **Manual E2E**: If E2E tests cannot be automated, use Playwright MCP to manually test your local deployment
4. **All tests must pass** before creating a PR

## Knowledge Bank Usage

- Query the KB frequently for project-specific information:
  - Architecture decisions
  - Testing procedures
  - User preferences
  - Common patterns and gotchas
- Report learnings to KB when you discover important information
- The KB is your persistent memory across sessions

## Communication Protocol

- **ALL user communication MUST go through the Document Review MCP tool**
- Do NOT attempt to communicate through plain text responses
- Create document reviews for:
  - Proposals and plans
  - Progress updates
  - Questions that need answers
  - Final results and summaries

## Handling Unrelated Errors

If you discover errors/issues that are NOT related to your current task:
1. Take note of the issue
2. Include it in your next document review to the user
3. Ask how they want to proceed
4. Do NOT attempt to fix unrelated issues without approval

## Diagram Generation

- Use Python's `diagrams` package for architecture diagrams
- Install if needed: `pip install diagrams`
- Save diagrams as PNG and include in document reviews

## Git Workflow

- Start with a fresh branch for your work
- Commit and push regularly
- Your branch is deployed at a unique URL the user can access
- When complete, create a PR to main
- Get user approval before merging
- Be careful with destructive git operations - ask first
