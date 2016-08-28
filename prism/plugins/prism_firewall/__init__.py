from api import BasePlugin

class FirewallPlugin(BasePlugin):
	def __init__(self):
		BasePlugin.__init__(self,
					plugin_id = 'prism_firewall',
					name = 'Firewall',
					version = [ 1, 0, 0, 'indev' ],
					description = 'Basic firewall management.',
					author = 'Stumblinbear',
					homepage = 'http://prismcp.org/',

					dependencies = [ ('library', 'netfilter'), ('binary', 'iptables'), ('binary', 'firewalld') ],

					icon = 'fire')

from .views import *
