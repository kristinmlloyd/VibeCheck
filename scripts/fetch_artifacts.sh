#!/usr/bin/env bash
# Simple script to download artifacts from S3 into /data
# Usage: set S3_BUCKET and optionally S3_PREFIX, then run this script during image startup
set -euo pipefail

if [ -z "${S3_BUCKET:-}" ]; then
  echo "S3_BUCKET not set — skipping artifact fetch"
  exit 0
fi

PREFIX=${S3_PREFIX:-}
TARGET_DIR=${TARGET_DIR:-/data}

echo "Fetching artifacts from s3://$S3_BUCKET/$PREFIX to $TARGET_DIR"

# require awscli to be installed in the image if you enable this path
aws s3 sync "s3://$S3_BUCKET/$PREFIX" "$TARGET_DIR"

echo "Artifacts fetched"
