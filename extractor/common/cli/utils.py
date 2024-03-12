import json
import os

import yaml


def read_yaml(_path):
    """Reads a yaml file

    Args:
      _path: path to the file


    Returns:
      a dict with the configuration

    """

    with open(_path, "r") as f_stream:
        config = yaml.load(f_stream, Loader=yaml.FullLoader)

    return config


def read_json(_path):
    """Reads json file

    Args:
      _path: path to the file

    Returns:
      a dict with the object

    """

    with open(_path, "r") as f_in:
        _json = json.load(f_in)

    return _json


def write_json(_path, _json, indent=0):
    """Writes a json file

    Args:
      _path: to the file
      _json: json to write

    """

    with open(_path, "w+") as f_out:
        json.dump(_json, f_out, indent=indent)


def remove_locally_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def write_ndjson(_path, _ndjson):
    """Writes a ndjson file

    Args:
      _path: to the file
      _ndjson: ndjson to write


    """

    with open(_path, "w+") as f_out:
        for line in _ndjson:
            f_out.write("{}\n".format(json.dumps(line)))
