from .colors import colors
import torch
# from diff_view_gen.utils import * 
import torch
import pandas
import os

def get_all_idx_of_substring(my_string, substring):
    idx = []
    index = my_string.find(substring)
    # Keep searching for the substring until no more occurrences are found
    while index != -1:
        idx.append(index)
        # Search for the next occurrence of the substring
        index = my_string.find(substring, index + 1)
    return idx
def convert_string_to_torch(my_string, device = "cuda", dtype = torch.float32):
    idx = [-2]
    idx += (get_all_idx_of_substring(my_string, '\\,'))
    res = torch.tensor([0,0,0], device = device, dtype = dtype)
    idx.append(len(my_string))
    for i in range(3):
        res[i] = float(my_string[idx[i] + 2: idx[i + 1]])
    return res

def get_all_idx_of_substring(my_string, substring):
    idx = []
    index = my_string.find(substring)
    # Keep searching for the substring until no more occurrences are found
    while index != -1:
        idx.append(index)
        # Search for the next occurrence of the substring
        index = my_string.find(substring, index + 1)
    return idx
def convert_string_to_torch(my_string, device = "cuda", dtype = torch.float32):
    idx = [-2]
    idx += (get_all_idx_of_substring(my_string, '\\,'))
    res = torch.tensor([0,0,0], device = device, dtype = dtype)
    idx.append(len(my_string))
    for i in range(3):
        res[i] = float(my_string[idx[i] + 2: idx[i + 1]])
    return res


class ShapeNetDataset():
    def __init__(
        self,
        SHAPENET_DIR,
        SAVE_DIR,
        device = "cpu",
        dtype = torch.float32
    ):
        self.SHAPENET_DIR = SHAPENET_DIR
        self.SAVE_DIR = SAVE_DIR
        self.mesh_dir = f"{SHAPENET_DIR}/models"
        self.meta_path = f"{SHAPENET_DIR}/metadata.csv"
        self.mesh_data = pandas.read_csv(self.meta_path)
        self.mesh_num = self.mesh_data.shape[0]
        self.device = device
        self.dtype = dtype
        self.trans_tar = torch.tensor([[1,0,0],
                          [0,1,0],
                          [0,0,1]], device =  device).to(dtype)
    def __len__(self):
        return self.mesh_num
    def __getitem__(self, idx, exp_name = "", save_dir = None, seed_latents = 2023, color = "", prepend_idx=False):
        dataframe = self.mesh_data.iloc[idx]
        mesh_path =  f"{self.mesh_dir}/{dataframe[0][4:]}.obj"
        up = dataframe[4]
        front = dataframe[5]
        name = str(dataframe[-2])
        if isinstance(up, str) and isinstance(front, str):
            up_vec = convert_string_to_torch(up, device =  self.device, dtype = self.dtype)
            fron_vec = convert_string_to_torch(front, device =  self.device, dtype = self.dtype)
            right_vec  = up_vec.cross(fron_vec)
            trans_ori = torch.cat([right_vec[None,], up_vec[None,], fron_vec[None,]], axis = 0)
        else:
            trans_ori = torch.tensor([[1,0,0],
                                  [0,0,1],
                                  [0,-1,0]], device =  self.device).to(self.dtype)
        trans_tar = torch.tensor([[1,0,0],
                          [0,1,0],
                          [0,0,1]], device =  self.device).to(self.dtype)

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
            