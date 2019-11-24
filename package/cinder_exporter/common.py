import yaml
from loguru import logger

def format_project_id(project_id):
    last_num = 0
    split_lst = []
    for num in [8, 12, 16, 20, 32]:
        split_lst.append(project_id[last_num:num])
        last_num = num

    return "-".join(split_lst)

def get_cloud_config(config_file):

    logger.debug(f"Get yaml config file: {config_file}")
    try:
        with open(config_file) as f:
            fy = yaml.safe_load(f)
        return fy['clouds']

    except TypeError as te:
        logger.error(f'The config file cannot be parsed: {te}')
        exit(1)
    except FileNotFoundError as fe:
        logger.error(f'The config file was not found: {fe}')
        exit(127)
