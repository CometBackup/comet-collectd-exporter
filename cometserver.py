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
	start_time = int(time.time())

	userList = srv.AdminListUsers()
	liveconns = srv.AdminDispatcherListActive()
	jobs_48h = srv.AdminGetJobsForDateRange(start_time - (86400 * 2), start_time + 180)
	meta = srv.AdminMetaVersion()

	return {
		"comet_user_count": len(userList),
		"comet_liveconn_count": len(liveconns),
		"comet_total_jobs_48h": len(jobs_48h),
		"comet_uptime": start_time - meta["ServerStartTime"]
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
