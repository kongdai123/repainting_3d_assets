FROM nvcr.io/nvidia/pytorch:21.05-py3

ARG UNAME=user

RUN apt-get -y update --fix-missing
RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y \
    libgl1-mesa-glx

RUN groupadd ${UNAME}-group
RUN useradd -m -c ${UNAME} -G root -s /bin/bash ${UNAME}

ENV SL3A_ROOT=/sl3a
RUN mkdir -p ${SL3A_ROOT}
RUN chown -R ${UNAME}:${UNAME}-group ${SL3A_ROOT}
RUN chmod -R 777 ${SL3A_ROOT}

USER ${UNAME}

WORKDIR ${SL3A_ROOT}

ENV SL3A_CONDA_ROOT=${SL3A_ROOT}/conda
ENV SL3A_DATASET_ROOT=${SL3A_ROOT}/dataset
ENV SL3A_INSTANTNGP_ROOT=${SL3A_ROOT}/instantngp

ENV TRANSFORMERS_CACHE=${SL3A_ROOT}/hfcache
ENV HF_DATASETS_CACHE=${SL3A_ROOT}/hfcache
ENV HF_HOME=${SL3A_ROOT}/hfcache

COPY . ${SL3A_ROOT}/code

RUN bash ${SL3A_ROOT}/code/scripts/setup_conda_bin.sh ${SL3A_ROOT}
RUN bash ${SL3A_ROOT}/code/scripts/setup_conda_env.sh ${SL3A_ROOT}
RUN bash ${SL3A_ROOT}/code/scripts/setup_instantngp.sh ${SL3A_ROOT}
