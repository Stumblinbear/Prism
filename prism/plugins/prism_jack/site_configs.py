import nginx

import prism

from . import JackPlugin

class DefaultConfig:
    def __init__(self, type_id, description, options=[]):
        self.disabled = False
        self.type_id = type_id
        self.description = description

        self.options = [('site_id', 'Site ID')] + options

    def generate(self, site_config, site_id):
        pass

    def delete(self, site_config):
        pass

class PHPConfig(DefaultConfig):
    def __init__(self):
        DefaultConfig.__init__(self, 'php', 'Use this option if you wish to set up a website created using PHP.', [('url_endpoint', 'URL Endpoint', 'example.com')])
        self.disabled = True

    def generate(self, site_config, site_id, url_endpoint):
        if not request.form['url_endpoint']:
            return 'Must specify a URL endpoint.'
        site_config['url_endpoint'] = request.form['url_endpoint']

    def delete(self, site_config):
        pass

    def post(self, request, site_config):
        pass

class GUnicornConfig(DefaultConfig):
    def __init__(self):
        DefaultConfig.__init__(self, 'gunicorn', 'Use this option if you wish to set up a website created using Python scripts.', [('url_endpoint', 'URL Endpoint', 'example.com')])
        self.disabled = True

    def generate(self, site_config, site_id, url_endpoint):
        if not request.form['url_endpoint']:
            return 'Must specify a URL endpoint.'
        site_config['url_endpoint'] = request.form['url_endpoint']

    def delete(self, site_config):
        pass

    def post(self, request, site_config):
        pass

class ReverseProxyConfig(DefaultConfig):
    def __init__(self):
        DefaultConfig.__init__(self, 'reverseproxy', 'Set up a website as a reverse proxy.', [('url_endpoint', 'URL Endpoint', 'example.com'), ('proxy_to', 'Proxy To', 'http://example.com/')])

    def generate(self, site_config, site_id, url_endpoint, proxy_to):
        site_config['url_endpoint'] = url_endpoint
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

    def delete(self, site_config):
        pass

    def post(self, request, site_config):
        if not request.form['url_endpoint']:
            return 'Must specify a URL endpoint.'
        if not request.form['proxy_to']:
            return 'Must specify a site or IP to Proxy To.'
        site_config['url_endpoint'] = request.form['url_endpoint']
        site_config['locations']['/']['proxy_pass'] = request.form['proxy_to']

class AdvancedConfig(DefaultConfig):
    def __init__(self):
        DefaultConfig.__init__(self, 'nginx', 'Gives complete access to all configuration items.')

    def delete(self, site_config):
        pass

    def post(self, request, site_config):
        pass
