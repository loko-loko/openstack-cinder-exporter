# Cinder Exporter

## How Use

### Starting

Start container with clouds config file as a volume :

```bash
CLOUD_CONFIG="$(pwd)/config/clouds.yaml"
HOST_PORT=8888

$ docker run -d --name cinder_exporter -p ${HOST_PORT}:8000 -v "${CLOUD_CONFIG}:/config/clouds.yaml" cinder-exporter:v1.0
```

You can also set `DEBUG` environment variable to `1` for activate debug mode `-e DEBUG=1`.

```
$ docker logs cinder_exporter
exec: python -m cinder_exporter --cloud-config /config/clouds.yaml --port 8000
2019/11/23 21:38:19  INFO    - Prometheus web server started: 657b9aea6157:8000
2019/11/23 21:38:19  INFO    - Cinder exporter start:openstack_dev (PID:6) ..
2019/11/23 21:38:20  INFO    - Exporting completed
```

When exporting is done, you can see metrics on host exposed port :

```
$ curl 127.0.0.1:8888
[...]
# TYPE cinder_volumes_info_size gauge
cinder_volumes_info_size{
    account_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    availability_zone="nova",
    created_at="2019-11-18T00:35:05.000000",
    host="openstack@lvmdriver-1#lvmdriver-1",
    id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    metadata="",
    name="vol_2",
    project_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    status="available",
    volume_type="lvmdriver-1"
} 1.0
cinder_volumes_info_size{
    account_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    availability_zone="nova",
    created_at="2019-11-17T21:41:36.000000",
    host="openstack@lvmdriver-1#lvmdriver-1",
    id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    metadata="key=value",
    name="vol",
    project_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    status="available",
    volume_type="lvmdriver-1"
} 1.0
```
