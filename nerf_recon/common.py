#!/usr/bin/env python3

# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import code
import os
import struct
import sys

import PIL.Image as Image
import numpy as np
import torch


def find_instantngp_binaries(path_instantngp, verbose=True):
    if not os.path.isdir(path_instantngp):
        raise RuntimeError(f'{path_instantngp=} is not a directory')

    entries = os.listdir(path_instantngp)

    build_dirs = {
        int(e[len('build_sm'):]): os.path.join(path_instantngp, e)
        for e in entries
        if os.path.isdir(os.path.join(path_instantngp, e)) and e.startswith("build_sm")
    }

    if len(build_dirs) == 0:
        raise RuntimeError(f'{path_instantngp=} does not contain any build directories')

    CUDA_DEFAULT_DEVICE_COMPUTE_CAPABILITY = int(''.join([str(a) for a in torch.cuda.get_device_capability()]))

    resolved_version = None
    for k in sorted(build_dirs.keys(), reverse=True):
        if k <= CUDA_DEFAULT_DEVICE_COMPUTE_CAPABILITY:
            resolved_version = k
            break
    if resolved_version is None:
        raise RuntimeError(
            f"The detected CUDA architecture {CUDA_DEFAULT_DEVICE_COMPUTE_CAPABILITY} cannot be treated by any of the "
            f"available builds: {sorted(build_dirs.keys())}"
        )

    if verbose:
        print(
            f'Found instant-ngp build {resolved_version} for the detected CUDA SM '
            f'{CUDA_DEFAULT_DEVICE_COMPUTE_CAPABILITY}'
        )

    out = build_dirs[resolved_version]
    return out


def add_instantngp_sys_path(path_instantngp, verbose=True):
    path = find_instantngp_binaries(path_instantngp, verbose=verbose)
    sys.path.append(path)


def repl(testbed):
    print("-------------------\npress Ctrl-Z to return to gui\n---------------------------")
    code.InteractiveConsole(locals=locals()).interact()
    print("------- returning to gui...")


def write_image_PIL(img_file, img, quality):
    img = (np.clip(img, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    img_PIL = Image.fromarray(img)
    kwargs = {}
    if os.path.splitext(img_file)[1].lower() in [".jpg", ".jpeg"]:
        if img.ndim >= 3 and img.shape[2] > 3:
            img = img[:, :, :3]
        kwargs["quality"] = quality
        kwargs["subsampling"] = 0
    img_PIL.save(img_file, **kwargs)

def linear_to_srgb(img):
    limit = 0.0031308
    return np.where(img > limit, 1.055 * (img ** (1.0 / 2.4)) - 0.055, 12.92 * img)


def write_image(file, img, quality=95):
    if os.path.splitext(file)[1] == ".bin":
        if img.shape[2] < 4:
            img = np.dstack((img, np.ones([img.shape[0], img.shape[1], 4 - img.shape[2]])))
        with open(file, "wb") as f:
            f.write(struct.pack("ii", img.shape[0], img.shape[1]))
            f.write(img.astype(np.float16).tobytes())
    else:
        if img.shape[2] == 4:
            img = np.copy(img)
            # Unmultiply alpha
            img[..., 0:3] = np.divide(
                img[..., 0:3], img[..., 3:4], out=np.zeros_like(img[..., 0:3]), where=img[..., 3:4] != 0
            )
            img[..., 0:3] = linear_to_srgb(img[..., 0:3])
        else:
            img = linear_to_srgb(img)
        write_image_PIL(file, img, quality)
