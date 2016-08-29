import os
import platform
import time

import psutil

import prism.settings
import prism.helpers
from prism.memorize import memorize

from prism_dashboard import Widget


class UsageWidget(Widget):
	def __init__(self):
		Widget.__init__(self, 'usage')

	def render(self):
		netusage = prism.helpers._convert_bytes(self.get_network())
		return ('widget/usage.html',
								{
									'cpu': self.get_cpu(),
									'ram': self.get_memory(),
									'disk': self.get_disk(),
									'network': netusage[0],
									'network_type': netusage[1]
								})

	@memorize(10)
	def get_cpu(self):
		return int(psutil.cpu_percent())

	@memorize(10)
	def get_memory(self):
		return int(psutil.virtual_memory()[2])

	@memorize(60)
	def get_disk(self):
		return int(psutil.disk_usage('/')[3])

	_last_check = 0
	_previous_network = 0

	@memorize(10)
	def get_network(self):
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

class InfoWidget(Widget):
	def __init__(self):
		Widget.__init__(self, 'info')

	def render(self):
		return ('widget/info.html',
								{
									'os': '%s %s (%s)' % (platform.system(), platform.release(), platform.architecture()[0]),
									'hostname': platform.node(),
									'address': prism.settings.PRISM_CONFIG['host'],
									'uptime': self.get_uptime(),
									'disk': self.get_total_disk(),
									'processor': platform.processor(),
									'memory': self.get_total_memory(),
									'swap': self.get_total_swap()
								})

	@memorize(5)
	def get_uptime(self):
		from datetime import timedelta

		with open('/proc/uptime', 'r') as f:
			uptime_seconds = float(f.readline().split()[0])
			uptime_string = str(timedelta(seconds=uptime_seconds))

		return uptime_string

	@memorize(60)
	def get_total_disk(self):
		return psutil.disk_usage('/')[0]

	@memorize(60)
	def get_total_memory(self):
		return psutil.virtual_memory()[0]

	@memorize(60)
	def get_total_swap(self):
		return psutil.swap_memory()[0]
