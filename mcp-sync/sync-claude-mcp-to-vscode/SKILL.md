---
name: sync-claude-mcp-to-vscode
description: Syncs MCP servers from Claude Code's installed plugins into VS Code's settings so they can be used in Copilot chat. Use this skill whenever the user wants to import, sync, or add Claude Code MCP servers to VS Code, asks why Copilot can't access an MCP server they have in Claude, or wants to reuse Claude plugin MCP servers in VS Code chat. Also use when the user asks to "add MCP servers to VS Code", "sync MCP from Claude", or "make Claude's MCP servers available in Copilot".
---

# Sync Claude Code MCP Servers → VS Code

Reads every enabled Claude Code plugin's `.mcp.json` file from the plugin cache and merges those server definitions into VS Code's user `settings.json` under the `"mcp"."servers"` key.

## Background

Claude Code stores MCP server configs in:
```
~/.claude/plugins/cache/claude-plugins-official/<plugin>/<version>/.mcp.json
```

VS Code (1.99+) uses a **dedicated `mcp.json`** file (not `settings.json`) for MCP server configuration. The file lives alongside `settings.json` in the active profile:
```
~/Library/Application Support/Code/User/profiles/<profile-id>/mcp.json
# or for the default profile:
~/Library/Application Support/Code/User/mcp.json
```

Format:
```json
{
  "servers": { "<name>": { ...config } },
  "inputs": []
}
```

## When to Run

- User is setting up VS Code Copilot for the first time and has Claude Code plugins installed
- User installed a new Claude Code plugin and wants it in VS Code too
- User asks why a tool (e.g. `context7`, `playwright`, `github`) isn't available in Copilot chat

## Procedure

### Step 1 — Find enabled plugins and their MCP configs

```bash
# List all enabled plugins from Claude settings
cat ~/.claude/settings.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
for k in d.get('enabledPlugins', {}):
    print(k.split('@')[0])
"
```

Then for each plugin, find its active `.mcp.json`:

```bash
python3 scripts/sync_mcp.py
```

The script handles version resolution (semver > hash, skips orphaned), normalises both Claude plugin `.mcp.json` schemas, and writes directly to VS Code's `mcp.json`.

### Step 2 — Merge into VS Code mcp.json

### Step 3 — Handle tokens / env vars

Servers that require API tokens (e.g. `github`, `greptile`) use `${ENV_VAR}` placeholders in VS Code. Remind the user to set the variable in their shell profile or replace the placeholder in settings.json:

| Plugin | Env var needed |
|--------|---------------|
| `github` | `GITHUB_PERSONAL_ACCESS_TOKEN` |
| `greptile` | `GREPTILE_API_KEY` |
| `figma` | None (browser auth) |
| `huggingface-skills` | None (browser auth) |
| `context7` | None |
| `playwright` | None |
| `serena` | None |

### Step 4 — Reload VS Code

Tell the user to **start a new chat session** in VS Code — MCP server discovery happens at session start. They can verify via Command Palette → `MCP: List Servers`.

## Running the Script

```bash
cd <project-root>
python3 .agents/skills/mcp-sync/sync-claude-mcp-to-vscode/scripts/sync_mcp.py
# With overwrite:
python3 .agents/skills/mcp-sync/sync-claude-mcp-to-vscode/scripts/sync_mcp.py --overwrite
```

Or as a one-liner to run from anywhere:
```bash
python3 ~/.agents/skills/mcp-sync/sync-claude-mcp-to-vscode/scripts/sync_mcp.py
```

## What Gets Skipped

- Plugins without a `.mcp.json` (skills/commands/agents/hooks-only plugins)
- Orphaned plugin versions (have `.orphaned_at` marker file)
- Servers already present in VS Code settings (unless `--overwrite`)

## Format Notes

Claude plugin `.mcp.json` uses two slightly different schemas:

**Schema A** (most plugins — top-level keys are server names):
```json
{ "github": { "type": "http", "url": "...", "headers": { ... } } }
```

**Schema B** (figma, huggingface — wrapped in `mcpServers`):
```json
{ "mcpServers": { "figma": { "type": "http", "url": "..." } } }
```

The collect script normalises both to Schema A before merging into VS Code settings.
