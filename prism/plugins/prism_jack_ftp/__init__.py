import prism
from prism.api.plugin import BasePlugin

from prism_jack import SiteTab

class JackFTPPlugin(BasePlugin):
    def init(self, prism_state):
        from prism_jack import JackPlugin
        JackPlugin.get().register_tab(FTPTab())

class FTPTab(SiteTab):
    def __init__(self):
        SiteTab.__init__(self, 'FTP')

    def render(self):
        pass

    def post(self):
        pass
