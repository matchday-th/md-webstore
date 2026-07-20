#!/usr/bin/env bash
# Assemble the static, frontend-only mock build into dist/ for AWS Amplify Hosting.
# Layout:
#   dist/                 -> hub page + classic HTML pages (login, store, admin, provider)
#   dist/studio/          -> built Vue "studio" app (frontend-vue)
set -euo pipefail

cd "$(dirname "$0")/.."

rm -rf dist
mkdir -p dist

# Pages reference scripts at /frontend-assets/*.js
mkdir -p dist/frontend-assets
cp frontend/*.html dist/
cp frontend/*.js dist/frontend-assets/

if [ ! -d frontend-vue/dist ]; then
  echo "frontend-vue/dist not found - run 'npm run build' in frontend-vue first" >&2
  exit 1
fi
cp -R frontend-vue/dist dist/studio

echo "dist/ assembled:"
find dist -maxdepth 2 -type f | sort
