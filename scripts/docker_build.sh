#!/usr/bin/env bash
set -e
set -x

SELF=$(realpath "$0")
SELF_DIR=$(dirname "${SELF}")
REPO_DIR=$(realpath "${SELF_DIR}/..")

nvidia-docker build \
  --pull \
  --tag second_life_3d_assets \
  -f "${SELF_DIR}/Dockerfile" \
  "${REPO_DIR}"
