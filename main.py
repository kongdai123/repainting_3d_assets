import argparse
import json
from dataloader.dataloader import *
from nerf_recon.common import add_instantngp_sys_path


def process_one(dataset, mesh_idx, inpaint_config, nerf_config):
    mesh_config = dataset.__getitem__(mesh_idx, seed_latents=(mesh_idx + 1) * 16384 - 1, prepend_idx=True)
    try:
        from paint import paint
        paint(mesh_config, inpaint_config, nerf_config)
    except Exception as e:
        if 'out of memory' in str(e):
            print('| WARNING: ran out of memory, this seems irrecoverable for the process')
            raise e
        print(e)
        import traceback
        print(traceback.print_exc())
        print('Continuing')


def process_items(dataset, range_ids_list, inpaint_config, nerf_config):
    for mesh_idx in range_ids_list:
        process_one(dataset, mesh_idx, inpaint_config, nerf_config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path_instantngp', type=str, required=True)
    parser.add_argument('--path_shapenet', type=str, required=True)
    parser.add_argument('--path_out', type=str, required=True)
    parser.add_argument('--config_inpaint_path', type=str, default="./diff_view_gen/config/config_inpaint.json")
    parser.add_argument('--config_nerf_path', type=str, default="./nerf_recon/config/config_nerf.json")
    parser.add_argument('--range_start', type=int, default=None)
    parser.add_argument('--range_end', type=int, default=None)
    parser.add_argument('--range_ids_list', type=int, nargs="+")

    args, unknown = parser.parse_known_args()

    if unknown:
        raise ValueError('Unknown arguments', unknown)

    add_instantngp_sys_path(args.path_instantngp)

    with open(args.config_inpaint_path) as json_file:
        inpaint_config = json.load(json_file)
    with open(args.config_nerf_path) as json_file:
        nerf_config = json.load(json_file)
    nerf_config['path_instantngp'] = args.path_instantngp

    dataset = ShapeNetDataset(args.path_shapenet, args.path_out)
    mesh_num = len(dataset)

    if args.range_start is not None:
        if args.range_end is None or args.range_end > mesh_num:
            args.range_end = mesh_num
        process_items(dataset, list(range(args.range_start, args.range_end)), inpaint_config, nerf_config)
    else:
        process_items(dataset, args.range_ids_list, inpaint_config, nerf_config)
