import os
import nginx
from flask_menu import current_menu

from prism.api.plugin import BasePlugin


class JackPlugin(BasePlugin):
    def init(self, prism_state):
        self._default_configs = [PHPConfig(), GUnicornConfig(), ReverseProxyConfig(), AdvancedConfig()]

        self.nginx_configs = []
        for file_id in os.listdir(self.config('sites-loc', '/etc/nginx/conf.d/')):
            self.nginx_configs.append(file_id[:-5])
        self.cached_config = {}

        with prism_state.flask_app().app_context():
            for file_id in self.nginx_configs:
                item = current_menu.submenu(self._endpoint + '.' + file_id.replace('.', '_').replace(' ', '_'))
                item.register(self._endpoint + '.JackSiteOverviewView', file_id, 1,
                                endpoint_arguments_constructor=self.site_overview_construct(file_id))

    def site_overview_construct(self, file_id):
        def wrapper():
            return {'site_id': file_id}
        return wrapper

    def clear_cache(self):
        self.cached_config = {}

    def get_config(self, site_id):
        if site_id in self.cached_config:
            return self.cached_config[site_id]
        conf_path = self.get_config_loc(site_id)
        if not os.path.exists(conf_path):
            return None
        self.cached_config[site_id] = nginx.loadf(conf_path)
        return self.cached_config[site_id]

    def get_config_loc(self, site_id):
        return os.path.join(self.config('sites-loc', '/etc/nginx/conf.d/'), site_id + '.conf')

    def add_default_config(self, inst):
        self._default_configs.append(inst)

    def get_default_configs(self):
        return self._default_configs

    def get_default_config(self, type_id):
        for config in self.get_default_configs():
            if config.type_id == type_id:
                return config
        return None


from .views import *
from .widgets import *
from .site_configs import *
