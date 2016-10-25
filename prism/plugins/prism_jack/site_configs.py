import nginx

import prism

from . import SiteTypeConfig

class ReverseProxyConfig(SiteTypeConfig):
    def __init__(self):
        SiteTypeConfig.__init__(self, 'reverseproxy', 'Reverse Proxy', 'Set up a website as a reverse proxy.', [('hostname', 'Hostname', 'example.com'), ('proxy_to', 'Proxy To', 'http://example.com/')])

    def generate(self, site_config, site_id, hostname, proxy_to):
        site_config['hostname'] = hostname
        site_config['locations']['/'] = {
                            'proxy_pass': proxy_to,
                            'proxy_redirect': 'off',

                            'proxy_set_header': (
                                            'Host $host',
                                            'X-Real-IP $remote_addr',
                                            'X-Forwarded-For $proxy_add_x_forwarded_for'),

                            'client_max_body_size': '10m',
                            'client_body_buffer_size': '128k',

                            'proxy_connect_timeout': '90',
                            'proxy_send_timeout': '90',
                            'proxy_read_timeout': '90',

                            'proxy_buffer_size': '4k',
                            'proxy_buffers': '4 32k',
                            'proxy_busy_buffers_size': '64k',
                            'proxy_temp_file_write_size': '64k'
                        }

    def post(self, request, site_config):
        if not request.form['hostname']:
            return 'Must specify a hostname.'
        if not request.form['proxy_to']:
            return 'Must specify a site or IP to Proxy To.'
        site_config['hostname'] = request.form['hostname']
        site_config['locations']['/']['proxy_pass'] = request.form['proxy_to']

    def delete(self, site_config):
        pass

class AdvancedConfig(SiteTypeConfig):
    def __init__(self):
        SiteTypeConfig.__init__(self, 'nginx', 'Advanced', 'Gives complete access to all configuration items.', [('hostname', 'Hostname', 'example.com')])

    def generate(self, site_config, site_id, hostname):
        site_config['hostname'] = hostname
        site_config['index'] = 'index.html'

    def post(self, request, site_config):
        site_config['hostname'] = request.form['hostname']
        site_config['hostname'] = hostname

    def delete(self, site_config):
        pass

class DirectConfig(SiteTypeConfig):
    def __init__(self):
        SiteTypeConfig.__init__(self, 'direct', 'Direct Configuration', 'No hand-holding. Gives direct access to configuration files.')
        self.disabled = True

    def post(self, request, site_config):
        pass

    def delete(self, site_config):
        pass
