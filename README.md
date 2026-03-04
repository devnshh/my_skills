# My Skills

A collection of custom skills I've built for use with AI coding agents (Claude Code, VS Code Copilot, Antigravity/Codex, etc.). These are reusable instruction sets that automate repetitive workflows and extend what AI assistants can do in my projects.

## Skills

| Skill | Description |
|-------|-------------|
| [skill_import.md](skill_import.md) | Imports all Claude Code plugin skills from the local cache into a project, supporting both `.agents/skills/` (Antigravity/Codex) and `.github/instructions/` (VS Code Copilot) formats. |

## How Skills Work

Each skill is a markdown file describing a procedure an AI agent can follow — when to use it, step-by-step instructions, and often a ready-to-run script. They act like reusable automation recipes that any compatible AI assistant can pick up and execute.

## Usage

Point your AI agent at a skill file, or copy skills into your project's `.agents/skills/` or `.github/instructions/` directory for automatic discovery.

## License

Personal use. Feel free to reference or adapt for your own workflows.
