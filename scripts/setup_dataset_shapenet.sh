#!/usr/bin/env bash
set -e
set -x

if ! type source > /dev/null 2>&1; then
    echo "Restarting the script with bash interpreter"
    bash "$0" "$@"
    exit $?
fi

if [ -z "${REPAINTING3D_CONDA_ROOT}" ]; then
    echo "REPAINTING3D_CONDA_ROOT not set or is empty"
    exit 255
fi

if [ ! -f "${REPAINTING3D_CONDA_ROOT}/miniconda3/bin/conda" ]; then
    echo "\"conda\" not found, check setup_conda_bin.sh"
    exit 255
fi

if [ -z "${REPAINTING3D_DATASET_ROOT}" ]; then
    echo "REPAINTING3D_DATASET_ROOT not set or is empty"
    exit 255
fi

if [ -f "${REPAINTING3D_DATASET_ROOT}/.marker.dataset.shapenet.completed" ]; then
    echo "Dataset already prepared"
    exit 0
fi

REPAINTING3D_ENV_NAME="${REPAINTING3D_ENV_NAME:-repainting_3d_assets}"

source "${REPAINTING3D_CONDA_ROOT}/miniconda3/bin/activate" "${REPAINTING3D_ENV_NAME}"

download_official() {
    mkdir -p "${REPAINTING3D_DATASET_ROOT}"
    cd "${REPAINTING3D_DATASET_ROOT}"
    wget --timeout=10 --tries=3 --no-check-certificate https://shapenet.cs.stanford.edu/shapenet/obj-zip/ShapeNetSem.v0/metadata.csv || true
    wget --timeout=10 --tries=3 --no-check-certificate https://shapenet.cs.stanford.edu/shapenet/obj-zip/ShapeNetSem.v0/models-OBJ.zip || true
    if [ -f "${REPAINTING3D_DATASET_ROOT}/metadata.csv" -a -f "${REPAINTING3D_DATASET_ROOT}/models-OBJ.zip" ]; then
        unzip models-OBJ.zip || return 1
        touch "${REPAINTING3D_DATASET_ROOT}/.marker.dataset.shapenet.completed"
    fi
}

download_fallback() {
    rm -rf "${REPAINTING3D_DATASET_ROOT}"
    mkdir -p "${REPAINTING3D_DATASET_ROOT}"
    cd "${REPAINTING3D_DATASET_ROOT}"
    git clone https://dagshub.com/toshas/ShapeNetSem-Dataset_of_3D_Shapes.git
    cd ShapeNetSem-Dataset_of_3D_Shapes
    dvc remote add origin --local https://dagshub.com/Rutam21/ShapeNetSem-Dataset_of_3D_Shapes.dvc
    dvc remote modify origin --local auth basic
    dvc remote modify origin --local user "${DAGSHUB_USER}"
    dvc remote modify origin --local password "${DAGSHUB_TOKEN}"
    dvc remote add fork --local https://dagshub.com/toshas/ShapeNetSem-Dataset_of_3D_Shapes.dvc
    dvc remote modify fork --local auth basic
    dvc remote modify fork --local user "${DAGSHUB_USER}"
    dvc remote modify fork --local password "${DAGSHUB_TOKEN}"
    dvc pull -r fork metadata.csv.dvc
    dvc pull -r origin models.dvc
    mv models metadata.csv ..
    rm -rf "${REPAINTING3D_DATASET_ROOT}/ShapeNetSem-Dataset_of_3D_Shapes"
    touch "${REPAINTING3D_DATASET_ROOT}/.marker.dataset.shapenet.completed"
}

download_official

if [ ! -f "${REPAINTING3D_DATASET_ROOT}/.marker.dataset.shapenet.completed" ]; then
    if [ ! -z "${DAGSHUB_USER}" -a ! -z "${DAGSHUB_TOKEN}" ]; then
        download_fallback
    else
        echo "Looks like the official ShapeNet source is unavailable. A fallback option requires a www.dagshub.com account.
Pass the account information in environment variables DAGSHUB_USER and DAGSHUB_TOKEN and rerun the same setup command again.
See https://dagshub.com/user/settings/tokens how to make an account and obtain a token.
Example:
DAGSHUB_USER=<your_username> DAGSHUB_TOKEN=<your_token> $0 $@"
    fi
fi

if [ ! -f "${REPAINTING3D_DATASET_ROOT}/.marker.dataset.shapenet.completed" ]; then
    echo "Dataset installation failed"
    exit 255
fi
