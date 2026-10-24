#!/usr/bin/env bash
# Build: tsc -> dist/js, copy html/css/mock -> dist/
set -euo pipefail
cd "$(dirname "$0")"
rm -rf dist
mkdir -p dist/js dist/styles dist/mock
tsc -p tsconfig.json
cp ./*.html dist/
cp styles/*.css dist/styles/
cp mock/*.json dist/mock/
echo "built -> $(pwd)/dist"
