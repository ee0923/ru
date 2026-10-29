#!/usr/bin/env bash
# RustDesk replayable DMG release upload.
set -euo pipefail

: "${DMG_PATH:?DMG_PATH is required}"
: "${RELEASE_TAG:?RELEASE_TAG is required}"
: "${RELEASE_TARGET:?RELEASE_TARGET is required}"
: "${GH_REPO:?GH_REPO is required}"
: "${GH_TOKEN:?GH_TOKEN is required}"

echo "[rustdesk-publish-dmg] script $(shasum -a 256 "${BASH_SOURCE[0]}")"
test -s "$DMG_PATH"
echo "[rustdesk-publish-dmg] asset $(shasum -a 256 "$DMG_PATH")"
command -v gh >/dev/null

for attempt in 1 2 3 4 5; do
  echo "[rustdesk-publish-dmg] attempt=$attempt/5"
  if gh release view "$RELEASE_TAG" >/dev/null ||
     gh release create "$RELEASE_TAG" --target "$RELEASE_TARGET" \
       --prerelease --title "$RELEASE_TAG" --notes ""; then
    if gh release upload "$RELEASE_TAG" "$DMG_PATH" --clobber; then
      exit 0
    fi
  fi
  if [[ "$attempt" -lt 5 ]]; then
    sleep "$((attempt * 10))"
  fi
done

echo "::error::DMG publication failed after 5 attempts."
exit 1
