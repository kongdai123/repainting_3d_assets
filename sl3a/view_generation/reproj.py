import os

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from pytorch3d.ops import interpolate_face_attributes
from pytorch3d.renderer import (
    look_at_view_transform,
    FoVPerspectiveCameras,
    MeshRasterizer,
)

from sl3a.view_generation.raster_settings import (
    raster_settings_mesh_ptcloud,
    raster_settings_mesh,
)
from sl3a.view_generation.utils import create_dir, import_config_key


def create_meshgrid(
    height,
    width,
    normalized_coordinates=True,
    device=torch.device("cpu"),
    dtype=torch.float32,
):
    xs = torch.linspace(0, width - 1, width, device=device, dtype=dtype)
    ys = torch.linspace(0, height - 1, height, device=device, dtype=dtype)
    if normalized_coordinates:
        xs = (xs / (width - 1) - 0.5) * 2
        ys = (ys / (height - 1) - 0.5) * 2
    base_grid = torch.stack(torch.meshgrid([xs, ys], indexing="ij"), dim=-1)  # WxHx2
    return base_grid.permute(1, 0, 2).unsqueeze(0)  # 1xHxWx2


def get_ray_directions(H, W, focal, center=None):
    """
    Get ray directions for all pixels in camera coordinate.
    Reference: https://www.scratchapixel.com/lessons/3d-basic-rendering/
               ray-tracing-generating-camera-rays/standard-coordinate-systems
    Inputs:
        H, W, focal: image height, width and focal length
    Outputs:
        directions: (H, W, 3), the direction of the rays in camera coordinate
    """
    grid = create_meshgrid(H, W, normalized_coordinates=False)[0] + 0.5

    i, j = grid.unbind(-1)
    # the direction here is without +0.5 pixel centering as calibration is not so accurate
    # see https://github.com/bmild/nerf/issues/24
    cent = center if center is not None else [W / 2, H / 2]
    directions = torch.stack(
        [(cent[0] - i) / focal[0], (cent[1] - j) / focal[1], torch.ones_like(i)], -1
    )  # (H, W, 3)

    return directions


def render_depth_map(angle, meshes, inpaint_config, mesh_config, device):
    Z_near, Z_far = inpaint_config["znear"], inpaint_config["zfar"]
    fov = inpaint_config["fov"]
    save_dir = create_dir(mesh_config["save_dir"])
    dataset_dir = create_dir(f"{save_dir}/dataset")

    ipt_depth_dir = create_dir(f"{dataset_dir}/{angle}/depth")
    depth_path = f"{ipt_depth_dir}/out_pt.npy"
    depth_path_ptc = f"{ipt_depth_dir}/out_ptc.npy"
    normal_path = f"{ipt_depth_dir}/out_norm.pt"
    normal_path_ptc = f"{ipt_depth_dir}/out_norm_ptc.pt"

    if not os.path.isfile(depth_path):
        elev_angles = torch.tensor([0]).to(device)
        azim_angles = torch.tensor([angle]).to(device)
        R, T = look_at_view_transform(
            (Z_near + Z_far) / 2, elev_angles.flatten(), (azim_angles + 180).flatten()
        )
        cameras = FoVPerspectiveCameras(device=device, R=R, T=T, fov=fov)
        rasterizer_mesh = MeshRasterizer(
            raster_settings=raster_settings_mesh_ptcloud, cameras=cameras
        )
        fragments = rasterizer_mesh(meshes)

        vertex_normals = meshes.verts_normals_packed()  # (V, 3)
        faces = meshes.faces_packed()
        faces_normals = vertex_normals[faces]

        pixel_normals = interpolate_face_attributes(
            fragments.pix_to_face, fragments.bary_coords, faces_normals
        )
        pixel_normals = F.normalize(pixel_normals, p=2, dim=-1, eps=1e-6)
        verts = meshes.verts_packed()
        faces_verts = verts[faces]
        points = interpolate_face_attributes(
            fragments.pix_to_face, fragments.bary_coords, faces_verts
        )

        camera_position = cameras.get_camera_center()
        view_direction = camera_position - points
        view_direction = F.normalize(
            view_direction, p=2, dim=-1, eps=1e-6
        )  # [1, 2048, 2048, 1, 3]

        dot = torch.sum(view_direction * pixel_normals, dim=-1)  # [1, 2048, 2048, 1]
        torch.save(dot[0], normal_path_ptc)

        depth_frag = fragments.zbuf[0].clone()
        depth_frag = torch.where(
            depth_frag == -1, Z_far * torch.ones_like(depth_frag), depth_frag
        )
        depth_tensor = depth_frag[:, :, 0]
        np.save(depth_path_ptc, depth_tensor.cpu().numpy())

        rasterizer_mesh = MeshRasterizer(
            raster_settings=raster_settings_mesh, cameras=cameras
        )
        fragments = rasterizer_mesh(meshes)

        vertex_normals = meshes.verts_normals_packed()  # (V, 3)
        faces_normals = vertex_normals[faces]

        pixel_normals = interpolate_face_attributes(
            fragments.pix_to_face, fragments.bary_coords, faces_normals
        )
        pixel_normals = F.normalize(pixel_normals, p=2, dim=-1, eps=1e-6)
        verts = meshes.verts_packed()
        faces_verts = verts[faces]
        points = interpolate_face_attributes(
            fragments.pix_to_face, fragments.bary_coords, faces_verts
        )

        camera_position = cameras.get_camera_center()
        view_direction = camera_position - points
        view_direction = F.normalize(
            view_direction, p=2, dim=-1, eps=1e-6
        )  # [1, 2048, 2048, 1, 3]

        dot = torch.sum(view_direction * pixel_normals, dim=-1)  # [1, 2048, 2048, 1]

        torch.save(dot[0], normal_path)

        depth_frag_img = fragments.zbuf[0].clone()
        depth_frag_img = torch.where(
            depth_frag_img == -1, torch.zeros_like(depth_frag_img), depth_frag_img
        )

        depth_frag_img = depth_frag_img / Z_far

        depth_frag_img = depth_frag_img[:, :, 0].cpu().numpy()
        depth_frag_img = (depth_frag_img * 65535).astype(np.uint16)
        depth_frag_img = Image.fromarray(depth_frag_img)
        depth_frag_img.save(f"{ipt_depth_dir}/out.png")

        depth_frag = fragments.zbuf[0].clone()
        depth_frag = torch.where(
            depth_frag == -1, Z_far * torch.ones_like(depth_frag), depth_frag
        )
        depth_tensor = depth_frag[:, :, 0]

        np.save(depth_path, depth_tensor.cpu().numpy())

    return depth_path


def backward_oculusion_aware_render(
    cur_angle,
    next_angle,
    inpaint_config,
    mesh_config,
    meshes,
    bg_image,
    angle_inc=40,
    use_train=False,
    device="cpu",
):
    Z_near, Z_far = inpaint_config["znear"], inpaint_config["zfar"]
    fov = inpaint_config["fov"]
    save_dir = create_dir(mesh_config["save_dir"])
    dataset_dir = create_dir(f"{save_dir}/dataset")
    normal_thresh = import_config_key(inpaint_config, "normal_thresh", 0.3)
    normal_mask_val = import_config_key(inpaint_config, "normal_mask_val", 0.8)
    add_samples = import_config_key(inpaint_config, "add_samples", -1)

    render_depth_map(next_angle, meshes, inpaint_config, mesh_config, device)
    render_depth_map(cur_angle, meshes, inpaint_config, mesh_config, device)

    next_normal_path = f"{dataset_dir}/{next_angle}/depth/out_norm_ptc.pt"
    next_normal = torch.load(next_normal_path)[:, :, 0]
    normal_path = f"{dataset_dir}/{cur_angle}/depth/out_norm_ptc.pt"
    normal = torch.load(normal_path)[:, :, 0]

    img_path = f"{dataset_dir}/{cur_angle}/out_alpha.png"
    if use_train:
        img_path = f"{dataset_dir}/{cur_angle}/out_train.png"

    elev_angles = torch.tensor([0]).to(device)
    azim_angles = torch.tensor([-angle_inc]).to(device)

    R, T = look_at_view_transform(
        (Z_near + Z_far) / 2, elev_angles.flatten(), (azim_angles + 180).flatten()
    )

    cameras = FoVPerspectiveCameras(device=device, R=R, T=T, fov=fov)

    def convert_depth_to_ptcloud(depth_path):
        d = np.load(depth_path)
        depth_tensor = torch.tensor(d).to(device)
        depth_tensor = depth_tensor.reshape(
            depth_tensor.shape[0], depth_tensor.shape[1], 1
        )
        depth_tensor = torch.where(
            depth_tensor == depth_tensor.max(),
            100 * torch.ones_like(depth_tensor),
            depth_tensor,
        )
        H, W = depth_tensor.shape[0:2]
        focal_length = [
            1 / np.tan(fov / 2 * np.pi / 180) * H / 2,
            1 / np.tan(fov / 2 * np.pi / 180) * W / 2,
        ]
        ray_directions = get_ray_directions(H, W, focal_length).to(device)
        pt_cloud = ray_directions * depth_tensor
        pt_cloud[:, :, 2] = pt_cloud[:, :, 2] - (Z_near + Z_far) / 2

        return pt_cloud

    depth_path_ptc = f"{dataset_dir}/{next_angle}/depth/out_ptc.npy"
    cur_depth_path_ptc = f"{dataset_dir}/{cur_angle}/depth/out_ptc.npy"

    pt_cloud = convert_depth_to_ptcloud(depth_path_ptc)
    pt_cloud2 = convert_depth_to_ptcloud(cur_depth_path_ptc)

    d = np.load(depth_path_ptc)
    depth_tensor = torch.tensor(d).to(device)

    img = Image.open(img_path)
    img = img.resize((depth_tensor.shape[0], depth_tensor.shape[1]), Image.LANCZOS)

    img_tensor = torch.as_tensor(np.array(img, copy=True))
    img_tensor = (
        img_tensor.view(img.size[1], img.size[0], -1).permute(2, 0, 1).to(device)
    )
    img_tensor = img_tensor.float()
    img_tensor = img_tensor / img_tensor.max()

    surface_pts = cameras.get_world_to_view_transform().transform_points(pt_cloud)
    surface_pts[:, :, 2] = surface_pts[:, :, 2] - (Z_near + Z_far) / 2
    surface_pts_masked = surface_pts * (depth_tensor != depth_tensor.max())[:, :, None]

    ndc_coords = -cameras.transform_points_ndc(pt_cloud)[:, :, :2]
    grid = ndc_coords[None, ...]

    input = img_tensor[None, ...]
    images = torch.nn.functional.grid_sample(
        input, grid, mode="bilinear", padding_mode="border", align_corners=False
    )
    images = images.permute(0, 2, 3, 1)

    input = normal[None, None, ...]
    normals = torch.nn.functional.grid_sample(
        input, grid, mode="nearest", padding_mode="border", align_corners=False
    )
    normals = normals[0, 0]

    input = pt_cloud2[None,].permute(0, 3, 1, 2)
    rev_depth = torch.nn.functional.grid_sample(
        input, grid, mode="bilinear", padding_mode="zeros", align_corners=False
    )

    if add_samples > 0:
        for j in range(add_samples):
            grid = ndc_coords[None, ...].clone()
            g_cuda = torch.Generator(device="cuda")
            g_cuda.manual_seed(0)
            grid = grid + (2 * torch.rand_like(grid) - 1) * (1 / 512.0)
            input = img_tensor[None, ...]
            images_sample = torch.nn.functional.grid_sample(
                input, grid, mode="bilinear", padding_mode="border", align_corners=False
            )

            images = images + images_sample.permute(0, 2, 3, 1)
            input = normal[None, None, ...]
            normals_sample = torch.nn.functional.grid_sample(
                input, grid, mode="nearest", padding_mode="border", align_corners=False
            )
            normals = normals + normals_sample[0, 0]

        images = images / (add_samples + 1)
        normals = normals / (add_samples + 1)

    rev_depth_masked = (
        rev_depth.permute(0, 2, 3, 1)[0]
        * (depth_tensor != depth_tensor.max())[:, :, None]
    )

    pt_dist = 0.1
    pt_dist2 = pt_dist**2
    occlu_mask = (
        torch.sum((surface_pts_masked - rev_depth_masked) ** 2, axis=-1) > pt_dist2
    )

    norm_mask = (
        (normals < normal_thresh)
        * (next_normal > normal)
        * (~occlu_mask)
        * (depth_tensor != depth_tensor.max())
    )

    images[0, :, :, 3] = torch.where(
        ~norm_mask,
        images[0, :, :, 3],
        normal_mask_val * torch.ones_like(images[0, :, :, 3]),
    )
    images[0, :, :, 3] = torch.where(
        (depth_tensor == depth_tensor.max()),
        torch.zeros_like(images[0, :, :, 3]),
        images[0, :, :, 3],
    )
    down = torch.nn.Upsample(size=(512, 512), mode="bilinear")

    images[0, :, :, 3] = torch.where(
        occlu_mask, torch.zeros_like(images[0, :, :, 3]), images[0, :, :, 3]
    )

    images = down(images.permute(0, 3, 1, 2)).permute(0, 2, 3, 1)
    images[0, :, :, :3] = torch.where(
        images[0, :, :, 3:4] == 0, bg_image, images[0, :, :, :3]
    )

    return images


def render_silhouette(
    angle, meshes, inpaint_config, mesh_config, size=512, device="cpu"
):
    Z_near, Z_far = inpaint_config["znear"], inpaint_config["zfar"]
    fov = inpaint_config["fov"]
    save_dir = create_dir(mesh_config["save_dir"])
    create_dir(f"{save_dir}/dataset")
    sil_dir = create_dir(f"{save_dir}/sil")
    elev_angles = torch.tensor([0]).to(device)
    azim_angles = torch.tensor([angle]).to(device)
    R, T = look_at_view_transform(
        (Z_near + Z_far) / 2, elev_angles.flatten(), (azim_angles + 180).flatten()
    )
    cameras = FoVPerspectiveCameras(device=device, R=R, T=T, fov=fov)
    rasterizer_mesh = MeshRasterizer(
        raster_settings=raster_settings_mesh, cameras=cameras
    )
    rasterizer_mesh.raster_settings.image_size = size
    fragments = rasterizer_mesh(meshes)
    sil = fragments.zbuf[0, :, :, 0] != -1
    sil = Image.fromarray((255 * sil.cpu().numpy()).astype(np.uint8))
    sil_path = f"{sil_dir}/{angle:04d}.png"
    sil.save(sil_path)
