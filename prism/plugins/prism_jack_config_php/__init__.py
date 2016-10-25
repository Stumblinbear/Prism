import prism
from prism.api.plugin import BasePlugin

from prism_jack import SiteTypeConfig

class JackPHPConfigPlugin(BasePlugin):
    pass

class PHPConfig(SiteTypeConfig):
    def __init__(self):
        SiteTypeConfig.__init__(self, 'php', 'PHP', 'Use this option if you wish to set up a website created using PHP.', [('hostname', 'Hostname', 'example.com')])
        self.disabled = True

    def generate(self, site_config, site_id, hostname):
        if not request.form['hostname']:
            return 'Must specify a hostname.'
        site_config['hostname'] = request.form['hostname']

    def delete(self, site_config):
        pass

    def post(self, request, site_config):
        pass
