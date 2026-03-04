#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

resolve_version() {
  local version="${APP_VERSION:-}"

  if [ -z "$version" ] && [ -f "$root_dir/api/version.py" ]; then
    version="$(sed -n 's/^APP_VERSION = \"\\(.*\\)\"$/\\1/p' "$root_dir/api/version.py" | head -n 1)"
  fi

  if [ -z "$version" ]; then
    version="0.0.0"
  fi

  printf '%s' "$version"
}

resolve_git_sha() {
  local var_name
  local candidate=""

  for var_name in COMMIT_SHA GIT_COMMIT GIT_SHA RENDER_GIT_COMMIT VERCEL_GIT_COMMIT_SHA SOURCE_COMMIT; do
    candidate="${!var_name:-}"
    if [ -n "$candidate" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  done

  if command -v git >/dev/null 2>&1 && git -C "$root_dir" rev-parse --git-dir >/dev/null 2>&1; then
    candidate="$(git -C "$root_dir" rev-parse HEAD 2>/dev/null || true)"
    if [ -n "$candidate" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  fi

  printf 'unknown'
}

version="$(resolve_version)"
git_sha="$(resolve_git_sha)"
short_sha="unknown"

if [ "$git_sha" != "unknown" ]; then
  short_sha="$(printf '%s' "$git_sha" | cut -c1-7)"
fi

printf '{"version":"%s","git_sha":"%s","short_sha":"%s"}\n' "$version" "$git_sha" "$short_sha"
