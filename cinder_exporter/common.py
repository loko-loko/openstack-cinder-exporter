import os
import yaml
import pickle
from loguru import logger as log

def get_cloud_config(config_file):

    log.debug(f"Get yaml config file: {config_file}")
    try:
        with open(config_file) as f:
            fy = yaml.safe_load(f)
        return fy['clouds']

    except TypeError as te:
        log.error(f'The config file cannot be parsed: {te}')
        exit(1)
    except FileNotFoundError as fe:
        log.error(f'The config file was not found: {fe}')
        exit(127)


def create_dump_path(dump_path):
    if not os.path.exists(dump_path):
        try:
            log.debug("Create dump directory")
            os.makedirs(dump_path)
        except Exception as e:
            log.error(f"The dump directory cannot be created: {e}")
            exit(1)


def write_dump_data_to_file(dump_file, data):
    log.debug(f"Write dump data to {dump_file} ..")
    try:
        with open(dump_file, "wb+") as f:
            pickle.dump((data, ), f, pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        log.error(f"Dump can't be write on dump file: {e}")
        exit(1)


def read_dump_data_from_file(dump_file, item=None):
    log.debug(f"Read dump data from {dump_file} ..")
    with open(dump_file, "rb") as f:
        data = pickle.load(f)[0]
    if not item:
        return data
    return data[item]
