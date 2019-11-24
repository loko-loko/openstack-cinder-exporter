# __main__.py

import argparse
import time
import os
import sys
import logging

from loguru import logger
from prometheus_client import REGISTRY

from cinder_exporter.cinder_collector import CinderCollector
from cinder_exporter.prometheus import CollectMany, init_http_server
from cinder_exporter.common import get_cloud_config

def arg_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-f",
        "--cloud-config",
        required=True,
        help="Cloud config file with Openstack auth. info"
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        required=True,
        help="Port for the webserver scraped by Prometheus"
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Debug Mode"
    )

    return parser.parse_args()


def main():

    error_msg = "Collector could not run"

    collector_pid = os.getpid()
    pid_file = "/var/run/cinder-exporter.pid"

    args = arg_parser()

    log_level = "DEBUG" if args.debug else "INFO"

    logger.remove()
    logger.add(
        sys.stderr,
        level=log_level,
        format="{time:YYYY/MM/DD HH:mm:ss}  {level:<7} - {message}"
    )

    if os.path.isfile(pid_file):
        logger.error(f"{error_msg}: Existing pid file is present")
        exit(1)

    auths = get_cloud_config(args.cloud_config)
    openstacks = auths.keys()

    try:
        init_http_server(args.port)

        collectors = []

        for openstack in openstacks:

            if auths[openstack]["enabled"] is False:
                continue

            logger.info(f"Cinder exporter start:{openstack} (PID:{collector_pid}) ..")
            collectors.append(CinderCollector(openstack, auths[openstack]))

        REGISTRY.register(CollectMany(collectors))
        logger.info(f"Exporting completed")

        while True:
            time.sleep(10)

    except ValueError as ve:
        logger.error(f"{error_msg}: {ve}")
        exit(1)
    except ImportError as ie:
        logger.error(f"{error_msg}: {ie}")
        exit(1)
    except AttributeError as ae:
        logger.error(f"{error_msg}: {ae}")
        exit(1)
    except PermissionError as pe:
        logger.error(f"{error_msg}: {pe}")
        exit(1)

if __name__ == "__main__":
    main()
