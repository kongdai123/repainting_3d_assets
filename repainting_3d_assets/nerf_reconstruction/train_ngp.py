#!/usr/bin/env python3

# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
import shutil
import subprocess
import time
from contextlib import contextmanager

import PIL.Image as Image
import commentjson as json
import numpy as np
import pyngp as ngp  # noqa
from tqdm import tqdm

from repainting_3d_assets.nerf_reconstruction.common import write_image
from repainting_3d_assets.nerf_reconstruction.utils import (
    create_dir,
    import_config_key,
    obj,
)


@contextmanager
def suppress_output_fd():
    if "DEBUG" in os.environ:
        yield
        return
    old_stdout_fd = os.dup(1)
    old_stderr_fd = os.dup(2)
    with open(os.devnull, "w") as fnull:
        devnull_fd = fnull.fileno()
        os.dup2(devnull_fd, 1)
        os.dup2(devnull_fd, 2)
        try:
            yield
        finally:
            os.dup2(old_stdout_fd, 1)
            os.dup2(old_stderr_fd, 2)
            os.close(old_stdout_fd)
            os.close(old_stderr_fd)


def sync_config(nerf_config, mesh_config):
    save_dir = create_dir(mesh_config["save_dir"])
    dataset_dir = create_dir(f"{save_dir}/dataset")
    video_save_name = import_config_key(mesh_config, "save_name", "model")

    nerf_config["scene"] = f"{save_dir}"
    nerf_config["video_output"] = f"{save_dir}/{video_save_name}.mp4".replace(" ", "\ ")
    nerf_config["test_transforms"] = f"{dataset_dir}/train_transforms.json"
    nerf_config["save_snapshot"] = f"{save_dir}/model.msgpack"
    nerf_config["bg_color"] = import_config_key(mesh_config, "bg_color", 0.5)
    nerf_args = obj(nerf_config)

    return nerf_args


def train_nerf(args):
    with suppress_output_fd():
        mode = ngp.TestbedMode.Nerf
        configs_dir = os.path.join(args.path_instantngp, "configs", "nerf")
        base_network = os.path.join(configs_dir, "base.json")
        network = args.network if args.network else base_network
        if not os.path.isabs(network):
            network = os.path.join(configs_dir, network)
        testbed = ngp.Testbed(mode)
        testbed.nerf.sharpen = 0.0
        testbed.exposure = 0.0
        testbed.nerf.training.depth_supervision_lambda = 1.0
        testbed.nerf.training.random_bg_color = True
        if args.scene:
            scene = args.scene
            testbed.load_training_data(scene)
        testbed.reload_network_from_file(network)
        testbed.shall_train = True
        testbed.nerf.render_with_lens_distortion = True

    old_training_step = 0
    n_steps = args.n_steps

    # If we loaded a snapshot, didn't specify a number of steps, _and_ didn't open a GUI,
    # don't train by default and instead assume that the goal is to render screenshots,
    # compute PSNR, or render a video.
    if n_steps < 0:
        n_steps = 35000

    tqdm_last_update = 0
    if n_steps > 0:
        with tqdm(desc="Reconciling views", total=n_steps, unit="step") as t:
            while testbed.frame():
                if testbed.want_repl():
                    raise RuntimeError("REPL not supported")

                # What will happen when training is done?
                if testbed.training_step >= n_steps:
                    break

                # Update progress bar
                if testbed.training_step < old_training_step or old_training_step == 0:
                    old_training_step = 0
                    t.reset()

                now = time.monotonic()
                if now - tqdm_last_update > 0.1:
                    t.update(testbed.training_step - old_training_step)
                    t.set_postfix(loss=testbed.loss)
                    old_training_step = testbed.training_step
                    tqdm_last_update = now

    if args.save_snapshot:
        testbed.save_snapshot(args.save_snapshot, False)

    if args.test_transforms:
        with open(args.test_transforms) as f:
            test_transforms = json.load(f)

        spp = 8

        testbed.background_color = [0.0, 0.0, 0.0, 1.0]
        testbed.snap_to_pixel_centers = True
        testbed.nerf.rendering_min_transmittance = 1e-4
        testbed.fov_axis = 0
        testbed.fov = test_transforms["camera_angle_x"] * 180 / np.pi
        testbed.shall_train = False

        for i, frame in enumerate(test_transforms["frames"]):
            testbed.set_nerf_camera_matrix(np.matrix(frame["transform_matrix"])[:-1, :])
            image = testbed.render(
                test_transforms["h"], test_transforms["w"], spp, True
            )
            file_dir = frame["file_dir"]
            save_dir_img = f"{args.scene}/{file_dir}"
            os.makedirs(save_dir_img, exist_ok=True)

            img_path = f"{save_dir_img}/out_train.png"
            write_image(img_path, image)

    if args.video_camera_path and args.record_video:
        with open(args.video_camera_path) as f:
            vid_transforms = json.load(f)

        testbed.background_color = [args.bg_color, args.bg_color, args.bg_color, 1.0]
        testbed.snap_to_pixel_centers = False

        path_video_tmp = f"{args.scene}/video_tmp"
        shutil.rmtree(path_video_tmp, ignore_errors=True)
        os.makedirs(path_video_tmp)
        with tqdm(
            list(enumerate(vid_transforms["frames"])),
            unit="images",
            desc=f"Rendering video frames",
        ) as t:
            for i, frame in t:
                testbed.set_nerf_camera_matrix(
                    np.matrix(frame["transform_matrix"])[:-1, :]
                )
                image = testbed.render(
                    args.video_resolution, args.video_resolution, args.video_spp, True
                )
                img_path = f"{path_video_tmp}/{i:04d}.png"
                write_image(img_path, image)

                mask = np.array(Image.open(f"{args.scene}/sil/{i:04d}.png"))
                image = np.array(Image.open(img_path))

                bg_img = int(args.bg_color * 255) * np.ones_like(image)
                image = np.where(mask[:, :, np.newaxis] == 0, bg_img, image)
                image = Image.fromarray(image[:, :, :3])
                image.save(f"{path_video_tmp}/{i:04d}.jpg")
                if i in [0, 45, 90, 135, 180, 225, 270, 315]:
                    spin_views_dir = create_dir(f"{args.scene}/spin_views")
                    image = np.array(image.convert("RGBA"))
                    image[:, :, 3] = mask
                    image = Image.fromarray(image)
                    image.save(f"{spin_views_dir}/deg{i:03d}.png")

        cmd = f"ffmpeg -y -framerate {args.video_fps} -i {path_video_tmp}/%04d.jpg -c:v mpeg4 -q:v 2 -pix_fmt yuv420p {args.video_output}"
        if "DEBUG" in os.environ:
            print(subprocess.getoutput("which ffmpeg"))
            print(cmd)
        with suppress_output_fd():
            os.system(cmd)
        shutil.rmtree(path_video_tmp, ignore_errors=True)
        if not os.path.exists(args.video_output):
            print("Video generation failed")
