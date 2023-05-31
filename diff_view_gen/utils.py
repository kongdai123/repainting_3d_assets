import struct
import torch
from PIL import Image
import cv2
import json
import numpy as np
import os
import torchvision.transforms as transforms


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

def load_img_to_torch(img_path, device):
    # Read a PIL image
    image = Image.open(img_path)

    # Define a transform to convert PIL 
    # image to a Torch tensor
    transform = transforms.Compose([
        transforms.PILToTensor()
    ])

    # transform = transforms.PILToTensor()
    # Convert the PIL image to Torch tensor
    img_tensor = transform(image).to(device)

    # print the converted Torch tensor
    img_tensor = img_tensor.long()
    img_tensor = img_tensor/img_tensor.max()
    img_tensor = img_tensor.permute(1,2,0)
    return img_tensor 