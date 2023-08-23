#!/usr/bin/env bash
set -e
if [ ! -z "${DEBUG}" ]; then
    set -x
fi

if ! type source > /dev/null 2>&1; then
    if [ ! -z "${DEBUG}" ]; then
        echo "Restarting the script with bash interpreter"
    fi
    bash "$0" "$@"
    exit $?
fi
SELF=$(readlink -f "${BASH_SOURCE[0]}")
SELF_DIR=$(dirname "${SELF}")

DISABLE_SHAPENET=1 bash "${SELF_DIR}/setup_all_for_shapenet.sh" "$@"
