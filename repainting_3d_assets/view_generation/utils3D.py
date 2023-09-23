import numpy as np
import PIL.Image as Image
import torch
from pytorch3d.renderer import look_at_view_transform
import json

from repainting_3d_assets.view_generation.utils import sharpness, listify_matrix


def position_verts(verts, trans_mat, swap_face=True, shape_scale=1.2):
    if trans_mat is not None:
        verts = torch.matmul(verts, trans_mat)
    if swap_face:
        verts[:, 0] = verts[:, 0] * (-1)

    verts = verts - (verts.max(0).values + verts.min(0).values) * 0.5

    verts = verts / torch.sqrt(torch.sum(verts * verts, axis=1)).max()
    verts = verts * shape_scale

    return verts


def swap_faces(faces):
    faces_res = faces.clone()
    tmp = faces_res[:, 1].clone()
    faces_res[:, 1] = faces_res[:, 2]
    faces_res[:, 2] = tmp
    return faces_res


def init_ngp_config(config):
    return {
        "camera_angle_x": config["fov"] * np.pi / 180,
        "camera_angle_y": config["fov"] * np.pi / 180,
        "fl_x": 256 / np.tan(config["fov"] / 2 * np.pi / 180),
        "fl_y": 256 / np.tan(config["fov"] / 2 * np.pi / 180),
        "k1": 0,
        "k2": 0,
        "p1": 0,
        "p2": 0,
        "cx": 256,
        "cy": 256,
        "w": 512,
        "h": 512,
        "aabb_scale": 1,
        "enable_depth_loading": True,
        "integer_depth_scale": config["zfar"] / 65535,
        "z_near": config["znear"],
        "z_far": config["zfar"],
        "frames": [],
    }


def convert_pt_NGP_transform(elev_angles, azim_angles, r=3.5):
    R_save, T_save = look_at_view_transform(
        r, elev_angles.flatten(), -azim_angles.flatten() + 180
    )

    views = R_save.shape[0]
    matrix_world = torch.zeros((views, 4, 4), device=R_save.device)
    matrix_axis_transform = torch.tensor(
        [[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], device=R_save.device
    ).to(torch.float)

    for i in range(views):
        matrix_world[i, :3, :3] = R_save[i].inverse()
        matrix_world[i, :3, 3] = torch.matmul((R_save[i].inverse()), T_save[i])
        matrix_world[i, 3, 3] = 1
        matrix_world[i] = torch.matmul(matrix_axis_transform, matrix_world[i])

    return matrix_world


def write_outframe(next_angle, ipt_save_dir, transforms_config_out, save_dir):
    outframe = {
        "file_dir": f"./dataset/{next_angle}/",
        "file_path": f"./dataset/{next_angle}/out_alpha.png",
        "depth_path": f"./dataset/{next_angle}/depth/out.png",
        "sharpness": sharpness(f"{ipt_save_dir}/out.png"),
        "transform_matrix": listify_matrix(
            convert_pt_NGP_transform(torch.tensor([0]), torch.tensor([next_angle]))
        )[0],
    }

    transforms_config_out["frames"].append(outframe)
    with open(f"{save_dir}/transforms.json", "w") as out_file:
        json.dump(transforms_config_out, out_file, indent=4)
    return transforms_config_out


def save_diffusion_image(image, ipt_save_dir, depth_path):
    image.save(f"{ipt_save_dir}/out.png")
    image = np.array(image.convert("RGBA"))

    if np.all(image[:, :, :3] == np.zeros_like(image[:, :, :3])):
        image = np.random.randint(0, high=255, size=image.shape).astype(np.uint8)
        image = Image.fromarray(image.astype("uint8"))
        image.save(f"{ipt_save_dir}/out_alpha.png")
        image.save(f"{ipt_save_dir}/out.png")
    else:
        d = np.load(depth_path)
        image[:, :, 3] = (d != d.max()).astype("uint8") * 255
        image = Image.fromarray(image)
        image.save(f"{ipt_save_dir}/out_alpha.png")
