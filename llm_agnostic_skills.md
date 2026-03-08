# Skill: Convert Local Skills to LLM-Agnostic Format

## Description

Scans all skill files (`SKILL.md`) and supporting markdown in the project's `.agents/skills/` directory and rewrites them to be **LLM-agnostic** — removing or generalizing any references to a specific AI provider (Claude, GPT, Gemini, etc.) while preserving the **exact original logic, procedure, structure, and code** of each skill. The goal is to make every skill usable by any LLM or AI coding agent, regardless of provider.

This also processes **converted plugin content** (commands, agents, hooks that were imported as skills) — including frontmatter fields like `model: sonnet` or `model: opus` that tie content to a specific provider's model lineup.

## When to Use

- After importing skills from a provider-specific source (e.g., Claude Code plugins)
- When preparing skills for use across multiple AI assistants (Claude, GPT, Copilot, Gemini, Codex, etc.)
- When the user asks to "make skills generic", "remove Claude references", "make LLM-agnostic", or "universalize skills"
- Before sharing skills publicly or across teams that use different AI tools
- After running the `skill_import.md` skill to convert imported plugin content

## Procedure

### Step 1: Discover All Processable Files

Recursively find every `SKILL.md` file under `.agents/skills/`:

```bash
find .agents/skills -name "SKILL.md" -type f
```

Also find reference `.md` files within skill directories (e.g., `references/*.md`, agent definitions):

```bash
find .agents/skills -name "*.md" -type f
```

Also process any `.md` files in `.github/instructions/` if they exist (these are the VS Code Copilot copies).

### Step 2: Identify Provider-Specific Language

For each file, scan for language that ties the skill to a specific LLM provider. The replacements are context-aware — different treatment for prose, frontmatter, and protected content.

#### Prose Replacements (outside code blocks, file paths, URLs)

| Provider-Specific | LLM-Agnostic Replacement |
|---|---|
| `Claude` (when referring to the AI agent) | `the AI agent` / `the assistant` |
| `Claude Code` | `the AI coding agent` |
| `Anthropic` (when referring to the provider generically) | `the AI provider` |
| `Claude's` (possessive, referring to capabilities) | `the agent's` |
| `Ask Claude to...` | `Ask the AI agent to...` |
| `Claude will...` / `Claude should...` | `The agent will...` / `The agent should...` |
| `GPT` / `ChatGPT` / `OpenAI` (when referring to the AI agent) | `the AI agent` / `the assistant` |
| `Gemini` / `Google AI` (when referring to the AI agent) | `the AI agent` / `the assistant` |
| `Copilot` (when referring to the AI agent, not VS Code Copilot the product) | `the AI agent` / `the assistant` |
| `Generated with [Claude Code]` | `Generated with AI` |
| `Sonnet agent` / `Haiku agent` / `Opus agent` | `agent` |
| `Launch N Sonnet agents` | `Launch N agents` |
| `Use a Haiku agent to` | `Use an agent to` |

#### Frontmatter Replacements

| Provider-Specific Frontmatter | LLM-Agnostic Replacement |
|---|---|
| `model: sonnet` | remove line entirely |
| `model: opus` | remove line entirely |
| `model: haiku` | remove line entirely |
| `color: red` (model-specific styling) | remove line entirely |
| `color: yellow` | remove line entirely |
| `color: green` | remove line entirely |

#### Protected Content — DO NOT Replace

| What | Why |
|---|---|
| `claude-*` in tool/plugin names within prose | These are identifiers, not branding |
| `~/.claude/` in file paths | Real system paths |
| `CLAUDE.md` as a filename | Real filename (project guidelines) |
| Everything inside ``` fenced code blocks | Real commands, paths, identifiers |
| Everything inside `` inline code `` | Real identifiers |
| URLs (https://...) | Real links |
| Quoted strings that are actual values | Config keys, filenames |
| Tool names in frontmatter (e.g., `Bash(gh pr view:*)`) | Real tool identifiers |

### Step 3: Apply Replacements With Precision

**Context-awareness is essential.** The same word can mean different things:
- `"Claude will scan the directory"` → Replace `Claude` (it's the agent acting)
- `"~/.claude/plugins/cache/"` → Do NOT replace (it's a file path)
- `"claude-md-improver"` → Do NOT replace (it's a tool/directory name)
- `"Use a Haiku agent to check"` → Replace with `"Use an agent to check"`
- `"Launch 5 parallel Sonnet agents"` → Replace with `"Launch 5 parallel agents"`
- `"model: opus"` in frontmatter → Remove the line
- `"as recommended by Anthropic"` → Replace with `"as a best practice"`
- `"🤖 Generated with [Claude Code]"` → Replace with `"🤖 Generated with AI"`

### Step 4: Process Each File

For each `.md` file:

1. **Read** the entire file content.
2. **Identify** all lines that contain provider-specific language (outside of code blocks and file paths).
3. **Replace** provider-specific terms with LLM-agnostic equivalents using the mappings above.
4. **Remove** provider-specific frontmatter fields (`model:`, `color:`) that tie the skill to a specific model.
5. **Verify** that no code blocks, file paths, tool names, or URLs were modified.
6. **Write** the updated content back to the same file, overwriting the original.

### Step 5: Process VS Code Instruction Files

If `.github/instructions/` exists, apply the same transformations to all `.md` files there. These are flat copies of SKILL.md files and should receive identical treatment.

### Step 6: Validate No Logic Was Changed

After processing, verify for each file:
- All code blocks (``` fenced) are **byte-identical** to the original.
- All file paths remain unchanged.
- All shell commands remain unchanged.
- The number of procedure steps is the same.
- No new steps, conditions, or logic were added or removed.
- Frontmatter structure is valid (only `model:` and `color:` fields were removed, not core fields like `name`, `description`, `tools`, `allowed-tools`).

### Step 7: Report Results

Provide a summary after conversion:

```
LLM-Agnostic Conversion Summary
================================
Scanned: .agents/skills/ + .github/instructions/

Processed:
  ✓ superpowers/brainstorming/SKILL.md (3 replacements)
  ✓ superpowers/writing-skills/SKILL.md (7 replacements)
  ✓ feature-dev/feature-dev/SKILL.md (12 replacements, 1 frontmatter field removed)
  ✓ feature-dev/code-reviewer/SKILL.md (5 replacements, 2 frontmatter fields removed)
  ✓ code-review/code-review/SKILL.md (15 replacements)
  ✓ code-simplifier/code-simplifier/SKILL.md (4 replacements, 1 frontmatter field removed)
  — superpowers/using-git-worktrees/SKILL.md (no changes needed)
  ...

VS Code instructions:
  ✓ superpowers--brainstorming.md (3 replacements)
  ✓ feature-dev--feature-dev.md (12 replacements)
  ...

Total: X files processed, Y replacements made, Z frontmatter fields removed
Files unchanged (already agnostic): W
```

## Implementation

The following script automates the text replacements. Run from the project root:

```bash
#!/bin/bash
set -euo pipefail

AGENTS_DIR=".agents/skills"
VSCODE_DIR=".github/instructions"

total_files=0
total_replacements=0
total_frontmatter=0
unchanged=0

process_file() {
  local file="$1"
  local display_name="$2"
  local count=0
  local fm_count=0

  # Create a working copy
  local tmp_file
  tmp_file=$(mktemp)
  cp "$file" "$tmp_file"

  # Strategy: Extract code blocks, replace in prose only, reassemble.
  # Using perl for multi-line awareness.

  perl -0777 -i -pe '
    # Protect code blocks by temporarily replacing them
    my @blocks;
    s/(```[\s\S]*?```)/push @blocks, $1; "___CODEBLOCK_${$#blocks}___"/ge;

    # Protect inline code
    my @inlines;
    s/(`[^`]+`)/push @inlines, $1; "___INLINE_${$#inlines}___"/ge;

    # Protect file paths with .claude or claude- in them
    my @paths;
    s/(~?\/?(?:\.claude|claude-)[^\s\)\"\]]*)/push @paths, $1; "___PATH_${$#paths}___"/ge;

    # Protect URLs
    my @urls;
    s/(https?:\/\/[^\s\)\]]+)/push @urls, $1; "___URL_${$#urls}___"/ge;

    # Protect CLAUDE.md filename references
    my @filenames;
    s/(CLAUDE\.md)/push @filenames, $1; "___FNAME_${$#filenames}___"/ge;

    # ── Frontmatter: remove model-specific fields ──
    # Remove model: lines (sonnet, opus, haiku, etc.)
    s/^model:\s*\S+\s*\n//gm;
    # Remove color: lines (model-specific styling)
    s/^color:\s*\S+\s*\n//gm;

    # ── Provider-specific model references in prose ──

    # "Sonnet agent(s)" / "Haiku agent(s)" / "Opus agent(s)" → "agent(s)"
    s/\b(?:Sonnet|Haiku|Opus)\s+(agents?)\b/$1/gi;

    # "Use a Haiku/Sonnet/Opus agent to" → "Use an agent to"
    s/\bUse a (?:Haiku|Sonnet|Opus) agent\b/Use an agent/gi;

    # "Launch N Sonnet/Haiku/Opus agents" → "Launch N agents"
    s/\b(Launch\s+\d+\s+(?:parallel\s+)?)(?:Sonnet|Haiku|Opus)\s+(agents)\b/$1$2/gi;

    # "Generated with [Claude Code](link)" → "Generated with AI"
    s/Generated with \[Claude Code\]\([^\)]*\)/Generated with AI/g;
    s/Generated with Claude Code/Generated with AI/g;

    # ── Now apply general provider replacements ──

    # "Claude Code" as a product the agent is part of → "the AI coding agent"
    s/\bClaude Code\b/the AI coding agent/g;

    # "Claude will/should/can/does" → "The agent will/should/can/does"
    s/\bClaude (will|should|can|does|may|might|could|would)\b/The agent $1/g;

    # "tell/ask/instruct Claude" → "tell/ask/instruct the agent"
    s/\b(tell|Tell|ask|Ask|instruct|Instruct|have|Have|let|Let) Claude\b/$1 the agent/g;

    # "Claude'\''s" possessive → "the agent'\''s"
    s/\bClaude'\''s\b/the agent'\''s/g;

    # "by Anthropic" → "as a best practice" (in recommendation context)
    s/\b(recommended|suggested|advised) by Anthropic\b/$1 as a best practice/g;
    s/\bAnthropic'\''s (guidelines|recommendations|best practices|docs)\b/the provider'\''s $1/g;
    s/\bfollow Anthropic\b/follow the provider/gi;
    s/\bAnthropic\b/the AI provider/g;

    # Standalone "Claude" as subject at start of sentence
    s/(?<=\. )Claude (?!\.md)/The agent /g;
    s/^Claude (?!\.md)/The agent /gm;

    # "Claude" after common prepositions in prose
    s/\b(to|with|for|from|by) Claude\b/$1 the agent/gi;

    # GPT / ChatGPT / OpenAI
    s/\bChatGPT\b/the AI agent/g;
    s/\bGPT-4o?\b/the AI model/g;
    s/\bGPT\b/the AI agent/g;
    s/\bOpenAI\b/the AI provider/g;

    # Gemini / Google AI
    s/\bGemini\b/the AI agent/g;
    s/\bGoogle AI\b/the AI provider/g;

    # Restore protected content (reverse order)
    s/___FNAME_(\d+)___/$filenames[$1]/ge;
    s/___URL_(\d+)___/$urls[$1]/ge;
    s/___PATH_(\d+)___/$paths[$1]/ge;
    s/___INLINE_(\d+)___/$inlines[$1]/ge;
    s/___CODEBLOCK_(\d+)___/$blocks[$1]/ge;
  ' "$tmp_file"

  # Count how many lines differ
  count=$(diff "$file" "$tmp_file" | grep "^[<>]" | grep "^<" | wc -l | tr -d ' ')

  # Count frontmatter field removals specifically
  fm_count=$(diff "$file" "$tmp_file" | grep "^< " | grep -cE "^< (model|color):" || echo 0)

  if [[ "$count" -gt 0 ]]; then
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
      echo "  ⚡ $display_name ($count replacements${fm_count:+, $fm_count frontmatter fields removed} — dry run, not written)"
      diff --unified=1 "$file" "$tmp_file" || true
    else
      cp "$tmp_file" "$file"
      local extra=""
      if [[ "$fm_count" -gt 0 ]]; then
        extra=", $fm_count frontmatter fields removed"
        total_frontmatter=$((total_frontmatter + fm_count))
      fi
      echo "  ✓ $display_name ($count replacements$extra)"
    fi
    total_replacements=$((total_replacements + count))
  else
    echo "  — $display_name (no changes needed)"
    unchanged=$((unchanged + 1))
  fi

  rm -f "$tmp_file"
  total_files=$((total_files + 1))
}

echo "LLM-Agnostic Conversion"
echo "========================"
echo ""

# Process .agents/skills/ — ALL .md files, not just SKILL.md
if [[ -d "$AGENTS_DIR" ]]; then
  echo "Processing $AGENTS_DIR/..."
  while IFS= read -r -d '' md_file; do
    rel_path="${md_file#$AGENTS_DIR/}"
    process_file "$md_file" "$rel_path"
  done < <(find "$AGENTS_DIR" -name "*.md" -type f -print0 | sort -z)
fi

# Process .github/instructions/
if [[ -d "$VSCODE_DIR" ]]; then
  echo ""
  echo "Processing $VSCODE_DIR/..."
  for md_file in "$VSCODE_DIR"/*.md; do
    [[ -f "$md_file" ]] || continue
    rel_path=$(basename "$md_file")
    process_file "$md_file" "$rel_path"
  done
fi

echo ""
echo "========================"
echo "Conversion Complete"
echo "========================"
echo "Total files processed: $total_files"
echo "Total replacements: $total_replacements"
if [[ "$total_frontmatter" -gt 0 ]]; then
  echo "Frontmatter fields removed: $total_frontmatter"
fi
echo "Files unchanged (already agnostic): $unchanged"
```

## Dry Run Mode

To preview changes without modifying any files, set `DRY_RUN=1`:

```bash
DRY_RUN=1 bash convert-agnostic.sh
```

When dry run is enabled:
- Each file that would be modified shows a unified diff of the changes.
- No files are written.
- The summary shows what would have been changed.

## Notes

- **Code blocks are never touched.** The perl script extracts all fenced code blocks before applying any replacements, then restores them after. This guarantees shell scripts, commands, file paths in code, and configuration snippets remain byte-identical.
- **File paths and identifiers are protected.** Patterns like `~/.claude/`, `claude-md-improver`, and `CLAUDE.md` are regex-matched and excluded before any prose replacements run.
- **All `.md` files are processed.** Unlike the previous version which only touched `SKILL.md` files, this version also processes reference files, agent definitions, and READMEs within skill directories. This is important for converted plugin content where agent definitions and command files are stored as both `SKILL.md` and `references/*.md`.
- **Frontmatter cleanup.** Provider-specific frontmatter fields like `model: sonnet`, `model: opus`, and `color: red` are removed entirely. These fields specify which provider-specific model to use and have no meaning in a provider-agnostic context. Core frontmatter fields (`name`, `description`, `tools`, `allowed-tools`) are preserved.
- **Model name references in prose.** References to specific model tiers like "Sonnet agent", "Haiku agent", "Opus agent" are simplified to just "agent". Phrases like "Launch 5 parallel Sonnet agents" become "Launch 5 parallel agents".
- **The replacement is idempotent.** Running the script multiple times produces the same result — already-converted text won't be double-replaced (e.g., "the agent" won't become "the the agent").
- **Manual review is recommended** after conversion for edge cases the automated regex can't catch — e.g., nuanced prose where "Claude" is used in a way that needs a different phrasing than "the agent".
- **To reverse the conversion**, restore the original skills by re-running the import skill (`skill_import.md`) with `OVERWRITE=1`.
