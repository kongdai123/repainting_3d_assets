import os
import shutil

import torch

from diff_view_gen.depth_supervised_inpainting_pipeline import (
    StableDiffusionDepth2ImgInpaintingPipeline,
)
from diff_view_gen.inpaint import (
    initialize_meshes,
    inpaint_first_view,
    inpaint_facade,
    write_train_transforms,
    inpaint_bidirectional,
)
from diff_view_gen.reproj import render_silhouette
from diff_view_gen.utils import import_config_key
from nerf_recon.train_ngp import sync_config, train_nerf


def remove_artifacts(save_dir):
    os.remove(f"{save_dir}/transforms.json")
    shutil.rmtree(f"{save_dir}/dataset", ignore_errors=True)
    shutil.rmtree(f"{save_dir}/vis", ignore_errors=True)
    shutil.rmtree(f"{save_dir}/sil", ignore_errors=True)


def paint(mesh_config, inpaint_config, nerf_config):
    device = "cuda" if torch.cuda.is_available() else "cpu"

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

    remove_artifacts(mesh_config["save_dir"])
