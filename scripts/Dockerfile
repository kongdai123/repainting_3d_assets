FROM nvcr.io/nvidia/pytorch:21.05-py3

ARG UNAME=user

RUN apt-get -y update --fix-missing
RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y \
    libgl1-mesa-glx

RUN groupadd ${UNAME}-group
RUN useradd -m -c ${UNAME} -G root -s /bin/bash ${UNAME}

ENV REPAINTING3D_ROOT=/repainting_3d_assets
RUN mkdir -p ${REPAINTING3D_ROOT}
RUN chown -R ${UNAME}:${UNAME}-group ${REPAINTING3D_ROOT}
RUN chmod -R 777 ${REPAINTING3D_ROOT}

USER ${UNAME}

WORKDIR ${REPAINTING3D_ROOT}

ENV REPAINTING3D_CONDA_ROOT=${REPAINTING3D_ROOT}/conda
ENV REPAINTING3D_DATASET_ROOT=${REPAINTING3D_ROOT}/dataset
ENV REPAINTING3D_INSTANTNGP_ROOT=${REPAINTING3D_ROOT}/instantngp

ENV TRANSFORMERS_CACHE=${REPAINTING3D_ROOT}/hfcache
ENV HF_DATASETS_CACHE=${REPAINTING3D_ROOT}/hfcache
ENV HF_HOME=${REPAINTING3D_ROOT}/hfcache

COPY . ${REPAINTING3D_ROOT}/code

RUN bash ${REPAINTING3D_ROOT}/code/scripts/setup_conda_bin.sh ${REPAINTING3D_ROOT}
RUN bash ${REPAINTING3D_ROOT}/code/scripts/setup_conda_env.sh ${REPAINTING3D_ROOT}
RUN bash ${REPAINTING3D_ROOT}/code/scripts/setup_instantngp.sh ${REPAINTING3D_ROOT}

COPY docker_build_entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
