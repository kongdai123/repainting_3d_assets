import json
import os
import shutil
from pathlib import Path

import torch

from repainting_3d_assets.view_generation.depth_supervised_inpainting_pipeline import (
    StableDiffusionDepth2ImgInpaintingPipeline,
)
from repainting_3d_assets.view_generation.inpaint import (
    initialize_meshes,
    inpaint_first_view,
    inpaint_facade,
    write_train_transforms,
    inpaint_bidirectional,
)
from repainting_3d_assets.view_generation.nerf_to_mesh import nerf_to_mesh
from repainting_3d_assets.view_generation.reproj import render_silhouette
from repainting_3d_assets.view_generation.utils import import_config_key
from repainting_3d_assets.nerf_reconstruction.train_ngp import sync_config, train_nerf


def dump_configs(save_dir, mesh_config, inpaint_config, nerf_config):
    def dump_one(name, vals):
        with open(f"{save_dir}/{name}", "w") as fp:
            json.dump(vals, fp, indent=4)

    dump_one("config_mesh.log", mesh_config)
    dump_one("config_inpaint.log", inpaint_config)
    dump_one("config_nerf.log", nerf_config)


def remove_intermediates(save_dir):
    if "DEBUG" in os.environ:
        return
    Path(f"{save_dir}/transforms.json").unlink(missing_ok=True)
    shutil.rmtree(f"{save_dir}/dataset", ignore_errors=True)
    shutil.rmtree(f"{save_dir}/vis", ignore_errors=True)
    shutil.rmtree(f"{save_dir}/sil", ignore_errors=True)


def paint(mesh_config, inpaint_config, nerf_config):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    save_dir = mesh_config["save_dir"]

    dump_configs(save_dir, mesh_config, inpaint_config, nerf_config)
    nerf_args = sync_config(nerf_config, mesh_config)

    meshes = initialize_meshes(inpaint_config, mesh_config, device)

    pipe = StableDiffusionDepth2ImgInpaintingPipeline.from_pretrained(
        "stabilityai/stable-diffusion-2-depth",
        torch_dtype=torch.float16,
    ).to("cuda")

    rng_randn = torch.Generator(device=device)
    rng_randn.manual_seed(mesh_config["seed_latents"])
    latents = torch.randn(
        (1, 4, 64, 64), generator=rng_randn, dtype=torch.float16, device=device
    )

    transforms_config_out, bg_image = inpaint_first_view(
        meshes, pipe, latents, inpaint_config, mesh_config, device
    )

    view_1, view_2, transforms_config_out = inpaint_facade(
        inpaint_config,
        mesh_config,
        pipe,
        latents,
        meshes,
        bg_image,
        transforms_config_out,
        device,
    )

    angle_inc = import_config_key(inpaint_config, "angle_inc", 40)

    backwards = False

    while True:
        backwards = not backwards
        if backwards:
            view_synth = view_2 - angle_inc
        else:
            view_synth = view_1 + angle_inc
        if view_synth == view_2 or view_synth == view_1:
            break

        write_train_transforms(
            view_1, view_2, view_synth, mesh_config, transforms_config_out, device
        )

        nerf_args.record_video = False

        train_nerf(nerf_args)

        view_1, view_2, view_synth, transforms_config_out = inpaint_bidirectional(
            view_1,
            view_2,
            view_synth,
            inpaint_config,
            mesh_config,
            pipe,
            latents,
            meshes,
            transforms_config_out,
            bg_image,
            device,
        )

        if backwards:
            view_2 = view_synth
        else:
            view_1 = view_synth

    for i in range(360):
        render_silhouette(
            i,
            meshes,
            inpaint_config,
            mesh_config,
            size=nerf_args.video_resolution,
            device=device,
        )

    nerf_args.record_video = True
    train_nerf(nerf_args)

    nerf_to_mesh(meshes, save_dir, path_nerf_weights=nerf_args.save_snapshot)

    remove_intermediates(save_dir)
