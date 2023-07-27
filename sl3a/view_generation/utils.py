import cv2
import numpy as np
import os


def create_dir(dir_name):
    os.makedirs(dir_name, exist_ok=True)
    return dir_name


def import_config_key(config, key, default=""):
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
