# Second Life for 3D Assets 

This repository implements a method from the paper "Second Life for 3D Assets".

# Quick Start

Use the following command to process your custom 3D asset, or use the one from the `assets` folder:

```shell
sh scripts/docker_run_one.sh assets/sample.obj
```

# Development

Run `sh scripts/setup_all.sh <WORK>` to set up a new working directory pointed to by `<WORK>`. 
This requires ~100 GB of disk space and installs a custom python runtime, compiles [Instant NGP](https://github.com/NVlabs/instant-ngp), and downloads the [ShapeNetSem](https://shapenet.org/) dataset.

Once the setup completes, use

- `sh scripts/conda_run_shapenet.sh <WORK> <ID_1> ... <ID_N>` to process several model ids from the ShapeNetSem dataset;
- `sh scripts/conda_run_one.sh <WORK> <PATH_ASSET>` to process your custom 3D asset.

If this way of building fails, resort to using the docker image, either as described in the [Quick Start](#quick-start), or build one from scratch by running `sh scripts/docker_build.sh`. 
