import re
from os import rename
from time import time, sleep
from threading import Thread
from pprint import pformat

from loguru import logger as log
from openstack import connection
from prometheus_client.core import GaugeMetricFamily, InfoMetricFamily

from cinder_exporter.common import write_dump_data_to_file, read_dump_data_from_file


RE_CAMEL_TO_SNAKE = re.compile(r"(?<!^)(?=[A-Z])")


class DataDumpCollect(Thread):

    def __init__(self, name, auth, file_dump, refresh_interval=300):
        Thread.__init__(self)
        self.name = name
        self._client = self._get_client(name, auth)
        self._file_dump = file_dump
        self._refresh_interval = refresh_interval

    @staticmethod
    def _get_client(name, auth):
        log.debug(f"Get openstack client: {name}")
        client = connection.Connection(
            region_name=auth["region_name"],
            auth=dict(
                auth_url=auth["auth_url"],
                username=auth["username"],
                password=auth["password"],
                project_name=auth["project_name"],
                user_domain_name=auth["domain_name"],
                project_domain_name=auth["project_domain_name"]
            ),
            verify=False
        )
        client.authorize()
        client.block_storage
        return client

    def _get_projects(self):
        projects = self._client.list_projects()
        return {p["id"]: p["name"] for p in projects}

    def _get_services(self):
        services = self._client.block_storage.get("/os-services")
        return [s for s in services.json()["services"]]

    def _get_volumes(self):
        volumes = self._client.block_storage.volumes(all_projects=True)
        return [v.to_dict() for v in volumes]

    def _get_limits(self, projects):
        limits = []
        for pid, pname in projects.items():
            limit = {
                "project_id": pid,
                "project_name": pname,
            }
            limit.update(self._client.get_volume_limits(pid)["absolute"])
            limits.append(limit)
        return limits

    def run(self):
        log.debug(f"Starting data gather thread for: {self.name}")
        # Init dump file
        write_dump_data_to_file(dump_file=self._file_dump, data={"collect": 0})
        # Start data collect with interval
        while True:
            start_time = time()
            # Init data
            data = {"collect": 0}
            try:
                # Get openstack data
                projects = self._get_projects()
                data.update({
                    "volumes": self._get_volumes(),
                    "services": self._get_services(),
                    "projects": projects,
                    "limits": self._get_limits(projects),
                })
            except Exception as e:
                log.error(f"Error getting data for {self.name}: {e}")
            else:
                log.info(f"Done getting data for {self.name}")
                # Update data with new value if collect OK
                data.update({
                    "collect": 1,
                    "poll_time": time() - start_time
                })
            # Write new dump
            log.debug(f"Data for {self.name}: {pformat(data)}")
            new_file_dump = f"{self._file_dump}.new"
            write_dump_data_to_file(dump_file=new_file_dump, data=data)
            rename(new_file_dump, self._file_dump)
            log.debug(f"Done dumping data for {self.name} to {self._file_dump}")
            # Waiting for the next collect
            sleep(self._refresh_interval)


class CinderCollector:

    def __init__(self, name, file_dump):
        self.name = name
        self._file_dump = file_dump

    @staticmethod
    def _get_attachments(attachments):
        if attachments:
            return ",".join([a["server_id"] for a in attachments])
        return ""

    def limits(self):
        log.debug(f"Get collect of limits: {self.name}")
        # Get limits from cache file
        limits = read_dump_data_from_file(
            dump_file=self._file_dump,
            item="limits"
        )
        labels = [
            "stack",
            "project_id",
            "project_name",
        ]
        for klimit, vlimit in limits[0].items():
            if not isinstance(vlimit, (int, float)):
                continue
            # Convert limit name to snake case
            klimit_fmt = RE_CAMEL_TO_SNAKE.sub("_", klimit).lower()
            limits_metrics = GaugeMetricFamily(
                f"cinder_limit_{klimit_fmt}",
                f"Cinder limits",
                labels=labels
            )
            for limit in limits:
                metric = limit[klimit]
                data = [
                    self.name,
                    limit["project_id"],
                    limit["project_name"],
                ]
                limits_metrics.add_metric(data, metric)

            yield limits_metrics

    def service_status(self):
        log.debug(f"Get collect of services: {self.name}")
        # Get services from cache file
        services = read_dump_data_from_file(
            dump_file=self._file_dump,
            item="services"
        )
        labels = [
            "stack",
            "binary",
            "host",
            "status",
            "availability_zone",
        ]
        services_metrics = GaugeMetricFamily(
            "cinder_service_status",
            "Cinder service status",
            labels=labels
        )
        for service in services:
            metric = 1 if service["state"] == "up" else 0
            data = [
                self.name,
                service["binary"],
                service["host"],
                service["status"],
                service["zone"],
            ]
            services_metrics.add_metric(data, metric)

        yield services_metrics

    def volume_size(self):
        log.debug(f"Get collect of volumes: {self.name}")
        # Get projects from cache file
        projects = read_dump_data_from_file(
            dump_file=self._file_dump,
            item="projects"
        )
        # Get volumes from cache file
        volumes = read_dump_data_from_file(
            dump_file=self._file_dump,
            item="volumes"
        )
        labels = [
            "stack",
            "id",
            "name",
            "created_at",
            "host",
            "project_id", 
            "project_name", 
            "volume_type",
            "availability_zone",
            "status",
            "attachments"
        ]

        volumes_metrics = GaugeMetricFamily(
            "cinder_volumes_size",
            "Cinder volumes information",
            labels=labels
        )

        for volume in volumes:
            metric = float(volume["size"])
            data = [
                self.name,
                volume["id"],
                volume["name"],
                volume["created_at"],
                volume["host"],
                volume["project_id"],
                projects.get(volume["project_id"], ""),
                volume["volume_type"],
                volume["availability_zone"],
                volume["status"],
                self._get_attachments(volume["attachments"]),
            ]
            volumes_metrics.add_metric(data, metric)

        yield volumes_metrics

    def collect_status(self):
        # Get collect status from cache file
        self._collect_state = bool(int(read_dump_data_from_file(
            dump_file=self._file_dump,
            item="collect"
        )))
        collect_metric = GaugeMetricFamily(
            "cinder_collect_status",
            "Cinder collect Status",
            labels=["stack"]
        )
        collect_metric.add_metric([self.name], int(self._collect_state))
        return collect_metric

    def collect(self):
        collect_metric = self.collect_status()

        if self._collect_state:
            yield from self.volume_size()
            yield from self.service_status()
            yield from self.limits()

        yield collect_metric
