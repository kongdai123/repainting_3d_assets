import pytorch3d
from pytorch3d.io.mtl_io import *
from pytorch3d.io.obj_io import *
from pytorch3d.io.utils import _check_faces_indices, _open_file

from sl3a.view_generation.utils3D import swap_faces


def load_obj(
    f,
    load_textures: bool = True,
    create_texture_atlas: bool = False,
    texture_atlas_size: int = 512,
    texture_wrap: Optional[str] = "repeat",
    device: Device = "cpu",
    path_manager: Optional[PathManager] = None,
    swap_face: bool = True,
):
    data_dir = "./"
    if isinstance(f, (str, bytes, Path)):
        data_dir = os.path.dirname(f)
    if path_manager is None:
        path_manager = PathManager()
    with _open_file(f, path_manager, "r") as f:
        return _load_obj_swap(
            f,
            data_dir=data_dir,
            load_textures=load_textures,
            create_texture_atlas=create_texture_atlas,
            texture_atlas_size=texture_atlas_size,
            texture_wrap=texture_wrap,
            path_manager=path_manager,
            device=device,
            swap_face=swap_face,
        )


def _load_obj_swap(
    f_obj,
    *,
    data_dir: str,
    load_textures: bool = True,
    create_texture_atlas: bool = False,
    texture_atlas_size: int = 512,
    texture_wrap: Optional[str] = "repeat",
    path_manager: PathManager,
    device: Device = "cpu",
    swap_face: bool = True
):
    """
    Load a mesh from a file-like object. See load_obj function more details.
    Any material files associated with the obj are expected to be in the
    directory given by data_dir.
    """

    if texture_wrap is not None and texture_wrap not in ["repeat", "clamp"]:
        msg = "texture_wrap must be one of ['repeat', 'clamp'] or None, got %s"
        raise ValueError(msg % texture_wrap)

    (
        verts,
        normals,
        verts_uvs,
        faces_verts_idx,
        faces_normals_idx,
        faces_textures_idx,
        faces_materials_idx,
        material_names,
        mtl_path,
    ) = pytorch3d.io.obj_io._parse_obj(f_obj, data_dir)

    verts = pytorch3d.io.obj_io._make_tensor(
        verts, cols=3, dtype=torch.float32, device=device
    )  # (V, 3)
    normals = pytorch3d.io.obj_io._make_tensor(
        normals,
        cols=3,
        dtype=torch.float32,
        device=device,
    )  # (N, 3)
    verts_uvs = pytorch3d.io.obj_io._make_tensor(
        verts_uvs,
        cols=2,
        dtype=torch.float32,
        device=device,
    )  # (T, 2)

    faces_verts_idx = pytorch3d.io.obj_io._format_faces_indices(
        faces_verts_idx, verts.shape[0], device=device
    )
    if swap_face:
        faces_verts_idx = swap_faces(faces_verts_idx)

    # Repeat for normals and textures if present.
    if len(faces_normals_idx):
        faces_normals_idx = pytorch3d.io.obj_io._format_faces_indices(
            faces_normals_idx, normals.shape[0], device=device, pad_value=-1
        )
        if swap_face:
            faces_normals_idx = swap_faces(faces_normals_idx)

    if len(faces_textures_idx):
        faces_textures_idx = pytorch3d.io.obj_io._format_faces_indices(
            faces_textures_idx, verts_uvs.shape[0], device=device, pad_value=-1
        )
        if swap_face:
            faces_textures_idx = swap_faces(faces_textures_idx)

    if len(faces_materials_idx):
        faces_materials_idx = torch.tensor(
            faces_materials_idx, dtype=torch.int64, device=device
        )

    texture_atlas = None
    material_colors, texture_images = pytorch3d.io.obj_io._load_materials(
        material_names,
        mtl_path,
        data_dir=data_dir,
        load_textures=load_textures,
        path_manager=path_manager,
        device=device,
    )

    if material_colors and not material_names:
        # usemtl was not present but single material was present in the .mtl file
        material_names.append(next(iter(material_colors.keys())))
        # replace all -1 by 0 material idx
        if torch.is_tensor(faces_materials_idx):
            faces_materials_idx.clamp_(min=0)

    if create_texture_atlas:
        # Using the images and properties from the
        # material file make a per face texture map.

        # Create an array of strings of material names for each face.
        # If faces_materials_idx == -1 then that face doesn't have a material.
        idx = faces_materials_idx.cpu().numpy()
        face_material_names = np.array(material_names)[idx]  # (F,)
        face_material_names[idx == -1] = ""

        # Construct the atlas.
        texture_atlas = make_mesh_texture_atlas_repeat(
            material_colors,
            texture_images,
            face_material_names,
            faces_textures_idx,
            verts_uvs,
            texture_atlas_size,
            texture_wrap,
        )

    faces = pytorch3d.io.obj_io._Faces(
        verts_idx=faces_verts_idx,
        normals_idx=faces_normals_idx,
        textures_idx=faces_textures_idx,
        materials_idx=faces_materials_idx,
    )
    aux = pytorch3d.io.obj_io._Aux(
        normals=normals if len(normals) else None,
        verts_uvs=verts_uvs if len(verts_uvs) else None,
        material_colors=material_colors,
        texture_images=texture_images,
        texture_atlas=texture_atlas,
    )
    return verts, faces, aux


def make_mesh_texture_atlas_repeat(
    material_properties: Dict,
    texture_images: Dict,
    face_material_names,
    faces_uvs: torch.Tensor,
    verts_uvs: torch.Tensor,
    texture_size: int,
    texture_wrap: Optional[str],
) -> torch.Tensor:
    F = faces_uvs.shape[0]

    # Initialize the per face texture map to a white color.
    # TODO: allow customization of this base color?
    R = texture_size
    f = F
    while f > 500:
        f = f // 4
        R = max(R // 2, 1)
    atlas = torch.ones(size=(F, R, R, 3), dtype=torch.float32, device=faces_uvs.device)
    # Check for empty materials.
    if not material_properties and not texture_images:
        return atlas

    # Iterate through the material properties - not
    # all materials have texture images so this is
    # done first separately to the texture interpolation.
    for material_name, props in material_properties.items():
        # Bool to indicate which faces use this texture map.
        faces_material_ind = torch.from_numpy(face_material_names == material_name).to(
            faces_uvs.device
        )
        if faces_material_ind.sum() > 0:
            # For these faces, update the base color to the
            # diffuse material color.
            if "diffuse_color" not in props:
                continue
            atlas[faces_material_ind, ...] = props["diffuse_color"][None, :]

    # If there are vertex texture coordinates, create an (F, 3, 2)
    # tensor of the vertex textures per face.
    faces_verts_uvs = verts_uvs[faces_uvs] if len(verts_uvs) > 0 else None

    # Some meshes only have material properties and no texture image.
    # In this case, return the atlas here.
    if faces_verts_uvs is None:
        return atlas

    # Iterate through the materials used in this mesh. Update the
    # texture atlas for the faces which use this material.
    # Faces without texture are white.
    for material_name, image in list(texture_images.items()):
        # Only use the RGB colors
        if image.shape[2] == 4:
            image = image[:, :, :3]

        # Reverse the image y direction
        image = torch.flip(image, [0]).type_as(faces_verts_uvs)

        # Bool to indicate which faces use this texture map.
        faces_material_ind = torch.from_numpy(face_material_names == material_name).to(
            faces_verts_uvs.device
        )

        # Find the subset of faces which use this texture with this texture image
        uvs_subset = faces_verts_uvs[faces_material_ind, :, :]
        repeats = max(
            1,
            (torch.ceil(uvs_subset.max()) - torch.floor(uvs_subset.min())).int().item(),
        )
        uvs_subset = (uvs_subset - torch.floor(uvs_subset.min())) / repeats
        sz_max_allowed = 512
        sz_img = max(image.shape[0], image.shape[1])
        sz_repeated = repeats * sz_img
        sz_img_downsampled = sz_max_allowed // repeats
        if sz_repeated <= 16384:
            image = image.repeat(repeats, repeats, 1)
            if sz_repeated > sz_max_allowed:
                image = image.permute(2, 0, 1)[None,]  # (1,3,h, w)
                image = torch.nn.functional.interpolate(
                    image,
                    size=(sz_max_allowed, sz_max_allowed),
                    mode="bilinear",
                    align_corners=False,
                    antialias=True,
                )
                image = image[0].permute(1, 2, 0)
        elif sz_img_downsampled <= 1:
            # beyond repair
            image = torch.ones_like(image)
        else:
            image = image.permute(2, 0, 1)[None,]  # (1,3,h, w)
            image = torch.nn.functional.interpolate(
                image,
                size=(sz_img_downsampled, sz_img_downsampled),
                mode="bilinear",
                align_corners=False,
                antialias=True,
            )
            image = image[0].permute(1, 2, 0)
            image = image.repeat(repeats, repeats, 1)

        atlas[faces_material_ind, :, :] = make_material_atlas(image, uvs_subset, R)

    return atlas


pytorch3d.io.mtl_io.make_mesh_texture_atlas = make_mesh_texture_atlas_repeat

pytorch3d.io.obj_io.make_mesh_texture_atlas = make_mesh_texture_atlas_repeat
pytorch3d.io.obj_io._load_obj = _load_obj_swap
