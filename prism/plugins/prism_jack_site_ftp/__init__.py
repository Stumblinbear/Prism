import prism
from prism.api.plugin import BasePlugin

from prism_jack import SiteTab

class JackFTPPlugin(BasePlugin):
    pass

class FTPTab(SiteTab):
    def __init__(self):
        SiteTab.__init__(self, 'FTP')

    def render(self):
        return ('ff')

    def post(self, request):
        pass
