from api import BasePlugin

class SystemPlugin(BasePlugin):
	def __init__(self):
		BasePlugin.__init__(self,
					plugin_id = 'prism_system',
					name = 'System',
					version = [ 1, 0, 0, 'indev' ],
					description = 'Basic system management.',
					author = 'Stumblinbear',
					homepage = 'http://prismcp.org/',

					dependencies = [ ('library', 'python-crontab') ],

					icon = 'television', order = 1)

from .views import *
from .widgets import *
