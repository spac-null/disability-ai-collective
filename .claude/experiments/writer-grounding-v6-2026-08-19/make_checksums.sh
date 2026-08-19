#!/bin/bash
# WG-6 evidence manifest. Hashes every file in the experiment except the manifest itself.
cd "$(dirname "$0")" || exit 1
find . -type f ! -name SHA256SUMS.txt -print0 \
  | sort -z | xargs -0 shasum -a 256 > SHA256SUMS.txt
echo "hashed $(wc -l < SHA256SUMS.txt) files"
echo "verified OK: $(shasum -a 256 -c SHA256SUMS.txt 2>/dev/null | grep -c ': OK$')"
echo "FAILED: $(shasum -a 256 -c SHA256SUMS.txt 2>/dev/null | grep -c 'FAILED')"
