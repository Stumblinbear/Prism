import prism
from prism.api.plugin import BasePlugin

from prism_jack import SiteTypeConfig

class JackGUnicornConfigPlugin(BasePlugin):
    pass

class GUnicornConfig(SiteTypeConfig):
    def __init__(self):
        SiteTypeConfig.__init__(self, 'gunicorn', 'GUnicorn', 'Use this option if you wish to set up a website created using Python scripts.', [('hostname', 'Hostname', 'example.com')])
        self.disabled = True

    def generate(self, site_config, site_id, hostname):
        if not request.form['hostname']:
            return 'Must specify a hostname.'
        site_config['hostname'] = request.form['hostname']

    def delete(self, site_config):
        pass

    def post(self, request, site_config):
        pass
