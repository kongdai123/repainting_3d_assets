#!/usr/bin/env bash
set -e
set -x

if ! type source > /dev/null 2>&1; then
    echo "Restarting the script with bash interpreter"
    bash "$0" "$@"
    exit $?
fi

if [ -z "${SL3A_CONDA_ROOT}" ]; then
    echo "SL3A_CONDA_ROOT not set or is empty"
    exit 255
fi

if [ ! -f "${SL3A_CONDA_ROOT}/miniconda3/bin/conda" ]; then
    echo "\"conda\" not found, check setup_conda_bin.sh"
    exit 255
fi

if [ -z "${SL3A_DATASET_ROOT}" ]; then
    echo "SL3A_DATASET_ROOT not set or is empty"
    exit 255
fi

if [ -f "${SL3A_DATASET_ROOT}/.marker.dataset.shapenet.completed" ]; then
    echo "Dataset already prepared"
    exit 0
fi

SL3A_ENV_NAME="${SL3A_ENV_NAME:-sl3a}"

source "${SL3A_CONDA_ROOT}/miniconda3/bin/activate" "${SL3A_ENV_NAME}"

download_official() {
    mkdir -p "${SL3A_DATASET_ROOT}"
    cd "${SL3A_DATASET_ROOT}"
    wget --timeout=10 --tries=3 --no-check-certificate https://shapenet.cs.stanford.edu/shapenet/obj-zip/ShapeNetSem.v0/metadata.csv || true
    wget --timeout=10 --tries=3 --no-check-certificate https://shapenet.cs.stanford.edu/shapenet/obj-zip/ShapeNetSem.v0/models-OBJ.zip || true
    if [ -f "${SL3A_DATASET_ROOT}/metadata.csv" -a -f "${SL3A_DATASET_ROOT}/models-OBJ.zip" ]; then
        unzip models-OBJ.zip || return 1
        touch "${SL3A_DATASET_ROOT}/.marker.dataset.shapenet.completed"
    fi
}

download_fallback() {
    rm -rf "${SL3A_DATASET_ROOT}"
    mkdir -p "${SL3A_DATASET_ROOT}"
    cd "${SL3A_DATASET_ROOT}"
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
    rm -rf "${SL3A_DATASET_ROOT}/ShapeNetSem-Dataset_of_3D_Shapes"
    touch "${SL3A_DATASET_ROOT}/.marker.dataset.shapenet.completed"
}

download_official

if [ ! -f "${SL3A_DATASET_ROOT}/.marker.dataset.shapenet.completed" ]; then
    if [ ! -z "${DAGSHUB_USER}" -a ! -z "${DAGSHUB_TOKEN}" ]; then
        download_fallback
    else
        echo "Looks like the official ShapeNet server is down. A fallback option requires a www.dagshub.com account."
        echo "Pass the account information in environment variables DAGSHUB_USER and DAGSHUB_TOKEN."
        echo "See https://dagshub.com/user/settings/tokens"
    fi
fi

if [ ! -f "${SL3A_DATASET_ROOT}/.marker.dataset.shapenet.completed" ]; then
    echo "Dataset installation failed"
    exit 255
fi
