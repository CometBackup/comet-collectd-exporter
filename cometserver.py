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
	userList = srv.AdminListUsers()
	return {
		"comet_user_count": len(userList)
	}

def main():
	svr = CometServer(COMETSERVER_URL, COMETSERVER_USER, COMETSERVER_PASS)

	while True:
		metrics = get_metrics(svr)
		for key in metrics:
			print(f"PUTVAL \"{COLLECTD_HOSTNAME}/{NAMESPACE}/{key}\" interval={COLLECTD_INTERVAL} N:{metrics[key]}")

		sys.stdout.flush()
		time.sleep(COLLECTD_INTERVAL)

main()
