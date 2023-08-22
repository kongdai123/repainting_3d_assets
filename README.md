# Breathing New Life into 3D Assets with Generative Repainting

This repository implements a method from our BMVC'23 paper "Breathing New Life into 3D Assets with Generative Repainting".

# Quick Start

Install a [Docker](https://www.docker.com/)-compatible<sup>*</sup> runtime and use the following command to repaint your 3D asset. 
The asset is painted according to the text prompt specified as the last argument. 
For example:

```shell
sh scripts/docker_run_userdata.sh assets/sample.obj out/ "red dragon"
```

The result can be found in the `out/` directory. It contains:

- `model.mp4`, a 360-degree spin view video of the result;
- `model.msgpack`, an NeRF file with the output in Instant NGP format;
- `model.obj`, a standard 3D model that has the geometry of the input 3D model and painting of the NeRF output.

<sup>*</sup> Docker, Singularity, Podman, etc.

# Development

Run `sh scripts/setup_all_for_userdata.sh <WORK>` to set up a new working directory pointed to by `<WORK>`. 
This requires ~32 GB of disk space and installs a custom python runtime with [Instant NGP](https://github.com/NVlabs/instant-ngp).

Once the setup completes, use `sh scripts/conda_run_userdata.sh <WORK> <PATH_ASSET> <PATH_OUTPUT_DIR> <PROMPT>` to process your custom 3D asset.

If this way of building fails, resort to using the docker image, either as described in the [Quick Start](#quick-start), or build one from scratch by running `sh scripts/docker_build.sh`. 

### ShapeNetSem

Run `sh scripts/setup_all_for_shapenet.sh <WORK>` to set up a new working directory pointed to by `<WORK>`. 
This requires ~100 GB of disk space and installs a custom python runtime, compiles [Instant NGP](https://github.com/NVlabs/instant-ngp), and downloads the [ShapeNetSem](https://shapenet.org/) dataset.

Once the setup completes, use `sh scripts/conda_run_shapenet.sh <WORK> <ID_1> ... <ID_N>` to process models from the ShapeNetSem dataset.
