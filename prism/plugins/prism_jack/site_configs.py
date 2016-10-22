import nginx

import prism

from . import JackPlugin

class ConfigWrapper:
    def __init__(self, site_id, nginx_config):
        self.site_id = site_id
        self.nginx = nginx_config

        if isinstance(nginx_config.children[0], nginx.Comment):
            cmnt = nginx_config.children[0].comment
            if cmnt[:7] == 'config=':
                config = JackPlugin.get().get_default_config(cmnt[7:])
                if config is not None:
                    self.config = config
        if self.config is None:
            self.config = JackPlugin.get().get_default_config('nginx')

class DefaultConfig:
    def __init__(self, type_id, description, options=[]):
        self.disabled = False
        self.type_id = type_id
        self.description = description

        self.options = [('site_id', 'Site ID'), ('url_endpoint', 'URL Endpoint', 'example.com')] + options

class PHPConfig(DefaultConfig):
    def __init__(self):
        DefaultConfig.__init__(self, 'php', 'Use this option if you wish to set up a website created using PHP.')
        self.disabled = True

    def generate_config(self, nginx_config, site_id, url_endpoint):
        pass

    def post(self, request, nginx_config):
        pass

class GUnicornConfig(DefaultConfig):
    def __init__(self):
        DefaultConfig.__init__(self, 'gunicorn', 'Use this option if you wish to set up a website created using Python scripts. ')
        self.disabled = True

    def generate_config(self, nginx_config, site_id, url_endpoint):
        pass

    def post(self, request, nginx_config):
        pass

class ReverseProxyConfig(DefaultConfig):
    def __init__(self):
        DefaultConfig.__init__(self, 'reverseproxy', 'Set up a website as a reverse proxy.', [('proxy_to', 'Proxy To', 'http://example.com/')])

    def generate_config(self, nginx_config, site_id, url_endpoint, proxy_to):
        server_block = nginx.Server()
        server_block.add(
                        nginx.Key('listen', '80'),
                        nginx.Key('listen', '[::]:80'),
                        nginx.Key('server_name', url_endpoint),
                        nginx.Location('/',
                                nginx.Key('proxy_pass', proxy_to),
                                nginx.Key('proxy_redirect', 'off'),

                                nginx.Key('proxy_set_header', 'Host $host'),
                                nginx.Key('proxy_set_header', 'X-Real-IP $remote_addr'),
                                nginx.Key('proxy_set_header', 'X-Forwarded-For $proxy_add_x_forwarded_for'),

                                nginx.Key('client_max_body_size', '10m'),
                                nginx.Key('client_body_buffer_size', '128k'),

                                nginx.Key('proxy_connect_timeout', '90'),
                                nginx.Key('proxy_send_timeout', '90'),
                                nginx.Key('proxy_read_timeout', '90'),

                                nginx.Key('proxy_buffer_size', '4k'),
                                nginx.Key('proxy_buffers', '4 32k'),
                                nginx.Key('proxy_busy_buffers_size', '64k'),
                                nginx.Key('proxy_temp_file_write_size', '64k')
                            )
                    )
        nginx_config.add(server_block)
        return True

    def post(self, request, nginx_config):
        if not request.form['proxy_to']:
            return 'Must specify a site or IP to Proxy To.'
        nginx_config.server.locations[0].keys[0].value = request.form['proxy_to']

class AdvancedConfig(DefaultConfig):
    def __init__(self):
        DefaultConfig.__init__(self, 'nginx', 'Gives complete access to all configuration items.')
        self.disabled = True

    def generate_config(self, nginx_config, site_id, url_endpoint):
        pass

    def post(self, request, nginx_config):
        pass
