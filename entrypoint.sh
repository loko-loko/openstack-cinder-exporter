ARG_DEBUG=""
CLOUDS_CONFIG="/config/clouds.yaml"

if [[ ! -e $CLOUDS_CONFIG ]]; then
    echo "<!> Clouds config file missing: $CLOUDS_CONFIG"
    exit 1
fi

[[ $DEBUG == 1 ]] && ARG_DEBUG="--debug"

set - "--cloud-config $CLOUDS_CONFIG" "--port 8000" "$ARG_DEBUG"

COMMAND="python -m cinder_exporter $@"

echo "exec: $COMMAND"
$COMMAND
