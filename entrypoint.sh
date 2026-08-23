#!/bin/sh
# Census Assistant container entrypoint.
#
# DATA_DIR is a persistent volume in production (see Dockerfile/fly.toml).
# On first boot of a fresh volume it will be empty, so we seed it once from
# the seed Excel/PDF files baked into the image. On every later boot the
# database already exists in the volume and we skip re-ingestion, so
# admin-uploaded data and edits survive redeploys/restarts.
set -e

DATA_DIR="${DATA_DIR:-/app/data}"
mkdir -p "$DATA_DIR"

if [ ! -f "$DATA_DIR/census_assistant.db" ]; then
    echo "No existing database found in $DATA_DIR — running initial ingestion..."
    python -m backend.ingestion
else
    echo "Existing database found in $DATA_DIR — skipping initial ingestion."
fi

exec python -m backend.main
