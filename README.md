# Collectd Exporter for Comet Server

This is a script for [collectd](https://collectd.org/) to export metrics from a running Comet Server instance over the Comet Server HTTP API. It runs under the [Exec plugin](https://collectd.org/wiki/index.php/Plugin:Exec) and requires no additional Python library dependencies.

## Requirements

- Python 3.6 or later

## Installation instructions

1. Ensure in `/etc/collectd/collectd.conf` that the default TypesDB file is loaded:

```
TypesDB "/usr/share/collectd/types.db"
```

Without this, we would override the types instead of adding to them.

2. Add this content to `/etc/collectd/collectd.conf.d/cometserver.conf`:

```
TypesDB "/usr/local/comet-collectd-exporter/types.db"
LoadPlugin exec

<Plugin exec>
	Exec "nobody" "/usr/bin/python3" "/usr/local/comet-collectd-exporter/cometserver.py" "http://127.0.0.1:8060/" "admin" "admin" "cometserver-example"
</Plugin>
```

Then reload the `collectd` service.

## Generated metrics

|Metric                |Type  |Description
|----------------------|------|----
|`comet_user_count`    |Gauge |The total number of user accounts on the server
|`comet_liveconn_count`|Gauge |The total current number of live-connections from devices
|`comet_total_jobs_48h`|Gauge |The total number of jobs (started or running) within the last 48 hours
|`comet_uptime`        |Gauge |The uptime of the Comet Server, in seconds

## Debugging

Run collectd in the foreground:

```bash
collectd -f
```
