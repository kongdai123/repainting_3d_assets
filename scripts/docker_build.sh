#!/usr/bin/env bash
set -e
if [ ! -z "${DEBUG}" ]; then
    set -x
fi

EXTRA=""
if [ ! -z "${DEBUG}" ]; then
    EXTRA="--build-arg DEBUG=${DEBUG}"
fi

docker build \
    --pull \
    --tag repainting_3d_assets \
    -f scripts/Dockerfile \
    ${EXTRA} \
    .
