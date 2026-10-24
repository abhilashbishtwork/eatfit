#!/bin/sh
# Build the EatFit site from site.config.json.
#   ./build.sh         build every page and SEO file
#   ./build.sh check   build, then verify the output against a local server
set -e
cd "$(dirname "$0")"
python3 build/images.py
python3 build/generate.py
if [ "$1" = "check" ]; then
  python3 build/check.py
fi
