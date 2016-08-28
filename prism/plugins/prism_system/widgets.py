import os
import platform
import time

import psutil

import settings
import helpers
from memorize import memorize

from prism_dashboard import Widget


class UsageWidget(Widget):
	def render(self):
		netusage = helpers.convert_bytes(get_network())
		return render_template('widget/usage.html',
								cpu=get_cpu(),
								ram=get_memory(),
								disk=get_disk(),
								network=netusage[0],
								network_type=netusage[1])

	@memorize(10)
	def get_cpu():
		return int(psutil.cpu_percent())

	@memorize(10)
	def get_memory():
		return int(psutil.virtual_memory()[2])

	@memorize(60)
	def get_disk():
		return int(psutil.disk_usage('/')[3])

	_last_check = 0
	_previous_network = 0
	@memorize(10)
	def get_network():
		usage = 0

		current_network = psutil.net_io_counters()[0]

		if self._previous_network == 0:
			# Check, wait a second, then check again to get a base value.
			self._previous_network = current_network
			time.sleep(2)
			current_network = psutil.net_io_counters()[0]

		time_since = time.time() - self._last_check
		usage = (current_network - self._previous_network)

		self._previous_network = current_network
		self._last_check = time.time()

		return usage

class UsageWidget(Widget):
	def render(self):
		return render_template('widget/info.html',
								os='%s %s (%s)' % (platform.system(), platform.release(), platform.architecture()[0]),
								hostname=platform.node(),
								address=settings.PRISM_CONFIG['host'],
								uptime=get_uptime(),
								disk=get_total_disk(),
								processor=platform.processor(),
								memory=get_total_memory(),
								swap=get_total_swap())

	@memorize(5)
	def get_uptime():
		from datetime import timedelta

		with open('/proc/uptime', 'r') as f:
			uptime_seconds = float(f.readline().split()[0])
			uptime_string = str(timedelta(seconds = uptime_seconds))

		return uptime_string

	@memorize(60)
	def get_total_disk():
		return psutil.disk_usage('/')[0]

	@memorize(60)
	def get_total_memory():
		return psutil.virtual_memory()[0]

	@memorize(60)
	def get_total_swap():
		return psutil.swap_memory()[0]
