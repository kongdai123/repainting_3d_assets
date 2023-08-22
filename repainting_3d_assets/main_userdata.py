import argparse
import json
import os

from repainting_3d_assets.nerf_reconstruction.common import add_instantngp_sys_path


def process_one(path_in, path_out, prompt, seed, inpaint_config, nerf_config):
    from repainting_3d_assets.paint import paint

    mesh_config = {
        "prompt": prompt,
        "obj": path_in,
        "save_dir": path_out,
        "seed_latents": seed,
    }

    paint(mesh_config, inpaint_config, nerf_config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--path_in", type=str, required=True)
    parser.add_argument("-p", "--prompt", type=str, required=True)
    parser.add_argument("-o", "--path_out", type=str, required=True)
    parser.add_argument("-g", "--path_instantngp", type=str, required=True)
    parser.add_argument("-s", "--seed", type=int, default=2023)
    parser.add_argument(
        "--config_inpaint_path",
        type=str,
        default="./repainting_3d_assets/view_generation/config/config_inpaint.json",
    )
    parser.add_argument(
        "--config_nerf_path",
        type=str,
        default="./repainting_3d_assets/nerf_reconstruction/config/config_nerf.json",
    )

    args, unknown = parser.parse_known_args()

    if unknown:
        raise ValueError("Unknown arguments", unknown)

    add_instantngp_sys_path(args.path_instantngp)

    with open(args.config_inpaint_path) as json_file:
        inpaint_config = json.load(json_file)
    with open(args.config_nerf_path) as json_file:
        nerf_config = json.load(json_file)
    nerf_config["path_instantngp"] = args.path_instantngp

    process_one(
        args.path_in, args.path_out, args.prompt, args.seed, inpaint_config, nerf_config
    )
