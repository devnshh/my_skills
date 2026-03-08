# Skill: Import Claude Code Plugin Skills and Plugins to Local Format

## Description

Automatically imports all skills **and plugins** from the Claude Code plugins cache (`~/.claude/plugins/cache/`) into the local project, supporting both **Antigravity/Codex** (`.agents/skills/`) and **VS Code Copilot** (`.github/instructions/`) formats. Skills are grouped under their parent plugin folder, preserving the original directory hierarchy.

**What's new:** Plugins that don't have a `skills/` directory but contain useful content — such as **commands** (workflow instructions), **agents** (specialized sub-agent prompts), and **hooks** (automated triggers with handler scripts) — are now also imported. These are converted into a skill-compatible format so they can be discovered and used by any agentic LLM, not just the original provider.

## When to Use

- When setting up a new project and you want local access to all cached Claude Code skills and plugins
- When you want to sync the latest plugin skills into the current workspace
- After installing or updating Claude Code plugins and want local copies
- When the user asks to "import skills", "sync skills", "import plugins", or "convert plugin skills to local format"
- When you want plugin commands, agents, and hooks available as reusable skills for any AI coding agent

## Procedure

### Step 1: Identify the Cache Directory

The Claude Code plugins cache lives at:

```
~/.claude/plugins/cache/claude-plugins-official/
```

Each subdirectory is a plugin (e.g., `superpowers`, `figma`, `claude-md-management`). Inside each plugin directory there are one or more version directories (either semver like `4.3.1` or hash-based like `205b6e0b3036`).

### Step 2: Determine the Latest Active Version of Each Plugin

For each plugin directory, identify the **latest non-orphaned** version:

1. List all version subdirectories inside the plugin folder.
2. **Exclude** any version that contains an `.orphaned_at` file — these are stale/replaced versions.
3. From the remaining (non-orphaned) versions, pick the one to use:
  - If any version names are valid semver (for example `1.2.0`), choose the highest semver.
  - If none are semver (for example hash-like directory names), choose the most recently modified directory.
4. If **no** non-orphaned version has importable content (no `skills/`, `commands/`, `agents/`, or `hooks/` directory), skip this plugin entirely.

Important implementation detail: do not just take the last directory returned by shell globbing; directory order is not guaranteed to match semver recency.

### Step 3: Discover Importable Content Within Each Plugin Version

Inside the selected version directory, look for these content types in priority order:

#### 3a. Skills (highest priority — import as-is)

```
~/.claude/plugins/cache/claude-plugins-official/<plugin>/<version>/skills/
```

Each child directory under `skills/` represents one skill. A valid skill directory:
- Contains a `SKILL.md` file
- May contain additional reference files and subdirectories (e.g., `references/`, example files, scripts)

#### 3b. Commands (plugin workflow instructions)

```
~/.claude/plugins/cache/claude-plugins-official/<plugin>/<version>/commands/
```

Each `.md` file in `commands/` contains a structured workflow or command prompt. These often have YAML frontmatter with `description`, `allowed-tools`, and `argument-hint` fields.

#### 3c. Agents (specialized sub-agent prompts)

```
~/.claude/plugins/cache/claude-plugins-official/<plugin>/<version>/agents/
```

Each `.md` file in `agents/` defines a specialized agent with a particular role (code reviewer, code explorer, architect, etc.). These have YAML frontmatter with `name`, `description`, `tools`, and `model` fields.

#### 3d. Hooks (automated trigger handlers)

```
~/.claude/plugins/cache/claude-plugins-official/<plugin>/<version>/hooks/
```

Contains a `hooks.json` configuration and handler scripts (`.py`, `.sh`, etc.) in `hooks/` or `hooks-handlers/`. These define automated behaviors triggered by specific events.

#### 3e. Plugin Metadata

```
~/.claude/plugins/cache/claude-plugins-official/<plugin>/<version>/.claude-plugin/plugin.json
```

Contains the plugin's `name`, `description`, and `author`. Used to generate SKILL.md for plugins that only have commands/agents/hooks.

### Step 4: Copy Skills Preserving Plugin Folder Structure

For each discovered **skill directory**, copy it **in its entirety** (preserving internal structure) into a subdirectory named after the plugin:

```
<project-root>/.agents/skills/<plugin-name>/<skill-name>/
```

**Rules:**
- **Do NOT modify** any file content — copy everything as-is.
- Preserve the full directory tree under each skill (subdirectories, reference files, scripts, etc.).
- If a skill already exists at the target path, **skip it** unless the user explicitly requests overwriting. Report which skills were skipped.
- Create the `.agents/skills/<plugin-name>/` directory if it does not exist.

### Step 5: Convert and Import Plugin Commands, Agents, and Hooks

For plugins that have **commands**, **agents**, or **hooks** but no `skills/` directory (or as additional content alongside skills), convert them into skill-compatible format:

#### 5a. Converting Commands to Skills

For each `.md` file in `commands/`:

1. Create a skill directory: `.agents/skills/<plugin-name>/<command-name>/`
2. Copy the original `.md` file as `SKILL.md`.
3. If the command references agent files (e.g., `code-explorer`, `code-architect`), copy those agent `.md` files into a `references/` subdirectory within the skill.
4. Preserve the original YAML frontmatter intact.

#### 5b. Converting Agents to Skills

For each `.md` file in `agents/` (when not already pulled in as a command reference):

1. Create a skill directory: `.agents/skills/<plugin-name>/<agent-name>/`
2. Copy the original `.md` file as `SKILL.md`.
3. Preserve the original YAML frontmatter intact.

#### 5c. Converting Hooks to Skills

For plugins that only have hooks:

1. Create a skill directory: `.agents/skills/<plugin-name>/<plugin-name>-hooks/`
2. Generate a `SKILL.md` with:
   - The plugin's `name` and `description` from `plugin.json`
   - A description of what the hooks do (from `hooks.json`)
   - Instructions on how to use or adapt them
3. Copy all hook handler scripts and `hooks.json` into a `scripts/` subdirectory.

#### 5d. Handling Plugins with Mixed Content

Some plugins have both `skills/` and `commands/`/`agents/`. In this case:
- Import skills normally (Step 4).
- Import commands and agents that are **not already covered** by an existing skill.
- Use the plugin's README.md (if present) to provide additional context.

### Step 6: Copy Skills for VS Code Copilot Compatibility

In addition to the `.agents/skills/` structure, also copy each skill's `SKILL.md` into the VS Code Copilot custom instructions directory:

```
<project-root>/.github/instructions/<plugin-name>--<skill-name>.md
```

VS Code Copilot reads `.md` files from `.github/instructions/` and can auto-attach them as context. Only the `SKILL.md` content is copied (as a flat `.md` file); reference files remain in `.agents/skills/` only.

**Rules:**
- Create `.github/instructions/` if it does not exist.
- Name each file `<plugin-name>--<skill-name>.md` to keep them unique and identifiable.
- If the file already exists, skip it (unless overwrite mode is enabled).
- Do NOT modify the content of the SKILL.md — copy as-is.
- This applies to both imported skills AND converted commands/agents/hooks.

### Step 7: Report Results

After import, provide a summary:

```
Imported Skills & Plugins Summary
===================================
Source: ~/.claude/plugins/cache/claude-plugins-official/
Targets: .agents/skills/ (Antigravity/Codex) + .github/instructions/ (VS Code Copilot)

Plugin: superpowers (v4.3.1) -> .agents/skills/superpowers/
  ✓ brainstorming                           [skill]
  ✓ systematic-debugging                    [skill]
  ✓ writing-skills                          [skill]
  ...

Plugin: feature-dev (v205b6e0b3036) -> .agents/skills/feature-dev/
  ✓ feature-dev                             [command → skill]
  ✓ code-explorer                           [agent → skill]
  ✓ code-architect                          [agent → skill]
  ✓ code-reviewer                           [agent → skill]

Plugin: code-review (v205b6e0b3036) -> .agents/skills/code-review/
  ✓ code-review                             [command → skill]

Plugin: code-simplifier (v1.0.0) -> .agents/skills/code-simplifier/
  ✓ code-simplifier                         [agent → skill]

Plugin: security-guidance (v205b6e0b3036) -> .agents/skills/security-guidance/
  ✓ security-guidance-hooks                 [hooks → skill]

Plugin: explanatory-output-style (v205b6e0b3036) -> .agents/skills/explanatory-output-style/
  ✓ explanatory-output-style-hooks          [hooks → skill]

VS Code instructions: N files written to .github/instructions/

Skipped (already exists): <list any skipped>
Skipped (no importable content): <list any skipped>

Total: X skills imported, Y plugins converted
```

## Implementation

Run this shell script from the project root to perform the import:

```bash
#!/bin/bash
set -euo pipefail

CACHE_DIR="$HOME/.claude/plugins/cache/claude-plugins-official"
AGENTS_DIR=".agents/skills"
VSCODE_DIR=".github/instructions"
PROJECT_ROOT="$(pwd)"

cleaned_zsh=0

cleanup_leftover_zsh() {
  local leftover="$PROJECT_ROOT/.zsh"
  if [[ -f "$leftover" ]] || [[ -L "$leftover" ]]; then
    rm -f "$leftover"
    cleaned_zsh=1
  fi
}

cleanup_leftover_zsh
trap cleanup_leftover_zsh EXIT

if [[ ! -d "$CACHE_DIR" ]]; then
  echo "ERROR: Cache directory not found: $CACHE_DIR"
  exit 1
fi

mkdir -p "$AGENTS_DIR"
mkdir -p "$VSCODE_DIR"

imported_skills=0
converted_plugins=0
vscode_count=0
skipped_exists=()
skipped_no_content=()

is_semver() {
  [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

# ─── Helper: Write a SKILL.md to VS Code instructions ───
write_vscode_instruction() {
  local plugin="$1"
  local skill="$2"
  local skill_md="$3"
  local vscode_file="$VSCODE_DIR/${plugin}--${skill}.md"
  if [[ ! -f "$vscode_file" ]] || [[ "${OVERWRITE:-0}" == "1" ]]; then
    cp "$skill_md" "$vscode_file"
    ((vscode_count++))
  fi
}

# ─── Helper: Import a skill directory (copy as-is) ───
import_skill_dir() {
  local plugin="$1"
  local skill="$2"
  local skill_dir="$3"
  local target="$AGENTS_DIR/$plugin/$skill"
  local label="${4:-skill}"

  if [[ -d "$target" ]]; then
    if [[ "${OVERWRITE:-0}" == "1" ]]; then
      rm -rf "$target"
      echo "  ↻ $skill (overwritten)  [$label]"
    else
      skipped_exists+=("$plugin/$skill")
      echo "  ⏭ $skill (already exists, skipped)  [$label]"
      # Still ensure VS Code instruction exists
      if [[ -f "$skill_dir/SKILL.md" ]]; then
        write_vscode_instruction "$plugin" "$skill" "$skill_dir/SKILL.md"
      fi
      return
    fi
  fi

  cp -R "$skill_dir" "$target"
  echo "  ✓ $skill  [$label]"
  ((imported_skills++))

  if [[ -f "$target/SKILL.md" ]]; then
    write_vscode_instruction "$plugin" "$skill" "$target/SKILL.md"
  fi
}

# ─── Helper: Convert a command/agent .md to skill ───
convert_md_to_skill() {
  local plugin="$1"
  local name="$2"
  local source_md="$3"
  local label="$4"
  local target="$AGENTS_DIR/$plugin/$name"

  if [[ -d "$target" ]]; then
    if [[ "${OVERWRITE:-0}" == "1" ]]; then
      rm -rf "$target"
      echo "  ↻ $name (overwritten)  [$label → skill]"
    else
      skipped_exists+=("$plugin/$name")
      echo "  ⏭ $name (already exists, skipped)  [$label → skill]"
      if [[ -f "$target/SKILL.md" ]]; then
        write_vscode_instruction "$plugin" "$name" "$target/SKILL.md"
      fi
      return
    fi
  fi

  mkdir -p "$target"
  cp "$source_md" "$target/SKILL.md"
  echo "  ✓ $name  [$label → skill]"
  ((converted_plugins++))

  write_vscode_instruction "$plugin" "$name" "$target/SKILL.md"
}

# ─── Helper: Convert hooks to skill ───
convert_hooks_to_skill() {
  local plugin="$1"
  local version_dir="$2"
  local skill_name="${plugin}-hooks"
  local target="$AGENTS_DIR/$plugin/$skill_name"

  if [[ -d "$target" ]]; then
    if [[ "${OVERWRITE:-0}" == "1" ]]; then
      rm -rf "$target"
      echo "  ↻ $skill_name (overwritten)  [hooks → skill]"
    else
      skipped_exists+=("$plugin/$skill_name")
      echo "  ⏭ $skill_name (already exists, skipped)  [hooks → skill]"
      return
    fi
  fi

  mkdir -p "$target/scripts"

  # Read plugin description from plugin.json if available
  local plugin_desc=""
  local plugin_json="$version_dir/.claude-plugin/plugin.json"
  if [[ -f "$plugin_json" ]]; then
    plugin_desc=$(python3 -c "import json; d=json.load(open('$plugin_json')); print(d.get('description',''))" 2>/dev/null || echo "")
  fi

  # Read hooks description from hooks.json
  local hooks_desc=""
  local hooks_json="$version_dir/hooks/hooks.json"
  if [[ -f "$hooks_json" ]]; then
    hooks_desc=$(python3 -c "import json; d=json.load(open('$hooks_json')); print(d.get('description',''))" 2>/dev/null || echo "")
  fi

  # Copy all hook files
  if [[ -d "$version_dir/hooks" ]]; then
    cp -R "$version_dir/hooks/"* "$target/scripts/" 2>/dev/null || true
  fi
  if [[ -d "$version_dir/hooks-handlers" ]]; then
    cp -R "$version_dir/hooks-handlers/"* "$target/scripts/" 2>/dev/null || true
  fi

  # Generate SKILL.md
  cat > "$target/SKILL.md" << HOOKSKILLEOF
---
name: $skill_name
description: ${plugin_desc:-"Hooks and automated triggers from the $plugin plugin."}${hooks_desc:+" $hooks_desc"}
---

# $skill_name

${plugin_desc:-"Automated hooks and triggers from the $plugin plugin."}

## What This Contains

${hooks_desc:-"This skill contains hook handlers and trigger configurations."}

The hook scripts and configuration are available in the \`scripts/\` subdirectory for reference, adaptation, or direct use.

## Files

$(ls "$target/scripts/" 2>/dev/null | while read f; do echo "- \`scripts/$f\`"; done)

## Usage

Review the hook scripts in \`scripts/\` for patterns and logic you can adapt to your project or other AI coding agents.
HOOKSKILLEOF

  echo "  ✓ $skill_name  [hooks → skill]"
  ((converted_plugins++))

  write_vscode_instruction "$plugin" "$skill_name" "$target/SKILL.md"
}


# ═══════════════════════════════════════════════
# Main loop: iterate over each plugin
# ═══════════════════════════════════════════════

for plugin_dir in "$CACHE_DIR"/*/; do
  [[ -d "$plugin_dir" ]] || continue
  plugin=$(basename "$plugin_dir")

  # Build candidate list of non-orphaned versions
  semver_candidates=()
  hash_candidates=()

  for version_dir in "$plugin_dir"*/; do
    [[ -d "$version_dir" ]] || continue
    version=$(basename "${version_dir%/}")
    [[ "$version" == ".DS_Store" ]] && continue
    [[ -f "$version_dir/.orphaned_at" ]] && continue

    # Check if this version has any importable content
    has_content=0
    for subdir in skills commands agents hooks; do
      if [[ -d "$version_dir/$subdir" ]]; then
        has_content=1
        break
      fi
    done
    [[ "$has_content" == "0" ]] && continue

    if is_semver "$version"; then
      semver_candidates+=("$version")
    else
      hash_candidates+=("$version_dir")
    fi
  done

  best_version=""
  best_version_dir=""

  if [[ ${#semver_candidates[@]} -gt 0 ]]; then
    best_version=$(printf '%s\n' "${semver_candidates[@]}" | sort -V | tail -n 1)
    best_version_dir="$plugin_dir$best_version/"
  elif [[ ${#hash_candidates[@]} -gt 0 ]]; then
    best_version_dir=$(ls -td "${hash_candidates[@]}" | head -n 1)
    best_version=$(basename "${best_version_dir%/}")
  fi

  if [[ -z "$best_version_dir" ]]; then
    skipped_no_content+=("$plugin")
    continue
  fi

  echo ""
  echo "Plugin: $plugin (v$best_version) -> $AGENTS_DIR/$plugin/"
  mkdir -p "$AGENTS_DIR/$plugin"

  # Track which agent names are already pulled in by commands (to avoid duplicates)
  imported_agents=()

  # ── 4a. Import native skills ──
  if [[ -d "$best_version_dir/skills" ]]; then
    for skill_dir in "$best_version_dir"/skills/*/; do
      [[ -d "$skill_dir" ]] || continue
      skill=$(basename "$skill_dir")
      [[ ! -f "$skill_dir/SKILL.md" ]] && continue
      import_skill_dir "$plugin" "$skill" "$skill_dir" "skill"
    done
  fi

  # ── 5a. Convert commands to skills ──
  if [[ -d "$best_version_dir/commands" ]]; then
    for cmd_file in "$best_version_dir"/commands/*.md; do
      [[ -f "$cmd_file" ]] || continue
      cmd_name=$(basename "$cmd_file" .md)
      convert_md_to_skill "$plugin" "$cmd_name" "$cmd_file" "command"

      # If there's a matching agents/ directory, copy agent files as references
      if [[ -d "$best_version_dir/agents" ]]; then
        local_target="$AGENTS_DIR/$plugin/$cmd_name"
        if [[ -d "$local_target" ]]; then
          mkdir -p "$local_target/references"
          for agent_file in "$best_version_dir"/agents/*.md; do
            [[ -f "$agent_file" ]] || continue
            agent_name=$(basename "$agent_file" .md)
            cp "$agent_file" "$local_target/references/$agent_name.md"
            imported_agents+=("$agent_name")
          done
        fi
      fi
    done
  fi

  # ── 5b. Convert standalone agents to skills (not already imported as references) ──
  if [[ -d "$best_version_dir/agents" ]]; then
    for agent_file in "$best_version_dir"/agents/*.md; do
      [[ -f "$agent_file" ]] || continue
      agent_name=$(basename "$agent_file" .md)

      # Skip if already pulled in as a command reference
      already_imported=0
      for imported in "${imported_agents[@]+"${imported_agents[@]}"}"; do
        if [[ "$imported" == "$agent_name" ]]; then
          already_imported=1
          break
        fi
      done
      [[ "$already_imported" == "1" ]] && continue

      convert_md_to_skill "$plugin" "$agent_name" "$agent_file" "agent"
    done
  fi

  # ── 5c. Convert hooks to skills (only if no skills/commands/agents were already imported) ──
  if [[ -d "$best_version_dir/hooks" ]]; then
    # Only create a hooks skill if we didn't import anything else from this plugin
    if [[ ! -d "$best_version_dir/skills" ]] && [[ ! -d "$best_version_dir/commands" ]] && [[ ! -d "$best_version_dir/agents" ]]; then
      convert_hooks_to_skill "$plugin" "$best_version_dir"
    fi
  fi

done

echo ""
echo "======================================"
echo "Import Complete"
echo "======================================"
echo "Total skills imported: $imported_skills"
echo "Total plugins converted: $converted_plugins"
echo "VS Code instructions: $vscode_count files written to $VSCODE_DIR/"

if [[ ${#skipped_exists[@]} -gt 0 ]]; then
  echo ""
  echo "Skipped (already exist): ${skipped_exists[*]}"
fi

if [[ ${#skipped_no_content[@]} -gt 0 ]]; then
  echo ""
  echo "Skipped (no importable content): ${skipped_no_content[*]}"
fi

if [[ "$cleaned_zsh" == "1" ]]; then
  echo ""
  echo "Cleanup: removed leftover .zsh file from project root"
fi
```

Recommended execution pattern:

```bash
cat > /tmp/import-skills.sh << 'EOF'
#!/bin/bash
# paste script here
EOF
chmod +x /tmp/import-skills.sh
bash /tmp/import-skills.sh
```

## Overwrite Mode

Overwrite mode is built into the main script. To enable it, set `OVERWRITE=1`:

```bash
OVERWRITE=1 bash /tmp/import-skills.sh
```

When enabled:
- Existing skill directories in `.agents/skills/<plugin>/<skill>/` are removed and replaced.
- Existing VS Code instruction files in `.github/instructions/` are overwritten.
- Converted plugin content (commands, agents, hooks) is also re-generated.
- Overwritten items are reported with `↻` in the output.

## Output Structure

After running the import, the project will contain:

```
<project-root>/
├── .agents/skills/                               # Antigravity/Codex format
│   ├── superpowers/                              # Plugin with native skills
│   │   ├── brainstorming/
│   │   │   └── SKILL.md
│   │   ├── systematic-debugging/
│   │   │   ├── SKILL.md
│   │   │   ├── defense-in-depth.md
│   │   │   └── find-polluter.sh
│   │   └── writing-skills/
│   │       ├── SKILL.md
│   │       └── examples/
│   ├── feature-dev/                              # Plugin with commands + agents
│   │   ├── feature-dev/                          # Command → skill
│   │   │   ├── SKILL.md
│   │   │   └── references/
│   │   │       ├── code-explorer.md
│   │   │       ├── code-architect.md
│   │   │       └── code-reviewer.md
│   │   ├── code-explorer/                        # Agent → standalone skill
│   │   │   └── SKILL.md
│   │   ├── code-architect/
│   │   │   └── SKILL.md
│   │   └── code-reviewer/
│   │       └── SKILL.md
│   ├── code-review/                              # Plugin with command only
│   │   └── code-review/
│   │       └── SKILL.md
│   ├── code-simplifier/                          # Plugin with agent only
│   │   └── code-simplifier/
│   │       └── SKILL.md
│   ├── security-guidance/                        # Plugin with hooks only
│   │   └── security-guidance-hooks/
│   │       ├── SKILL.md
│   │       └── scripts/
│   │           ├── hooks.json
│   │           └── security_reminder_hook.py
│   └── explanatory-output-style/                 # Plugin with hooks only
│       └── explanatory-output-style-hooks/
│           ├── SKILL.md
│           └── scripts/
│               ├── hooks.json
│               └── session-start.sh
├── .github/instructions/                         # VS Code Copilot format (flat)
│   ├── superpowers--brainstorming.md
│   ├── feature-dev--feature-dev.md
│   ├── feature-dev--code-explorer.md
│   ├── code-review--code-review.md
│   ├── code-simplifier--code-simplifier.md
│   ├── security-guidance--security-guidance-hooks.md
│   └── ...
```

## Notes

- This skill imports from `claude-plugins-official`. User-installed plugins in other cache paths can be added by extending the `CACHE_DIR` scan.
- **Skills** are copied verbatim — no frontmatter is rewritten, no paths are adjusted. The `.agents/skills/` convention uses the same `SKILL.md` format.
- **Commands and agents** are copied as `SKILL.md` with their original frontmatter and content preserved. They work natively as skills because the YAML frontmatter format (`name`, `description`) is compatible.
- **Hooks** get a generated `SKILL.md` wrapper that describes what the hooks do and includes the handler scripts for reference. This makes hook logic discoverable by any AI agent.
- When a command references agents (e.g., `feature-dev` uses `code-explorer`, `code-architect`, `code-reviewer`), the agent files are also copied into the command's `references/` directory AND imported as standalone skills. This gives maximum flexibility — the full workflow is available as one skill, and individual agents can be invoked independently.
- Some skills reference sibling files (e.g., `systematic-debugging` references `defense-in-depth.md`). These are preserved because the entire skill directory is copied.
- Plugins without any `skills/`, `commands/`, `agents/`, or `hooks/` directories (e.g., MCP-only plugins like `context7`, `playwright`) are automatically skipped.
- **VS Code Copilot** picks up `.github/instructions/*.md` files as custom instructions. Only the `SKILL.md` content is copied there (not reference files) since VS Code reads flat markdown.
- **Antigravity/Codex** uses the full `.agents/skills/<plugin>/<skill>/` structure with all supporting files intact.
- The script automatically removes a leftover `.zsh` file if one exists in the project root.
- **To reverse the conversion**, restore the original skills by re-running this import with `OVERWRITE=1`.
