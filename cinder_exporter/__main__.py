import os
import sys
import argparse

from time import sleep
from string import Template

from loguru import logger as log
from prometheus_client import REGISTRY

from cinder_exporter.cinder_collector import DataDumpCollect, CinderCollector
from cinder_exporter.prometheus import CollectMany, init_http_server
from cinder_exporter.common import get_cloud_config, create_dump_path

# Default vars
_REFRESH_INTERVAL = 120
_EXPORTER_PORT = 9250
_DUMP_PATH = "/tmp/cinder_exporter.cache"


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
        "--refresh-interval",
        type=int,
        default=_REFRESH_INTERVAL,
        help=f"Refresh interval in seconds for data collect [Default: {_REFRESH_INTERVAL}]"
    )
    parser.add_argument(
        "--dump-path",
        default=_DUMP_PATH,
        help=f"Path for the dumps [Default: {_DUMP_PATH}]"
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
    # Get args
    args = arg_parser()
    # Init logger
    log_level = "DEBUG" if args.debug else "INFO"
    log.remove()
    log.add(
        sys.stderr,
        level=log_level,
        format="{time:YYYY/MM/DD HH:mm:ss}  {level:<7} - {message}"
    )
    # Check pid file
    if os.path.isfile(pid_file):
        log.error(f"{error_msg}: Existing pid file is present")
        exit(1)
    # Get cloud config
    auths = get_cloud_config(args.cloud_config)
    stacks = auths.keys()
    # Generate dump file template path
    create_dump_path(args.dump_path)
    f_template = Template(
        os.path.join(args.dump_path, f"$name.{collector_pid}.dump")
    )
    # Init prometheus http server
    log.info(f"Cinder Exporter Start (PID:{collector_pid}) ..")
    init_http_server(args.port)
    # Start data collect with interval
    for stack in stacks:
        data_collect = DataDumpCollect(
            name=stack,
            auth=auths[stack],
            file_dump=f_template.substitute(name=stack.lower()),
            refresh_interval=args.refresh_interval
        )
        data_collect.start()
    # Wait dump files creation
    log.debug("Wait for first dump file creation ..")
    sleep(len(stacks) * 2)
    # Start cinder prometheus collector
    collectors = []
    for stack in stacks:
        collector = CinderCollector(
            name=stack,
            file_dump=f_template.substitute(name=stack.lower()),
        )
        collectors.append(collector)
    REGISTRY.register(CollectMany(collectors))
    log.info(f"Exporting Completed")

    while True:
        sleep(30)

if __name__ == "__main__":
    main()
