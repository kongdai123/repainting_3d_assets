#!/usr/bin/env python3

# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import argparse
import os
import subprocess

import commentjson as json

import numpy as np

import shutil
import time

from .common import *
from .scenes import *

from tqdm import tqdm

import pyngp as ngp # noqa
import json 

from .nsvf2nerf import sharpness
# from utils import obj

import PIL.Image as Image
from .utils import create_dir,import_config_key, obj

def sync_config(nerf_config, mesh_config):
    save_dir = create_dir(mesh_config["save_dir"])
    dataset_dir = create_dir(f'{save_dir}/dataset')
    save_name = import_config_key(mesh_config, "save_name", "")

    nerf_config["scene"] = f"{save_dir}"
    nerf_config["video_output"] = f"{save_dir}/{save_name}.mp4".replace(" ", "\ " )
    nerf_config["test_transforms"] = f"{dataset_dir}/train_transforms.json"
    nerf_config["save_snapshot"] = f"{save_dir}/model.msgpack"
    nerf_config['bg_color'] = import_config_key(mesh_config, "bg_color", 0.5)
    nerf_args = obj(nerf_config)
    
    return nerf_args

def train_nerf(args):
	mode = ngp.TestbedMode.Nerf
	configs_dir = os.path.join(ROOT_DIR, "configs", "nerf")
	scenes = scenes_nerf
	base_network = os.path.join(configs_dir, "base.json")
	if args.scene in scenes:
		network = scenes[args.scene]["network"] if "network" in scenes[args.scene] else "base"
		base_network = os.path.join(configs_dir, network+".json")
	network = args.network if args.network else base_network
	if not os.path.isabs(network):
		network = os.path.join(configs_dir, network)
	print("running_network")
	print(network)
	testbed = ngp.Testbed(mode)
	testbed.nerf.sharpen = 0.0
	testbed.exposure = 0.0
	testbed.nerf.training.depth_supervision_lambda = 1.0
	testbed.nerf.training.random_bg_color = True
	if args.scene:
		scene = args.scene
		if not os.path.exists(args.scene) and args.scene in scenes:
			scene = os.path.join(scenes[args.scene]["data_dir"], scenes[args.scene]["dataset"])
		testbed.load_training_data(scene)
	testbed.reload_network_from_file(network)
	testbed.shall_train = True
    
	testbed.nerf.render_with_lens_distortion = True

	network_stem = os.path.splitext(os.path.basename(network))[0]

	old_training_step = 0
	n_steps = args.n_steps

	# If we loaded a snapshot, didn't specify a number of steps, _and_ didn't open a GUI,
	# don't train by default and instead assume that the goal is to render screenshots,
	# compute PSNR, or render a video.
	if n_steps < 0:
		n_steps = 35000

	tqdm_last_update = 0
	if n_steps > 0:
		with tqdm(desc="Training", total=n_steps, unit="step") as t:
			while testbed.frame():
				if testbed.want_repl():
					repl(testbed)
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
		print("Saving snapshot ", args.save_snapshot)
		testbed.save_snapshot(args.save_snapshot, False)

	if args.test_transforms:
		print("Evaluating test transforms from ", args.test_transforms)
		with open(args.test_transforms) as f:
			test_transforms = json.load(f)
		data_dir=os.path.dirname(args.test_transforms)

		# Evaluate metrics on black background
		testbed.background_color = [0.0, 0.0, 0.0, 1.0]

		# Prior nerf papers don't typically do multi-sample anti aliasing.
		# So snap all pixels to the pixel centers.
		testbed.snap_to_pixel_centers = True
		spp = 8

		testbed.nerf.rendering_min_transmittance = 1e-4

		testbed.fov_axis = 0
		testbed.fov = test_transforms["camera_angle_x"] * 180 / np.pi
		testbed.shall_train = False
		
		with tqdm(list(enumerate(test_transforms["frames"])), unit="images", desc=f"Rendering test frame") as t:
			for i, frame in t:
				testbed.set_nerf_camera_matrix(np.matrix(frame["transform_matrix"])[:-1,:])
				image = testbed.render(test_transforms["h"], test_transforms["w"], spp, True)
				file_dir = frame["file_dir"]
				save_dir_img  =f"{args.scene}/{file_dir}"
				os.makedirs(save_dir_img, exist_ok=True)
				
				img_path = f"{save_dir_img}/out_train.png"
				write_image(img_path, image)
                

	if args.video_camera_path and args.record_video:
		with open(args.video_camera_path) as f:
			vid_transforms = json.load(f)
# 		testbed.load_camera_path(args.video_camera_path)
# 		testbed.loop_animation = args.video_loop_animation

		testbed.background_color = [args.bg_color, args.bg_color, args.bg_color, 1.0]
		testbed.snap_to_pixel_centers = False

# 		resolution = [512, 512]
# 		n_frames = args.video_n_seconds * args.video_fps

		path_video_tmp = f"{args.scene}/video_tmp"
		shutil.rmtree(path_video_tmp, ignore_errors=True)
		os.makedirs(path_video_tmp)
		with tqdm(list(enumerate(vid_transforms["frames"])), unit="images", desc=f"Rendering test frame") as t:
			for i, frame in t:
				testbed.set_nerf_camera_matrix(np.matrix(frame["transform_matrix"])[:-1,:])
				image = testbed.render(args.video_resolution, args.video_resolution, args.video_spp, True)
				img_path = f"{path_video_tmp}/{i:04d}.png"
				write_image(img_path, image)
                
				mask = np.array(Image.open(f"{args.scene}/sil/{i:04d}.png"))
				image = np.array(Image.open(img_path))

				bg_img = int(args.bg_color * 255) * np.ones_like(image)
				image = np.where(mask[:,:, np.newaxis] == 0, bg_img, image)
				image = Image.fromarray(image[:,:,:3])
				image.save(f"{path_video_tmp}/{i:04d}.jpg")
				if i in [0, 45, 90, 135, 180, 225, 270, 315]:
					spin_views_dir = create_dir(f"{args.scene}/spin_views")
					image = np.asarray(image.convert('RGBA'))
					image[:,:, 3] = mask
					image = Image.fromarray(image)
					image.save(f"{spin_views_dir}/deg{i:03d}.png")

                

		cmd = f"ffmpeg -y -framerate {args.video_fps} -i {path_video_tmp}/%04d.jpg -c:v mpeg4 -q:v 2 -pix_fmt yuv420p {args.video_output}"
		print(subprocess.getoutput("which ffmpeg"))
		print(cmd)
		os.system(cmd)
		shutil.rmtree(path_video_tmp, ignore_errors=True)

		# place a marker of completion
		path_marker_completed = f"{args.scene}/.marker.completed"
		os.system(f'touch "{path_marker_completed}"')

