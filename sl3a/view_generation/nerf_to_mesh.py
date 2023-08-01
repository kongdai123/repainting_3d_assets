import warnings

import numpy as np
import pyngp as ngp  # noqa
import pyacvd
import pyvista
from pyacvd.clustering import _subdivide
from tqdm import tqdm

from sl3a.view_generation.pt3d_mesh_io import load_obj
from sl3a.view_generation.utils3D import position_verts
import torch


def nerf_to_mesh(
    mesh_config,
    snapshot,
    swap_face=False,
    target_size=500000,
    num_samples=50,
    sigma=0.0005,
):
    mode = ngp.TestbedMode.Nerf
    testbed = ngp.Testbed(mode)
    testbed.load_snapshot(snapshot)

    trans_mat = mesh_config["trans_mat"]
    mesh_path = mesh_config["obj"]
    save_dir = mesh_config["save_dir"]

    # remeshing
    mesh = pyvista.read(mesh_path)
    while mesh.points.shape[0] < target_size * 2:
        mesh = _subdivide(mesh, 1)

    clus = pyacvd.Clustering(mesh)
    _ = clus.cluster(target_size)
    remesh = clus.create_mesh()
    pl = pyvista.Plotter()
    _ = pl.add_mesh(remesh)
    path_remeshed_input = f"{save_dir}/remeshed_input.obj"
    pl.export_obj(path_remeshed_input)

    # load mesh and align with ngp
    verts, faces, _ = load_obj(
        path_remeshed_input,
        load_textures=False,
        create_texture_atlas=False,
        swap_face=swap_face,
    )
    faces = faces.verts_idx

    verts = position_verts(verts, trans_mat, swap_face=swap_face)

    verts_np = verts.cpu().numpy()
    padd_num = 128 - verts_np.shape[0] % 128

    # align with instant ngp frame of reference and pad
    verts_ngp = np.zeros((verts_np.shape[0] + padd_num, 3))
    verts_ngp[:, 0] = np.pad(verts_np[:, 2], (0, padd_num), "constant")
    verts_ngp[:, 1] = np.pad(verts_np[:, 1], (0, padd_num), "constant")
    verts_ngp[:, 2] = -np.pad(verts_np[:, 0], (0, padd_num), "constant")
    verts_ngp = verts_ngp * 0.33 + 0.5

    # sample from instantngp
    color_ngp = np.zeros_like(verts_ngp)
    for _ in tqdm(range(num_samples), desc="Exporting NeRF to mesh"):
        noise = sigma * np.random.randn(verts_ngp.shape[0], verts_ngp.shape[1])
        color_ngp = color_ngp + testbed.sample_mesh_colors(verts_ngp + noise)
    color_ngp = color_ngp / num_samples
    color_ngp = color_ngp[: verts_np.shape[0]]

    # save obj
    def _save_obj(f, verts, faces, colors, decimal_places: int = None) -> None:
        if len(verts) and (verts.dim() != 2 or verts.size(1) != 3):
            message = "'verts' should either be empty or of shape (num_verts, 3)."
            raise ValueError(message)

        if len(faces) and (faces.dim() != 2 or faces.size(1) != 3):
            message = "'faces' should either be empty or of shape (num_faces, 3)."
            raise ValueError(message)

        if not (len(verts) or len(faces)):
            warnings.warn("Empty 'verts' and 'faces' arguments provided")
            return

        verts, faces = verts.cpu(), faces.cpu()

        lines = ""

        if len(verts):
            if decimal_places is None:
                float_str = "%f"
            else:
                float_str = "%" + ".%df" % decimal_places

            V, D = verts.shape
            for i in range(V):
                vert = [float_str % verts[i, j] for j in range(D)]
                color = [float_str % colors[i, j] for j in range(D)]
                # lines += "v %s\n" % " ".join(vert)
                lines += "v %s " % " ".join(vert)
                lines += "%s\n" % " ".join(color)
        if torch.any(faces >= verts.shape[0]) or torch.any(faces < 0):
            warnings.warn("Faces have invalid indices")

        if len(faces):
            F, P = faces.shape
            for i in range(F):
                face = ["%d" % (faces[i, j] + 1) for j in range(P)]

                if i + 1 < F:
                    lines += "f %s\n" % " ".join(face)

                elif i + 1 == F:
                    # No newline at the end of the file.
                    lines += "f %s" % " ".join(face)

        f.write(lines)

    path_out = f"{save_dir}/model.obj"

    with open(path_out, "w") as f:
        _save_obj(f, verts, faces, color_ngp)
