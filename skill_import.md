# Skill: Import Claude Code Plugin Skills to Local Format

## Description

Automatically imports all skills from the Claude Code plugins cache (`~/.claude/plugins/cache/`) into the local project, supporting both **Antigravity/Codex** (`.agents/skills/`) and **VS Code Copilot** (`.github/instructions/`) formats. Skills are grouped under their parent plugin folder, preserving the original directory hierarchy. This copies skill directories — including SKILL.md files and all reference/supporting files — without modifying their content.

## When to Use

- When setting up a new project and you want local access to all cached Claude Code skills
- When you want to sync the latest plugin skills into the current workspace
- After installing or updating Claude Code plugins and want local copies
- When the user asks to "import skills", "sync skills", or "convert plugin skills to local format"

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
3. From the remaining (non-orphaned) versions, pick the one to use. If multiple non-orphaned versions exist, prefer the one with the highest semver, or the most recently modified directory for hash-based versions.
4. If **no** non-orphaned version has skills (i.e., no `skills/` subdirectory containing a `SKILL.md`), skip this plugin entirely.

### Step 3: Discover Skills Within Each Plugin Version

Inside the selected version directory, look for the `skills/` subdirectory:

```
~/.claude/plugins/cache/claude-plugins-official/<plugin>/<version>/skills/
```

Each child directory under `skills/` represents one skill. A valid skill directory:
- Contains a `SKILL.md` file
- May contain additional reference files and subdirectories (e.g., `references/`, example files, scripts)

Example structures:

```
skills/
├── claude-md-improver/
│   ├── SKILL.md
│   └── references/
│       ├── quality-criteria.md
│       ├── templates.md
│       └── update-guidelines.md
├── systematic-debugging/
│   ├── SKILL.md
│   ├── CREATION-LOG.md
│   ├── condition-based-waiting.md
│   ├── defense-in-depth.md
│   ├── find-polluter.sh
│   └── root-cause-tracing.md
└── writing-skills/
    ├── SKILL.md
    ├── anthropic-best-practices.md
    ├── examples/
    │   └── CLAUDE_MD_TESTING.md
    └── persuasion-principles.md
```

### Step 4: Copy Skills Preserving Plugin Folder Structure

> **CRITICAL — DO NOT FLATTEN:** Skills MUST be nested inside a plugin-named parent folder. The target path is **two levels deep**: `.agents/skills/<PLUGIN>/<SKILL>/`. Do NOT copy skills directly into `.agents/skills/<SKILL>/` — that is wrong.

For each discovered skill directory, copy it **in its entirety** (preserving internal structure) into a subdirectory named after the **plugin**:

```
<project-root>/.agents/skills/<plugin-name>/<skill-name>/
```

**Correct examples:**
```
.agents/skills/superpowers/brainstorming/SKILL.md          ← CORRECT
.agents/skills/superpowers/systematic-debugging/SKILL.md   ← CORRECT
.agents/skills/figma/implement-design/SKILL.md             ← CORRECT
.agents/skills/claude-md-management/claude-md-improver/SKILL.md ← CORRECT
```

**Wrong examples (DO NOT DO THIS):**
```
.agents/skills/brainstorming/SKILL.md                      ← WRONG (missing plugin folder)
.agents/skills/systematic-debugging/SKILL.md               ← WRONG (missing plugin folder)
```

**Rules:**
- **Do NOT modify** any file content — copy everything as-is.
- **Do NOT flatten** — every skill MUST be inside its plugin's folder.
- Preserve the full directory tree under each skill (subdirectories, reference files, scripts, etc.).
- If a skill already exists at the target path, **skip it** unless the user explicitly requests overwriting. Report which skills were skipped.
- Create the `.agents/skills/<plugin-name>/` directory if it does not exist.
- This structure eliminates naming conflicts since skills are namespaced by plugin.

### Step 5: Copy Skills for VS Code Copilot Compatibility

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

### Step 6: Report Results

After import, provide a summary:

```
Imported Skills Summary
=======================
Source: ~/.claude/plugins/cache/claude-plugins-official/
Targets: .agents/skills/ (Antigravity/Codex) + .github/instructions/ (VS Code Copilot)

Plugin: superpowers (v4.3.1) -> .agents/skills/superpowers/
  ✓ brainstorming
  ✓ dispatching-parallel-agents
  ✓ executing-plans
  ✓ finishing-a-development-branch
  ✓ receiving-code-review
  ✓ requesting-code-review
  ✓ subagent-driven-development
  ✓ systematic-debugging
  ✓ test-driven-development
  ✓ using-git-worktrees
  ✓ using-superpowers
  ✓ verification-before-completion
  ✓ writing-plans
  ✓ writing-skills

Plugin: figma (v1.2.0) -> .agents/skills/figma/
  ✓ implement-design
  ✓ code-connect-components
  ✓ create-design-system-rules

Plugin: claude-md-management (v1.0.0) -> .agents/skills/claude-md-management/
  ✓ claude-md-improver

Plugin: frontend-design (205b6e0b3036) -> .agents/skills/frontend-design/
  ✓ frontend-design

VS Code instructions: 19 files written to .github/instructions/

Skipped (already exists): <list any skipped>
Skipped (no skills): code-simplifier, context7, playwright, pyright-lsp, security-guidance, serena, typescript-lsp

Total: X skills imported
```

## Implementation

Run this shell script **exactly as written** from the project root to perform the import. **Do NOT modify the script** — in particular, do not remove the plugin subfolder logic.

```bash
#!/bin/bash
set -euo pipefail

# === CONFIGURATION ===
CACHE_DIR="$HOME/.claude/plugins/cache/claude-plugins-official"
AGENTS_DIR=".agents/skills"   # Skills go to: .agents/skills/<PLUGIN>/<SKILL>/
VSCODE_DIR=".github/instructions"  # VS Code gets: .github/instructions/<PLUGIN>--<SKILL>.md

if [[ ! -d "$CACHE_DIR" ]]; then
  echo "ERROR: Cache directory not found: $CACHE_DIR"
  exit 1
fi

mkdir -p "$AGENTS_DIR"
mkdir -p "$VSCODE_DIR"

imported=0
vscode_count=0
skipped_exists=()
skipped_no_skills=()

for plugin_dir in "$CACHE_DIR"/*/; do
  plugin=$(basename "$plugin_dir")

  # Find the latest non-orphaned version
  best_version=""
  best_version_dir=""

  for version_dir in "$plugin_dir"*/; do
    [[ -d "$version_dir" ]] || continue
    version=$(basename "$version_dir")
    [[ "$version" == ".DS_Store" ]] && continue

    # Skip orphaned versions
    [[ -f "$version_dir/.orphaned_at" ]] && continue

    # Check if this version has skills
    if [[ -d "$version_dir/skills" ]] && find "$version_dir/skills" -name "SKILL.md" -type f 2>/dev/null | grep -q .; then
      best_version="$version"
      best_version_dir="$version_dir"
    fi
  done

  if [[ -z "$best_version_dir" ]]; then
    skipped_no_skills+=("$plugin")
    continue
  fi

  echo ""
  echo "Plugin: $plugin (v$best_version) -> $AGENTS_DIR/$plugin/"

  # IMPORTANT: Create the PLUGIN subdirectory under .agents/skills/
  # Skills are grouped by plugin: .agents/skills/<PLUGIN>/<SKILL>/
  mkdir -p "$AGENTS_DIR/$plugin"

  # Copy each skill directory INTO the plugin folder
  for skill_dir in "$best_version_dir"/skills/*/; do
    [[ -d "$skill_dir" ]] || continue
    skill=$(basename "$skill_dir")

    # Verify it has a SKILL.md
    if [[ ! -f "$skill_dir/SKILL.md" ]]; then
      continue
    fi

    # CRITICAL: target is PLUGIN/SKILL, not just SKILL
    target="$AGENTS_DIR/$plugin/$skill"

    # Handle existing skill
    if [[ -d "$target" ]]; then
      if [[ "${OVERWRITE:-0}" == "1" ]]; then
        rm -rf "$target"
        echo "  ↻ $skill (overwritten)"
      else
        skipped_exists+=("$plugin/$skill")
        echo "  ⏭ $skill (already exists, skipped)"
        continue
      fi
    fi

    # Copy the entire skill directory preserving structure
    cp -R "$skill_dir" "$target"
    echo "  ✓ $skill"
    ((imported++))

    # Also copy SKILL.md to .github/instructions/ for VS Code Copilot
    vscode_file="$VSCODE_DIR/${plugin}--${skill}.md"
    if [[ ! -f "$vscode_file" ]] || [[ "${OVERWRITE:-0}" == "1" ]]; then
      cp "$skill_dir/SKILL.md" "$vscode_file"
      ((vscode_count++))
    fi
  done
done

echo ""
echo "=============================="
echo "Import Complete"
echo "=============================="
echo "Total imported: $imported skills to $AGENTS_DIR/<plugin>/<skill>/"
echo "VS Code instructions: $vscode_count files written to $VSCODE_DIR/"

if [[ ${#skipped_exists[@]} -gt 0 ]]; then
  echo ""
  echo "Skipped (already exist): ${skipped_exists[*]}"
fi

if [[ ${#skipped_no_skills[@]} -gt 0 ]]; then
  echo ""
  echo "Skipped (no skills): ${skipped_no_skills[*]}"
fi
```

## Overwrite Mode

Overwrite mode is built into the main script. To enable it, set `OVERWRITE=1`:

```bash
OVERWRITE=1 bash import-skills.sh
```

When enabled:
- Existing skill directories in `.agents/skills/<plugin>/<skill>/` are removed and replaced with the fresh copy.
- Existing VS Code instruction files in `.github/instructions/` are also overwritten.
- Overwritten skills are reported with `↻` in the output.

## Output Structure

After running the import, the project will contain:

```
<project-root>/
├── .agents/skills/                          # Antigravity/Codex format (full skill dirs)
│   ├── superpowers/
│   │   ├── brainstorming/
│   │   │   └── SKILL.md
│   │   ├── systematic-debugging/
│   │   │   ├── SKILL.md
│   │   │   ├── defense-in-depth.md
│   │   │   └── find-polluter.sh
│   │   └── writing-skills/
│   │       ├── SKILL.md
│   │       └── examples/
│   ├── figma/
│   │   ├── implement-design/
│   │   └── code-connect-components/
│   ├── claude-md-management/
│   │   └── claude-md-improver/
│   └── frontend-design/
│       └── frontend-design/
├── .github/instructions/                    # VS Code Copilot format (flat SKILL.md copies)
│   ├── superpowers--brainstorming.md
│   ├── superpowers--systematic-debugging.md
│   ├── superpowers--writing-skills.md
│   ├── figma--implement-design.md
│   ├── claude-md-management--claude-md-improver.md
│   └── frontend-design--frontend-design.md
```

## Notes

- This skill only imports from `claude-plugins-official`. User-installed plugins in other cache paths can be added by extending the `CACHE_DIR` scan.
- Skills are copied verbatim — no frontmatter is rewritten, no paths are adjusted. The `.agents/skills/` convention uses the same `SKILL.md` format.
- Some skills reference sibling files (e.g., `systematic-debugging` references `defense-in-depth.md`). These are preserved because the entire skill directory is copied.
- Plugins without a `skills/` directory (e.g., MCP-only plugins like `context7`, `playwright`) are automatically skipped.
- **VS Code Copilot** picks up `.github/instructions/*.md` files as custom instructions. These can be auto-attached to chat contexts or referenced manually. Only the `SKILL.md` content is copied there (not reference files) since VS Code reads flat markdown.
- **Antigravity/Codex** uses the full `.agents/skills/<plugin>/<skill>/` structure with all supporting files intact.
