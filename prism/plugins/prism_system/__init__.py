from api import BasePlugin

from .views import *
from .widgets import *


class SystemPlugin(BasePlugin):
	def __init__(self):
		BasePlugin.__init__(self, order=1)
