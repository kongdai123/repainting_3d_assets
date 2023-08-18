import os.path
import subprocess
import tempfile
import uuid

import numpy as np
import pyngp as ngp  # noqa
import trimesh
from tqdm import tqdm

from sl3a.view_generation.pt3d_mesh_io import load_obj
from sl3a.view_generation.utils3D import position_verts


def remesh_subdivide_isotropic_planar(path_input, path_output, resolution):
    temp_dir = tempfile.gettempdir()
    path_input_off = os.path.join(temp_dir, str(uuid.uuid4()) + ".off")
    path_output_off = os.path.join(temp_dir, str(uuid.uuid4()) + ".off")

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
        ],
    )

    if not os.path.exists(path_output_off):
        raise RuntimeError("Remeshing failed")

    mesh = trimesh.load_mesh(path_output_off)
    mesh.export(path_output)


def nerf_to_mesh(
    mesh_config,
    snapshot,
    swap_face=False,
    resolution=384,
    num_samples=50,
    sigma=0.0005,
):
    mode = ngp.TestbedMode.Nerf
    testbed = ngp.Testbed(mode)
    testbed.load_snapshot(snapshot)

    trans_mat = mesh_config["trans_mat"]
    mesh_path = mesh_config["obj"]
    save_dir = mesh_config["save_dir"]

    # load mesh and align with ngp
    verts, faces, _ = load_obj(
        mesh_path,
        load_textures=False,
        create_texture_atlas=False,
        swap_face=swap_face,
    )
    faces = faces.verts_idx
    verts = position_verts(verts, trans_mat, swap_face=swap_face)

    trimesh.Trimesh(vertices=verts, faces=faces).export(f"{save_dir}/input.ply")
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
