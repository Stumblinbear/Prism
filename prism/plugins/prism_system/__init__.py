from api import BasePlugin

class SystemPlugin(BasePlugin):
	def __init__(self):
		BasePlugin.__init__(self, order = 1)

from .views import *
from .widgets import *
