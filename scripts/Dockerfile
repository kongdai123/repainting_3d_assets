FROM nvidia/cuda:11.8.0-devel-ubuntu20.04

ENV NGP_EXTRA_CMAKE_ARGS="-DCUDA_VERSION=11.8"

ARG DEBUG

RUN apt-get -y update --fix-missing && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        gosu \
        gcc \
        g++ \
        git \
        cmake \
        wget \
        libgl1-mesa-glx \
        libglib2.0-0 \
        unzip && \
    apt-get clean

ENV ROOT_PROJECT=/repainting_3d_assets

ENV ROOT_CODE=${ROOT_PROJECT}/code
ENV TRANSFORMERS_CACHE=${ROOT_PROJECT}/hfcache
ENV HF_DATASETS_CACHE=${ROOT_PROJECT}/hfcache
ENV HF_HOME=${ROOT_PROJECT}/hfcache

WORKDIR ${ROOT_CODE}
COPY . .

RUN mkdir -p ${HF_HOME} && \
    CLEANUP=1 bash scripts/setup.sh "${ROOT_PROJECT}"

COPY scripts/docker_build_entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
