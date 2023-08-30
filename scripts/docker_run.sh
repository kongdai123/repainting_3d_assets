#!/usr/bin/env bash
set -e
if ! type source > /dev/null 2>&1; then
    bash "$0" "$@"
    exit $?
fi
if [ ! -z "${DEBUG}" ]; then
    set -x
fi

if [ $# -lt 3 -o $# -gt 4 ]; then
    echo "Error: Insufficient command line arguments:"
    echo "$0 <path_input> <path_output> <prompt> [path_cache]"
    exit 255
fi

if [ -z "${CUDA_VISIBLE_DEVICES}" ]; then
    echo "CUDA_VISIBLE_DEVICES not set; assigning GPU id 0"
    CUDA_VISIBLE_DEVICES=0
fi

PATH_IN="$(readlink -f "$1")"
shift
PATH_OUT="$1"
shift
PROMPT="$1"
shift

PATH_IN_DIR=$(dirname "${PATH_IN}")
PATH_IN_FILE=$(basename "${PATH_IN}")
mkdir -p "${PATH_OUT}"
PATH_OUT="$(readlink -f "${PATH_OUT}")"

EXTRA=""
if [ $# -eq 1 ]; then
    PATH_CACHE="$1"
    mkdir -p "${PATH_CACHE}"
    PATH_CACHE="$(readlink -f "${PATH_CACHE}")"
    EXTRA+=" -v "${PATH_CACHE}":/repainting_3d_assets/hfcache"
fi
if [ ! -z "${DEBUG}" ]; then
    EXTRA+=" -e DEBUG="${DEBUG}""
fi

docker run \
    -it \
    --rm \
    --gpus "device=${CUDA_VISIBLE_DEVICES}" \
    -v .:/repainting_3d_assets/code \
    -v "${PATH_IN_DIR}":/repainting_3d_assets/input \
    -v "${PATH_OUT}":/repainting_3d_assets/output \
    ${EXTRA} \
    toshas/repainting_3d_assets:v1 \
    bash /repainting_3d_assets/code/scripts/conda_run.sh \
        /repainting_3d_assets \
        "/repainting_3d_assets/input/${PATH_IN_FILE}" \
        /repainting_3d_assets/output/ \
        "${PROMPT}"
