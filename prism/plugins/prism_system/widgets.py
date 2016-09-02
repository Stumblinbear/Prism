import os
import platform
import time

import psutil

import prism.settings
import prism.helpers
from prism.memorize import memorize

from prism_dashboard import Widget


class UsageCPUWidget(Widget):
	def __init__(self):
		Widget.__init__(self, 'usage.cpu', size=1)

	def render(self):
		return ('widget/usage.cpu.html', {'cpu': self.get_cpu()})

	@memorize(10)
	def get_cpu(self):
		return int(psutil.cpu_percent())

class UsageRAMWidget(Widget):
	def __init__(self):
		Widget.__init__(self, 'usage.ram', size=1)

	def render(self):
		return ('widget/usage.ram.html', {'ram': self.get_memory()})

	@memorize(10)
	def get_memory(self):
		return int(psutil.virtual_memory()[2])

class UsageDiskWidget(Widget):
	def __init__(self):
		Widget.__init__(self, 'usage.disk', size=1)

	def render(self):
		return ('widget/usage.disk.html', {'disk': self.get_disk()})

	@memorize(60)
	def get_disk(self):
		return int(psutil.disk_usage('/')[3])

class UsageNetworkWidget(Widget):
	def __init__(self):
		Widget.__init__(self, 'usage.network', size=1)

	def render(self):
		netusage = prism.helpers.convert_bytes(self.get_network())
		return ('widget/usage.network.html', {'network': netusage[0], 'network_type': netusage[1]})

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
		Widget.__init__(self, 'info', size=2)

	def render(self):
		return ('widget/info.html',
								{
									'os': '%s %s (%s)' % (platform.system(), platform.release(), platform.architecture()[0]),
									'hostname': platform.node(),
									'address': prism.settings.PRISM_CONFIG['host'],
									'uptime': self.get_uptime()
								})

	@memorize(5)
	def get_uptime(self):
		from datetime import timedelta

		with open('/proc/uptime', 'r') as f:
			uptime_seconds = float(f.readline().split()[0])
			uptime_string = str(timedelta(seconds=uptime_seconds))

		return uptime_string

class HardwareWidget(Widget):
	def __init__(self):
		Widget.__init__(self, 'hardware', size=2)

	def render(self):
		return ('widget/hardware.html',
								{
									'disk': self.get_total_disk(),
									'processor': platform.processor(),
									'memory': self.get_total_memory(),
									'swap': self.get_total_swap()
								})

	@memorize(60)
	def get_total_disk(self):
		return psutil.disk_usage('/')[0]

	@memorize(60)
	def get_total_memory(self):
		return psutil.virtual_memory()[0]

	@memorize(60)
	def get_total_swap(self):
		return psutil.swap_memory()[0]
