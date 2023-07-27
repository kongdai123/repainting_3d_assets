import os


class obj(object):
    def __init__(self, d):
        for k, v in d.items():
            if isinstance(k, (list, tuple)):
                setattr(self, k, [obj(x) if isinstance(x, dict) else x for x in v])
            else:
                setattr(self, k, v)

    def __repr__(self):
        return str(self.__dict__)


def create_dir(dir_name):
    os.makedirs(dir_name, exist_ok=True)
    return dir_name


def import_config_key(config, key, default=""):
    if key in config:
        return config[key]
    else:
        return default
