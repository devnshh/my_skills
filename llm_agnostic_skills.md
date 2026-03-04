# Skill: Convert Local Skills to LLM-Agnostic Format

## Description

Scans all skill files (`SKILL.md`) in the project's `.agents/skills/` directory and rewrites them to be **LLM-agnostic** — removing or generalizing any references to a specific AI provider (Claude, GPT, Gemini, etc.) while preserving the **exact original logic, procedure, structure, and code** of each skill. The goal is to make every skill usable by any LLM or AI coding agent, regardless of provider.

## When to Use

- After importing skills from a provider-specific source (e.g., Claude Code plugins)
- When preparing skills for use across multiple AI assistants (Claude, GPT, Copilot, Gemini, Codex, etc.)
- When the user asks to "make skills generic", "remove Claude references", "make LLM-agnostic", or "universalize skills"
- Before sharing skills publicly or across teams that use different AI tools

## Procedure

### Step 1: Discover All Skill Files

Recursively find every `SKILL.md` file under `.agents/skills/`:

```bash
find .agents/skills -name "SKILL.md" -type f
```

Also process any `.md` files in `.github/instructions/` if they exist (these are the VS Code Copilot copies).

### Step 2: Identify Provider-Specific Language

For each `SKILL.md`, scan for language that ties the skill to a specific LLM provider. Common patterns to detect:

| Provider-Specific | LLM-Agnostic Replacement |
|---|---|
| `Claude` (when referring to the AI agent) | `the AI agent` / `the assistant` |
| `Claude Code` | `the AI coding agent` |
| `Anthropic` (when referring to the provider generically) | `the AI provider` |
| `Claude's` (possessive, referring to capabilities) | `the agent's` |
| `Ask Claude to...` | `Ask the AI agent to...` |
| `Claude will...` / `Claude should...` | `The agent will...` / `The agent should...` |
| `claude-*` in tool/plugin names within prose | Keep as-is (these are identifiers, not branding) |
| `~/.claude/` in file paths | Keep as-is (these are real system paths) |
| `CLAUDE.md` as a filename | Keep as-is (this is a real filename) |
| `GPT` / `ChatGPT` / `OpenAI` (when referring to the AI agent) | `the AI agent` / `the assistant` |
| `Gemini` / `Google AI` (when referring to the AI agent) | `the AI agent` / `the assistant` |
| `Copilot` (when referring to the AI agent, not VS Code Copilot the product) | `the AI agent` / `the assistant` |

### Step 3: Apply Replacements With Precision

**CRITICAL RULES — what to change and what to preserve:**

#### DO Replace:
- References to a specific LLM **as the actor** performing the skill (e.g., "Claude will execute this plan" → "The agent will execute this plan")
- Provider-specific capability descriptions that are actually generic (e.g., "Claude can read files" → "The agent can read files")
- Instructions directed at a specific LLM (e.g., "Tell Claude to..." → "Tell the agent to...")
- Anthropic/OpenAI/Google-specific best practice references **in prose** (e.g., "Follow Anthropic's guidelines for..." → "Follow best practices for...")

#### DO NOT Replace:
- **File paths** — `~/.claude/`, `CLAUDE.md`, `.claude/` are real filesystem paths. Never change these.
- **Tool/plugin identifiers** — `claude-md-management`, `claude-md-improver`, etc. are directory/tool names. Never rename these.
- **Code blocks** — Do not modify anything inside ``` fenced code blocks, shell scripts, or inline code. These contain real commands, paths, and identifiers.
- **Quoted strings** — Text inside quotes that represents actual values (config keys, filenames, etc.) must stay as-is.
- **URLs** — Any links to documentation, repos, etc. must stay as-is.
- **The word "Claude" when it's part of a proper noun/product name being referenced** — e.g., "Compatible with Claude Code" in a features list is factual, not agent-directing. These can optionally be kept or generalized to "Compatible with AI coding agents" depending on context.
- **Skill procedure logic** — The steps, conditions, loops, file operations, and every piece of functional logic must remain **exactly** the same.
- **Supporting/reference files** — Only process `SKILL.md` files. Do not modify reference files, scripts, or other supporting files within skill directories.

### Step 4: Process Each File

For each `SKILL.md`:

1. **Read** the entire file content.
2. **Identify** all lines that contain provider-specific language (outside of code blocks and file paths).
3. **Replace** provider-specific terms with LLM-agnostic equivalents using the mapping in Step 2.
4. **Verify** that no code blocks, file paths, tool names, or URLs were modified.
5. **Write** the updated content back to the same file, overwriting the original.

**Context-awareness is essential.** The same word can mean different things:
- `"Claude will scan the directory"` → Replace `Claude` (it's the agent acting)
- `"~/.claude/plugins/cache/"` → Do NOT replace (it's a file path)
- `"claude-md-improver"` → Do NOT replace (it's a tool/directory name)
- `"as recommended by Anthropic"` → Replace with `"as recommended"` or `"as a best practice"`

### Step 5: Process VS Code Instruction Files

If `.github/instructions/` exists, apply the same transformations to all `.md` files there. These are flat copies of SKILL.md files and should receive identical treatment.

### Step 6: Validate No Logic Was Changed

After processing, verify for each file:
- All code blocks (``` fenced) are **byte-identical** to the original.
- All file paths remain unchanged.
- All shell commands remain unchanged.
- The number of procedure steps is the same.
- No new steps, conditions, or logic were added or removed.

### Step 7: Report Results

Provide a summary after conversion:

```
LLM-Agnostic Conversion Summary
================================
Scanned: .agents/skills/ + .github/instructions/

Processed:
  ✓ superpowers/brainstorming/SKILL.md (3 replacements)
  ✓ superpowers/writing-skills/SKILL.md (7 replacements)
  ✓ superpowers/systematic-debugging/SKILL.md (2 replacements)
  — superpowers/using-git-worktrees/SKILL.md (no changes needed)
  ✓ figma/implement-design/SKILL.md (1 replacement)
  ...

VS Code instructions:
  ✓ superpowers--brainstorming.md (3 replacements)
  ...

Total: X files processed, Y replacements made
Files unchanged (already agnostic): Z
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
unchanged=0

process_file() {
  local file="$1"
  local display_name="$2"
  local count=0

  # Create a working copy
  local tmp_file
  tmp_file=$(mktemp)
  cp "$file" "$tmp_file"

  # We use perl to do context-aware replacements:
  # - Skip content inside fenced code blocks
  # - Skip file paths containing .claude/ or claude- prefixed identifiers
  # - Only replace "Claude" (capitalized, as the agent) in prose context

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
    s/(~?\/?(?:\.claude|claude-)[^\s\)\"]*)/push @paths, $1; "___PATH_${$#paths}___"/ge;

    # Protect URLs
    my @urls;
    s/(https?:\/\/[^\s\)\]]+)/push @urls, $1; "___URL_${$#urls}___"/ge;

    # Protect CLAUDE.md filename references
    my @filenames;
    s/(CLAUDE\.md)/push @filenames, $1; "___FNAME_${$#filenames}___"/ge;

    # Now apply replacements on the remaining prose:

    # "Claude Code" as a product the agent is part of -> "the AI coding agent"
    s/\bClaude Code\b/the AI coding agent/g;

    # "Claude will/should/can/does" -> "The agent will/should/can/does"
    s/\bClaude (will|should|can|does|may|might|could|would)\b/The agent $1/g;

    # "tell/ask/instruct Claude" -> "tell/ask/instruct the agent"
    s/\b(tell|Tell|ask|Ask|instruct|Instruct|have|Have|let|Let) Claude\b/$1 the agent/g;

    # "Claude'\''s" possessive -> "the agent'\''s"
    s/\bClaude'\''s\b/the agent'\''s/g;

    # "by Anthropic" -> "as a best practice" (in recommendation context)
    s/\b(recommended|suggested|advised) by Anthropic\b/$1 as a best practice/g;
    s/\bAnthropic'\''s (guidelines|recommendations|best practices|docs)\b/the provider'\''s $1/g;
    s/\bfollow Anthropic\b/follow the provider/gi;

    # Standalone "Claude" as subject at start of sentence
    s/(?<=\. )Claude (?!\.md)/The agent /g;
    s/^Claude (?!\.md)/The agent /gm;

    # "Claude" after common prepositions in prose (to Claude, with Claude, for Claude)
    s/\b(to|with|for|from|by) Claude\b/$1 the agent/gi;

    # Restore protected content
    s/___FNAME_(\d+)___/$filenames[$1]/ge;
    s/___URL_(\d+)___/$urls[$1]/ge;
    s/___PATH_(\d+)___/$paths[$1]/ge;
    s/___INLINE_(\d+)___/$inlines[$1]/ge;
    s/___CODEBLOCK_(\d+)___/$blocks[$1]/ge;
  ' "$tmp_file"

  # Count how many lines differ
  count=$(diff "$file" "$tmp_file" | grep "^[<>]" | grep "^<" | wc -l | tr -d ' ')

  if [[ "$count" -gt 0 ]]; then
    cp "$tmp_file" "$file"
    echo "  ✓ $display_name ($count replacements)"
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

# Process .agents/skills/
if [[ -d "$AGENTS_DIR" ]]; then
  echo "Processing $AGENTS_DIR/..."
  while IFS= read -r -d '' skill_file; do
    rel_path="${skill_file#$AGENTS_DIR/}"
    process_file "$skill_file" "$rel_path"
  done < <(find "$AGENTS_DIR" -name "SKILL.md" -type f -print0 | sort -z)
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
echo "Files unchanged (already agnostic): $unchanged"
```

## Dry Run Mode

To preview changes without modifying any files, set `DRY_RUN=1`:

```bash
DRY_RUN=1 bash convert-agnostic.sh
```

To support this, wrap the write-back in the `process_file` function:

```bash
if [[ "$count" -gt 0 ]]; then
  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    echo "  ⚡ $display_name ($count replacements — dry run, not written)"
    diff --unified=1 "$file" "$tmp_file" || true
  else
    cp "$tmp_file" "$file"
    echo "  ✓ $display_name ($count replacements)"
  fi
  total_replacements=$((total_replacements + count))
fi
```

## Notes

- **Code blocks are never touched.** The perl script extracts all fenced code blocks before applying any replacements, then restores them after. This guarantees shell scripts, commands, file paths in code, and configuration snippets remain byte-identical.
- **File paths and identifiers are protected.** Patterns like `~/.claude/`, `claude-md-improver`, and `CLAUDE.md` are regex-matched and excluded before any prose replacements run.
- **Only `SKILL.md` files are modified.** Supporting files (reference docs, scripts, examples) within skill directories are never touched, since they may contain code, configs, or documentation with intentional provider-specific references.
- **The replacement is idempotent.** Running the script multiple times produces the same result — already-converted text won't be double-replaced (e.g., "the agent" won't become "the the agent").
- **Manual review is recommended** after conversion for edge cases the automated regex can't catch — e.g., nuanced prose where "Claude" is used in a way that needs a different phrasing than "the agent".
- **To reverse the conversion**, restore the original skills by re-running the import skill (`skill_import.md`) with `OVERWRITE=1`.
