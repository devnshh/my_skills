# Skill: Import Claude Code Plugin Skills to Local Antigravity Format

## Description

Automatically imports all skills from the Claude Code plugins cache (`~/.claude/plugins/cache/`) into the local project's `.agents/skills/` directory (Antigravity/Codex format). This copies skill directories — including SKILL.md files and all reference/supporting files — without modifying their content.

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

### Step 4: Copy Skills to `.agents/skills/`

For each discovered skill directory, copy it **in its entirety** (preserving internal structure) to:

```
<project-root>/.agents/skills/<skill-name>/
```

**Rules:**
- **Do NOT modify** any file content — copy everything as-is.
- Preserve the full directory tree under each skill (subdirectories, reference files, scripts, etc.).
- If a skill with the same name already exists in `.agents/skills/`, **skip it** unless the user explicitly requests overwriting. Report which skills were skipped.
- Create the `.agents/skills/` directory if it does not exist.

### Step 5: Handle Naming Conflicts

If two different plugins provide a skill with the same directory name:
- Prefix with the plugin name: `.agents/skills/<plugin>--<skill-name>/`
- Log this to the user so they're aware of the disambiguation.

### Step 6: Report Results

After import, provide a summary:

```
Imported Skills Summary
=======================
Source: ~/.claude/plugins/cache/claude-plugins-official/

Plugin: superpowers (v4.3.1)
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

Plugin: figma (v1.2.0)
  ✓ implement-design
  ✓ code-connect-components
  ✓ create-design-system-rules

Plugin: claude-md-management (v1.0.0)
  ✓ claude-md-improver

Plugin: frontend-design (205b6e0b3036)
  ✓ frontend-design

Skipped (already exists): <list any skipped>
Skipped (no skills): code-simplifier, context7, playwright, pyright-lsp, security-guidance, serena, typescript-lsp

Total: X skills imported to .agents/skills/
```

## Implementation

Run this shell script from the project root to perform the import:

```bash
#!/bin/bash
set -euo pipefail

CACHE_DIR="$HOME/.claude/plugins/cache/claude-plugins-official"
TARGET_DIR=".agents/skills"

if [[ ! -d "$CACHE_DIR" ]]; then
  echo "ERROR: Cache directory not found: $CACHE_DIR"
  exit 1
fi

mkdir -p "$TARGET_DIR"

imported=0
skipped_exists=()
skipped_no_skills=()
conflicts=()

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
  echo "Plugin: $plugin (v$best_version)"

  # Copy each skill directory
  for skill_dir in "$best_version_dir"/skills/*/; do
    [[ -d "$skill_dir" ]] || continue
    skill=$(basename "$skill_dir")

    # Verify it has a SKILL.md
    if [[ ! -f "$skill_dir/SKILL.md" ]]; then
      continue
    fi

    target="$TARGET_DIR/$skill"

    # Handle existing skill
    if [[ -d "$target" ]]; then
      skipped_exists+=("$skill")
      echo "  ⏭ $skill (already exists, skipped)"
      continue
    fi

    # Handle naming conflicts (same skill name from different plugin)
    if [[ -d "$TARGET_DIR/$skill" ]]; then
      target="$TARGET_DIR/${plugin}--${skill}"
      conflicts+=("$skill -> ${plugin}--${skill}")
      echo "  ⚠ $skill (conflict, imported as ${plugin}--${skill})"
    fi

    # Copy the entire skill directory preserving structure
    cp -R "$skill_dir" "$target"
    echo "  ✓ $skill"
    ((imported++))
  done
done

echo ""
echo "=============================="
echo "Import Complete"
echo "=============================="
echo "Total imported: $imported skills"
echo "Target: $TARGET_DIR/"

if [[ ${#skipped_exists[@]} -gt 0 ]]; then
  echo ""
  echo "Skipped (already exist): ${skipped_exists[*]}"
fi

if [[ ${#skipped_no_skills[@]} -gt 0 ]]; then
  echo ""
  echo "Skipped (no skills): ${skipped_no_skills[*]}"
fi

if [[ ${#conflicts[@]} -gt 0 ]]; then
  echo ""
  echo "Naming conflicts resolved:"
  for c in "${conflicts[@]}"; do
    echo "  $c"
  done
fi
```

## Overwrite Mode

If the user requests overwriting existing skills, modify the behavior:
- Instead of skipping when a skill directory already exists, **remove the existing directory first** and replace it with the fresh copy from the cache.
- Clearly report which skills were overwritten.

To enable overwrite mode, pass `--overwrite` or set `OVERWRITE=1`:

```bash
OVERWRITE=1 bash -c '<script above with overwrite logic>'
```

In overwrite mode, replace the skip block with:

```bash
if [[ -d "$target" ]]; then
  if [[ "${OVERWRITE:-0}" == "1" ]]; then
    rm -rf "$target"
    echo "  ↻ $skill (overwritten)"
  else
    skipped_exists+=("$skill")
    echo "  ⏭ $skill (already exists, skipped)"
    continue
  fi
fi
```

## Notes

- This skill only imports from `claude-plugins-official`. User-installed plugins in other cache paths can be added by extending the `CACHE_DIR` scan.
- Skills are copied verbatim — no frontmatter is rewritten, no paths are adjusted. The `.agents/skills/` convention uses the same `SKILL.md` format.
- Some skills reference sibling files (e.g., `systematic-debugging` references `defense-in-depth.md`). These are preserved because the entire skill directory is copied.
- Plugins without a `skills/` directory (e.g., MCP-only plugins like `context7`, `playwright`) are automatically skipped.
