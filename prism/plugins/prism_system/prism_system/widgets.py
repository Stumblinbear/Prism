from flask import render_template

# Dashboard plugins
import dashboard, os, platform, settings, time, helpers

def usage_widget():
	netusage = helpers.convert_bytes(get_network())
	return render_template('widget/usage.html',
								cpu=get_cpu(), ram=get_memory(), disk=get_disk(), network=netusage[0], network_type=netusage[1])
dashboard.get().add_widget('usage', usage_widget, order=0, default=True)

def info_widget():
	return render_template('widget/info.html',
								os='%s %s (%s)' % (platform.system(), platform.release(), platform.architecture()[0]),
								hostname=platform.node(),
								address=settings.PRISM_CONFIG['host'],
								uptime=get_uptime(),
								disk=get_total_disk(),
								processor=platform.processor(),
								memory=get_total_memory(),
								swap=get_total_swap())
dashboard.get().add_widget('system_info', info_widget)

import psutil
from memorize import memorize

_cpu = {}
@memorize(_cpu, 10)
def get_cpu():
	return int(psutil.cpu_percent())

_memory = {}
@memorize(_memory, 10)
def get_memory():
	return int(psutil.virtual_memory()[2])

_disk = {}
@memorize(_disk, 60)
def get_disk():
	return int(psutil.disk_usage('/')[3])

_network = {}
_last_check = 0
_previous_network = 0
@memorize(_network, 10)
def get_network():
	global _last_check, _previous_network
	
	usage = 0
	
	current_network = psutil.net_io_counters()[0]
	
	if _previous_network == 0:
		# Check, wait a second, then check again to get a base value.
		_previous_network = current_network
		time.sleep(2)
		current_network = psutil.net_io_counters()[0]
	
	time_since = time.time() - _last_check
	usage = (current_network - _previous_network)
	
	_previous_network = current_network
	_last_check = time.time()
	
	return usage

_uptime = {}
@memorize(_uptime, 5)
def get_uptime():
	from datetime import timedelta

	with open('/proc/uptime', 'r') as f:
		uptime_seconds = float(f.readline().split()[0])
		uptime_string = str(timedelta(seconds = uptime_seconds))
	
	return uptime_string

_total_disk = {}
@memorize(_total_disk, 60)
def get_total_disk():
	return psutil.disk_usage('/')[0]

_total_memory = {}
@memorize(_total_memory, 60)
def get_total_memory():
	return psutil.virtual_memory()[0]

_total_swap = {}
@memorize(_total_swap, 60)
def get_total_swap():
	return psutil.swap_memory()[0]