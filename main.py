import argparse
import json
import os

import pandas
import torch

from nerf_recon.common import add_instantngp_sys_path


class ShapeNetDataset():
    def __init__(
            self,
            SHAPENET_DIR,
            SAVE_DIR,
            device="cpu",
            dtype=torch.float32
    ):
        self.SHAPENET_DIR = SHAPENET_DIR
        self.SAVE_DIR = SAVE_DIR
        self.mesh_dir = f"{SHAPENET_DIR}/models"
        self.meta_path = f"{SHAPENET_DIR}/metadata.csv"
        self.mesh_data = pandas.read_csv(self.meta_path)
        self.mesh_num = self.mesh_data.shape[0]
        self.device = device
        self.dtype = dtype
        self.trans_tar = torch.tensor([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ], device=device).to(dtype)

    def __len__(self):
        return self.mesh_num

    def get(self, idx, exp_name="", save_dir=None, seed_latents=2023, color="", prepend_idx=False):
        dataframe = self.mesh_data.iloc[idx]
        mesh_path = f"{self.mesh_dir}/{dataframe[0][4:]}.obj"
        up = dataframe[4]
        front = dataframe[5]
        name = str(dataframe[-2])
        if isinstance(up, str) and isinstance(front, str):
            def convert_string_to_torch(my_string, device="cuda", dtype=torch.float32):
                vec = [int(a) for a in my_string.split('\\,')]
                assert len(vec) == 3
                out = torch.tensor(vec, device=device, dtype=dtype)
                return out

            up_vec = convert_string_to_torch(up, device=self.device, dtype=self.dtype)
            fron_vec = convert_string_to_torch(front, device=self.device, dtype=self.dtype)
            right_vec = up_vec.cross(fron_vec)
            trans_ori = torch.cat([right_vec[None,], up_vec[None,], fron_vec[None,]], dim=0)
        else:
            trans_ori = torch.tensor([
                [1, 0, 0],
                [0, 0, 1],
                [0, -1, 0]
            ], device=self.device).to(self.dtype)
        trans_tar = torch.tensor([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ], device=self.device).to(self.dtype)

        trans_mat = torch.matmul(trans_tar, trans_ori.inverse())

        sanitized_name = name.replace(' ', '_')
        save_name = f'{sanitized_name}'
        if exp_name != "":
            save_name += f'__{exp_name}'
        save_name += f'__{dataframe[0][4:]}'
        if prepend_idx:
            save_name = f'{idx:05d}__{save_name}'
        if save_dir is None:
            save_dir = os.path.join(self.SAVE_DIR, save_name)

        config = {
            "prompt": name,
            "code": dataframe[0][4:],
            "obj": mesh_path,
            "save_dir": save_dir,
            "save_name": save_name,
            "seed_latents": seed_latents,
            "color": color,
            "trans_mat": (trans_mat)
        }

        return config


def process_one(dataset, mesh_idx, inpaint_config, nerf_config):
    mesh_config = dataset.get(mesh_idx, seed_latents=(mesh_idx + 1) * 16384 - 1, prepend_idx=True)
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
