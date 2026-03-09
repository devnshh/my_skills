#!/usr/bin/env python3
"""
sync_mcp.py — Syncs Claude Code plugin MCP servers into VS Code settings.json

Usage:
    python3 sync_mcp.py              # merge, skip existing entries
    python3 sync_mcp.py --overwrite  # replace existing entries
"""

import json
import os
import sys
import glob
import shutil
import argparse
from pathlib import Path
from packaging.version import Version, InvalidVersion


def is_semver(s):
    try:
        Version(s)
        return True
    except InvalidVersion:
        return False


def collect_mcp_servers(cache_dir: Path, enabled_plugins: set) -> dict:
    """
    Walk claude plugin cache, find active .mcp.json for each enabled plugin,
    return normalised dict of { server_name: server_config }.
    """
    servers = {}
    skipped_no_mcp = []
    skipped_not_enabled = []

    for plugin_dir in sorted(cache_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        plugin = plugin_dir.name

        if enabled_plugins and plugin not in enabled_plugins:
            skipped_not_enabled.append(plugin)
            continue

        # Find best non-orphaned version
        semver_candidates = []
        hash_candidates = []

        for version_dir in plugin_dir.iterdir():
            if not version_dir.is_dir():
                continue
            if version_dir.name == ".DS_Store":
                continue
            if (version_dir / ".orphaned_at").exists():
                continue
            if not (version_dir / ".mcp.json").exists():
                continue

            v = version_dir.name
            if is_semver(v):
                semver_candidates.append((Version(v), version_dir))
            else:
                hash_candidates.append(version_dir)

        best_dir = None
        if semver_candidates:
            best_dir = sorted(semver_candidates, key=lambda x: x[0])[-1][1]
        elif hash_candidates:
            best_dir = sorted(hash_candidates, key=lambda d: d.stat().st_mtime, reverse=True)[0]

        if best_dir is None:
            skipped_no_mcp.append(plugin)
            continue

        mcp_path = best_dir / ".mcp.json"
        try:
            data = json.loads(mcp_path.read_text())
        except Exception as e:
            print(f"  [warn] Could not parse {mcp_path}: {e}")
            continue

        # Normalise schema A and schema B
        entries = data.get("mcpServers", data)
        if not isinstance(entries, dict):
            continue

        for server_name, config in entries.items():
            if isinstance(config, dict):
                servers[server_name] = config
                print(f"  found: {plugin} -> server '{server_name}'")

    if skipped_no_mcp:
        print(f"\n  Skipped (no .mcp.json): {', '.join(skipped_no_mcp)}")

    return servers


def find_vscode_mcp_config() -> Path:
    """
    Find the active VS Code user mcp.json.
    VS Code (1.99+) uses a dedicated mcp.json alongside settings.json.
    Falls back to creating one next to the active settings.json.
    """
    base = Path.home() / "Library" / "Application Support" / "Code" / "User"

    # Check active profiles first (most recently modified settings.json wins)
    profiles_dir = base / "profiles"
    if profiles_dir.exists():
        candidates = []
        for profile in profiles_dir.iterdir():
            if not profile.is_dir():
                continue
            s = profile / "settings.json"
            if s.exists():
                candidates.append(profile)
        if candidates:
            candidates.sort(key=lambda p: (p / "settings.json").stat().st_mtime, reverse=True)
            return candidates[0] / "mcp.json"

    return base / "mcp.json"


def merge_servers(mcp_path: Path, new_servers: dict, overwrite: bool) -> tuple[int, int]:
    """
    Merge new_servers into the dedicated mcp.json under "servers".
    Returns (added, skipped) counts.
    """
    if mcp_path.exists():
        try:
            data = json.loads(mcp_path.read_text())
        except Exception as e:
            print(f"[error] Could not parse {mcp_path}: {e}")
            sys.exit(1)
    else:
        data = {}

    existing = data.setdefault("servers", {})
    data.setdefault("inputs", [])

    added = 0
    skipped = 0

    for name, config in new_servers.items():
        if name in existing and not overwrite:
            print(f"  skipped (exists): {name}")
            skipped += 1
        else:
            action = "updated" if name in existing else "added"
            existing[name] = config
            print(f"  {action}: {name}")
            added += 1

    # Write back with backup
    if mcp_path.exists():
        shutil.copy2(mcp_path, mcp_path.with_suffix(".json.bak"))

    mcp_path.write_text(json.dumps(data, indent=4))
    return added, skipped


def get_enabled_plugins() -> set:
    claude_settings = Path.home() / ".claude" / "settings.json"
    if not claude_settings.exists():
        return set()
    try:
        data = json.loads(claude_settings.read_text())
        return {k.split("@")[0] for k in data.get("enabledPlugins", {}).keys()}
    except Exception:
        return set()


def main():
    parser = argparse.ArgumentParser(description="Sync Claude Code MCP servers to VS Code")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing server entries")
    parser.add_argument("--all-plugins", action="store_true", help="Include plugins not in enabledPlugins list")
    args = parser.parse_args()

    cache_dir = Path.home() / ".claude" / "plugins" / "cache" / "claude-plugins-official"
    if not cache_dir.exists():
        print(f"[error] Cache not found: {cache_dir}")
        sys.exit(1)

    enabled = set() if args.all_plugins else get_enabled_plugins()
    print(f"\nEnabled Claude plugins: {', '.join(sorted(enabled)) if enabled else '(all)'}")

    print("\n--- Collecting MCP servers from Claude plugins ---")
    servers = collect_mcp_servers(cache_dir, enabled)

    if not servers:
        print("\nNo MCP servers found to sync.")
        sys.exit(0)

    mcp_path = find_vscode_mcp_config()
    print(f"\n--- Merging into VS Code MCP config ---")
    print(f"Target: {mcp_path}")
    print(f"Mode: {'overwrite' if args.overwrite else 'skip existing'}\n")

    added, skipped = merge_servers(mcp_path, servers, args.overwrite)

    print(f"\n==============================")
    print(f"Sync complete")
    print(f"==============================")
    print(f"Servers added/updated : {added}")
    print(f"Servers skipped       : {skipped}")
    print(f"MCP config file       : {mcp_path}")
    if mcp_path.with_suffix(".json.bak").exists():
        print(f"Backup created        : {mcp_path.with_suffix('.json.bak')}")
    print()
    print("Next step: open a NEW chat session in VS Code — MCP servers are")
    print("discovered at session start. Verify via: MCP: List Servers")
    print()

    # Warn about tokens
    token_servers = {
        "github": "GITHUB_PERSONAL_ACCESS_TOKEN",
        "greptile": "GREPTILE_API_KEY",
    }
    needs_token = [f"  {s} -> ${v}" for s, v in token_servers.items() if s in servers]
    if needs_token:
        print("Servers requiring tokens (set env var or replace placeholder in settings):")
        print("\n".join(needs_token))


if __name__ == "__main__":
    main()
