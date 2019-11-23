from prometheus_client.core import GaugeMetricFamily, InfoMetricFamily
from openstack import connection
from loguru import logger

from cinder_exporter.common import format_project_id

class CinderCollector:

    def __init__(self, name, auth):
        self.name = name
        self._client = self._get_client(auth)
    
    def _get_client(self, auth):
        logger.debug(f"Get openstack client: {self.name}")
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
    
    @staticmethod
    def _get_volume_data(vdata, labels):
        data = {}
        for label in labels:
            data[label] = str(vdata.get(label))
            
        data["account_id"] = format_project_id(data["project_id"])
        
        return [data[k] for k in sorted(data.keys())]
        
    def volume_size(self):
        logger.debug(f"Get collect of volume size: {self.name}")
        volumes = self._client.block_storage.volumes(all_projects=True)
        labels = sorted([
            "id",
            "name",
            "created_at",
            "host",
            "project_id", 
            "volume_type",
            "availability_zone",
            "status",
            "account_id",
            "metadata"
        ])

        volumes_metrics = GaugeMetricFamily(
            "cinder_volumes_info_size",
            "Cinder volumes information",
            labels=labels
        )
 
        for volume in volumes:
            metric = float(volume["size"])
            data = self._get_volume_data(volume, labels)
            
            volumes_metrics.add_metric(data, metric)

        yield volumes_metrics 

    def collect(self):
        yield from self.volume_size()
