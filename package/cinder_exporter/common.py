import yaml
from loguru import logger

def format_id(project_id):
    last_num = 0
    result = []
    for num in [8, 12, 16, 20, 32]:
        result.append(project_id[last_num:num])
        last_num = num

    return "-".join(result)

def format_metadata(mdata):
    if mdata:
        result = [f"{k}={v}" for k, v in mdata.items()]
        return ",".join(result)

    return ""

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
