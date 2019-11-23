#!/bin/sh

set -e

CLOUDS_CONFIG="/config/clouds.yaml"

if [ ! -e "$CLOUDS_CONFIG" ]; then
    echo "<!> Clouds config file missing: $CLOUDS_CONFIG"
    exit 1
fi

set -- "--port 8000" "--cloud-config $CLOUDS_CONFIG"

[ "${DEBUG:-0}" -eq 1 ] && set -- "$@" "--debug"

COMMAND="python -m cinder_exporter $@"

echo "exec: $COMMAND"
exec $COMMAND
