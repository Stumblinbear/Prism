from api import BasePlugin

class CorePlugin(BasePlugin):
	def __init__(self):
		BasePlugin.__init__(self,
					plugin_id = 'prism_core',
					name = 'Prism Core',
					version = [ 1, 0, 0, 'indev' ],
					description = 'Contains a few essential Prism views and functions.',
					author = 'Stumblinbear',
					homepage = 'http://prismcp.org/')

	def init(self, prism):
		def url_restart(return_url=None):
			return ('core.restart', { return_url: return_url })
		prism.flask().jinja_env.globals["url_restart"] = url_restart

from .views import *
