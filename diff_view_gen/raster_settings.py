from pytorch3d.renderer import RasterizationSettings


raster_settings_mesh = RasterizationSettings(
    image_size=512,
    blur_radius=0,
    faces_per_pixel=1,
    perspective_correct=True,
    bin_size=-1,
    cull_backfaces=True,
)

raster_settings_mesh_ptcloud = RasterizationSettings(
    image_size=2048,
    blur_radius=0,
    faces_per_pixel=1,
    perspective_correct=True,
    bin_size=-1,
    cull_backfaces=True,
)
