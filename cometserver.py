#!/usr/bin/env python3

import os
import time
import sys
import json
import urllib.request
import urllib.parse

try:
	COLLECTD_HOSTNAME = os.environ["COLLECTD_HOSTNAME"]
	COLLECTD_INTERVAL = int(float(os.environ["COLLECTD_INTERVAL"]))
	COMETSERVER_URL   = sys.argv[1]
	COMETSERVER_USER  = sys.argv[2]
	COMETSERVER_PASS  = sys.argv[3]
	NAMESPACE         = sys.argv[4]

except Exception:
	print("Usage:\nCOLLECTD_HOSTNAME=localhost COLLECTD_INTERVAL=60 ./cometserver.py COMETSERVER_URL USER PASS NAMESPACE")
	sys.exit(1)

class CometServer(object):
	def __init__(self, url, adminuser, adminpass):
		self.url = url
		self.adminuser = adminuser
		self.adminpass = adminpass

	def AdminListUsers(self):
		"""List all usernames on the Comet Server"""
		return self._request("api/v1/admin/list-users", {})

	def AdminDispatcherListActive(self):
		return self._request("api/v1/admin/dispatcher/list-active", {})

	def AdminGetJobsForDateRange(self, Start: int, End: int):
		return self._request("api/v1/admin/get-jobs-for-date-range", {"Start": Start, "End": End})

	def AdminMetaVersion(self):
		return self._request("api/v1/admin/meta/version", {})

	def _request(self, endpoint, extraparams):
		"""Make API request to Comet Server and parse response JSON"""
		apiRequest = urllib.request.Request(
			url = self.url + endpoint,
			data = urllib.parse.urlencode({
				"Username": self.adminuser,
				"AuthType": "Password",
				"Password": self.adminpass,
				**extraparams
			}).encode('utf-8')
		)

		ret = None
		with urllib.request.urlopen(apiRequest) as apiResponse:
			ret = json.loads( apiResponse.read() )

		return ret

def get_metrics(srv: CometServer):
	start_time = time.time()

	userList = srv.AdminListUsers()
	liveconns = srv.AdminDispatcherListActive()
	jobs_48h = srv.AdminGetJobsForDateRange(int(start_time) - (86400 * 2), int(start_time) + 180)
	meta = srv.AdminMetaVersion()

	end_time = time.time()

	elapsed_msecs = int((end_time - start_time) * 1000)

	liveconns_on_current_version = 0
	for liveconn_id in liveconns:
		if liveconns[liveconn_id]['ReportedVersion'] == meta['Version']:
			liveconns_on_current_version += 1

	# Time since last successful Server Self-Backup
	time_since_last_successful_selfbackup = 365 * 86400 # no self-backup runtime found = report as 1 year
	for selfbackup_info in meta['SelfBackup']:
		if selfbackup_info['LastRunSuccess']:
			time_since_last_successful_selfbackup = end_time - selfbackup_info['LastRunEnd']

	# The Comet Server version, expressed as a number
	server_version_numeric = 0
	version_number_parts = meta['Version'].split('.')
	if len(version_number_parts) == 3:
		server_version_numeric = (int(version_number_parts[0]) * 10000) + (int(version_number_parts[1]) * 100) + int(version_number_parts[2])

	return {
		"comet_user_count": len(userList),
		"comet_liveconn_count": len(liveconns),
		"comet_liveconn_currentversion_count": liveconns_on_current_version,
		"comet_total_jobs_48h": len(jobs_48h),
		"comet_uptime": int(start_time - meta["ServerStartTime"]),
		"comet_selfbackup_age": int(time_since_last_successful_selfbackup),
		"comet_version_number": server_version_numeric,
		"comet_total_api_time": elapsed_msecs
	}

def main():
	srv = CometServer(COMETSERVER_URL, COMETSERVER_USER, COMETSERVER_PASS)

	while True:
		metrics = get_metrics(srv)
		for key in metrics:
			print(f"PUTVAL \"{COLLECTD_HOSTNAME}/{NAMESPACE}/{key}\" interval={COLLECTD_INTERVAL} N:{metrics[key]}")

		sys.stdout.flush()
		time.sleep(COLLECTD_INTERVAL)

main()
