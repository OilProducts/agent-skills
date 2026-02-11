#!/usr/bin/env bash
set -euo pipefail

script_source="${BASH_SOURCE[0]}"
script_dir="$(cd "${script_source%/*}" && pwd)"
python3 "${script_dir}/capture_after_brp_sequence.py" "$@"
