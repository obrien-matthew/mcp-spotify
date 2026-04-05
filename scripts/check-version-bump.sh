#!/usr/bin/env bash
set -euo pipefail

PACKAGE_NAME="mcp-spotify"

# Determine what's changing relative to the remote tracking branch
remote_ref=$(git rev-parse --abbrev-ref --symbolic-full-name @{upstream} 2>/dev/null || echo "")
if [ -z "$remote_ref" ]; then
    echo "No upstream branch set -- skipping version check."
    exit 0
fi

changed_files=$(git diff --name-only "$remote_ref"...HEAD 2>/dev/null || "")
if ! echo "$changed_files" | grep -q '^src/'; then
    exit 0
fi

# src/ files changed -- check if version was bumped
local_version=$(grep '^version' pyproject.toml | head -1 | sed 's/.*"\(.*\)"/\1/')

pypi_version=$(curl -sf "https://pypi.org/pypi/${PACKAGE_NAME}/json" \
    | grep -o '"version":"[^"]*"' | head -1 | sed 's/"version":"//;s/"//' || echo "")

if [ -z "$pypi_version" ]; then
    echo "Could not fetch PyPI version for ${PACKAGE_NAME} -- skipping check."
    exit 0
fi

if [ "$local_version" = "$pypi_version" ]; then
    echo ""
    echo "!! Version bump required !!"
    echo ""
    echo "  src/ files changed but version is still ${local_version} (same as PyPI)."
    echo ""
    echo "  Run one of:"
    echo "    uv version --bump patch   (${local_version} -> bug fix)"
    echo "    uv version --bump minor   (${local_version} -> new feature)"
    echo "    uv version --bump major   (${local_version} -> breaking change)"
    echo ""
    exit 1
fi

exit 0
