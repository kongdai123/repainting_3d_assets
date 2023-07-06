import struct
import torch
from PIL import Image
import torchvision.transforms as transforms
import cv2
import json
import numpy as np
import os
import shutil

class obj(object):
    def __init__(self, d):
        for k, v in d.items():
            if isinstance(k, (list, tuple)):
                setattr(self, k, [obj(x) if isinstance(x, dict) else x for x in v])
            else:
                setattr(self, k, v)

def create_dir(dir_name):
    os.makedirs(dir_name, exist_ok=True)
    return dir_name

def import_config_key (config, key, default = ""):
    if key in config:
        return config[key]
    else:
        return default
def variance_of_laplacian(image):
	return cv2.Laplacian(image, cv2.CV_64F).var()

def sharpness(imagePath):
	image = cv2.imread(imagePath)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	fm = variance_of_laplacian(gray)
	return max(fm, 1)


def listify_matrix(mat):
    return np.ndarray.tolist(mat.cpu().numpy())

def remove_artifacts(save_dir):
    os.remove(f"{save_dir}/transforms.json")
    shutil.rmtree(f"{save_dir}/dataset", ignore_errors=True)
    shutil.rmtree(f"{save_dir}/vis", ignore_errors=True)
    shutil.rmtree(f"{save_dir}/sil", ignore_errors=True)
