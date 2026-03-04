#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target_path="${1:-$root_dir/api/deploy_metadata.json}"

mkdir -p "$(dirname "$target_path")"
bash "$root_dir/scripts/resolve_deploy_metadata.sh" > "$target_path"
