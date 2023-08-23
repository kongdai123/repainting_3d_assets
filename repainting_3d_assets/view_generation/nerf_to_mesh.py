import os
import subprocess
from pathlib import Path

import numpy as np
import pyngp as ngp  # noqa
import trimesh
from pytorch3d.io import save_ply
from tqdm import tqdm

from repainting_3d_assets.nerf_reconstruction.train_ngp import suppress_output_fd


def remove_intermediates(save_dir, resolution):
    if "DEBUG" in os.environ:
        return
    Path(f"{save_dir}/input.ply.off").unlink(missing_ok=True)
    Path(f"{save_dir}/input_{resolution}.ply.off").unlink(missing_ok=True)
    Path(f"{save_dir}/input_{resolution}.ply").unlink(missing_ok=True)


def remesh_subdivide_isotropic_planar(path_input, path_output, resolution):
    path_input_off = path_input + ".off"
    path_output_off = path_output + ".off"

    mesh = trimesh.load_mesh(path_input)
    if isinstance(mesh, trimesh.Scene):
        mesh = mesh.dump(concatenate=True)
    mesh.export(path_input_off)

    subprocess.call(
        [
            "remesh_isotropic_planar",
            path_input_off,
            path_output_off,
            "--resolution",
            str(resolution),
            "--verbose",
            str(1 if "DEBUG" in os.environ else 0),
        ],
    )

    if not os.path.exists(path_output_off):
        raise RuntimeError("Remeshing failed")

    mesh = trimesh.load_mesh(path_output_off)
    mesh.export(path_output)


def nerf_to_mesh(
    meshes,
    save_dir,
    path_nerf_weights,
    resolution=384,
    num_samples=50,
    sigma=0.0005,
):
    with suppress_output_fd():
        mode = ngp.TestbedMode.Nerf
        testbed = ngp.Testbed(mode)
        testbed.load_snapshot(path_nerf_weights)

    save_ply(f"{save_dir}/input.ply", meshes.verts_packed(), meshes.faces_packed())
    remesh_subdivide_isotropic_planar(
        f"{save_dir}/input.ply", f"{save_dir}/input_{resolution}.ply", resolution
    )

    mesh = trimesh.load_mesh(f"{save_dir}/input_{resolution}.ply")
    verts = mesh.vertices
    faces = mesh.faces
    padd_num = 128 - verts.shape[0] % 128

    # align with instant ngp frame of reference and pad
    verts_ngp = np.zeros((verts.shape[0] + padd_num, 3))
    verts_ngp[:, 0] = np.pad(verts[:, 2], (0, padd_num), "constant")
    verts_ngp[:, 1] = np.pad(verts[:, 1], (0, padd_num), "constant")
    verts_ngp[:, 2] = -np.pad(verts[:, 0], (0, padd_num), "constant")
    verts_ngp = verts_ngp * 0.33 + 0.5

    # sample from instantngp
    color_ngp = np.zeros_like(verts_ngp)
    for _ in tqdm(range(num_samples), desc="Exporting NeRF to mesh"):
        noise = sigma * np.random.randn(verts_ngp.shape[0], verts_ngp.shape[1])
        color_ngp = color_ngp + testbed.sample_mesh_colors(verts_ngp + noise)
    color_ngp = color_ngp / num_samples
    color_ngp = color_ngp[: verts.shape[0]]

    mesh_out = trimesh.Trimesh(vertices=verts, faces=faces, vertex_colors=color_ngp)
    mesh_out.export(f"{save_dir}/model.ply")
    mesh_out.export(f"{save_dir}/model.drc")

    remove_intermediates(save_dir, resolution)
