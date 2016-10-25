import json
import os
import nginx
from flask import request
from flask_menu import current_menu

import prism
from prism.config import JSONConfig
from prism.api.plugin import BasePlugin


class JackPlugin(BasePlugin):
    def init(self, prism_state):
        self.default_configs = []
        self.site_tabs = []

        # Search the plugins for DefaultConfig classes
        for plugin_id, plugin, name, obj in prism_state.plugin_manager.find_classes(SiteTypeConfig):
            self.default_configs.append(obj())

        # Search the plugins for SiteTab classes
        for plugin_id, plugin, name, obj in prism_state.plugin_manager.find_classes(SiteTab):
            self.site_tabs.append(obj())

        self.nginx = NginxManager(prism_state, self)

    def get_default_config(self, type_id):
        for config in self.default_configs:
            if config.type_id == type_id:
                return config
        return None

# Manages Nginx sites and jack site configurations
class NginxManager:
    def __init__(self, prism_state, jack_plugin):
        self._jack_plugin = jack_plugin

        # The 'sites' folder within jack's config folder
        # This is where site json files are saved
        self.config_folder = os.path.join(self._jack_plugin.data_folder, 'sites')
        if not os.path.exists(self.config_folder):
            os.makedirs(self.config_folder)

        # The location that we should export the generated Nginx configurations
        self.config_location = self._jack_plugin.config('nginx-site-loc', '/etc/nginx/conf.d/')
        # The location that we store website files and logs
        self.site_files_location = self._jack_plugin.config('site-files-loc', '/var/www/')

        # Load all the json configs located in jack's sites folder
        self.configs = {}
        with prism_state.flask_app().app_context():
            for i, file_name in enumerate(os.listdir(self.config_folder)):
                site_config = JSONConfig(self.config_folder, file_name)
                self.configs[file_name[:-5]] = site_config
                self.create_menu_item(item, site_config['id'], site_config['uuid'], i + 1)

        # On startup, replace all the nginx configurations with the json configs
        self.rebuild_sites()

    def create_menu_item(self, item, site_id, uuid, order):
        """ Creates the site's menu item """
        def site_overview_construct():
            """ Generates a function which wraps the menu item's argument variable """
            def wrapper():
                return {'site_uuid': site_uuid}
            return wrapper

        # Generate the menu item for the website
        item = current_menu.submenu(self._jack_plugin._endpoint + '.' + uuid)
        item.register(self._jack_plugin._endpoint + '.JackSiteOverviewView', site_id, order=order,
                        endpoint_arguments_constructor=site_overview_construct(uuid),
                        active_when=lambda self: request.path.endswith(uuid))

    def create_site(self, default_config, site_id, options):
        """ Creates the site, generates the config, and adds it to the menu """
        site_uuid = prism.generate_random_string(32)
        site_config = JSONConfig(self.config_folder, site_uuid + '.json')

        site_config['uuid'] = site_uuid
        site_config['id'] = site_id
        site_config['type'] = default_config.type_id

        site_config['listen'] = ['80', '[::]:80']
        site_config['locations'] = {}

        # Let the default nginx configuration input their values
        default_config.generate(site_config, *options)
        site_config.save()

        self.configs[site_config['uuid']] = site_config

        self.create_menu_item(item, site_config['id'], site_config['uuid'], len(self.configs))

        return site_config

    def delete_site(self, site_uuid):
        """ Removes configs from nginx and jack, folders
        created for the site, and the menu item """
        del prism.flask_app().extensions['menu']._child_entries[self._jack_plugin._endpoint]._child_entries[site_uuid]
        self.configs[site_uuid].delete()
        del self.configs[site_uuid]

        # Remove the jack configuration file
        os.remove(os.path.join(self.config_location, site_uuid + '.conf'))
        # Remove the site folder
        os.remove(os.path.join(self.site_files_location, uuid))

        # Gets the default configuration the site used
        # and runs its delete method for cleanup
        default_config = JackPlugin.get().get_default_config(site_config['type'])
        default_config.delete(site_config)

        # Regen nginx configuration files
        self.rebuild_sites()

    def rebuild_sites(self):
        """ Turns jack's site json files into useable nginx configuration files """
        for uuid, config in self.configs.items():
            maintenance_mode = 'maintenance' in config and config['maintenance']

            nginx_config = nginx.Conf()

            # Add some comments so anyone who looks in the nginx config
            # knows what's going on
            nginx_config.add(nginx.Comment('Generated by Prism CP. Any changes will be overwritten!'))
            nginx_config.add(nginx.Comment('Site ID: %s' % config['id']))

            server_block = nginx.Server()

            if 'listen' in config:
                for port in config['listen']:
                    server_block.add(nginx.Key('listen', port))
            if 'hostname' in config:
                server_block.add(nginx.Key('server_name', config['hostname']))

            site_folder = os.path.join(self.site_files_location, uuid)
            root_folder = os.path.join(site_folder, 'public_html')
            if not os.path.exists(root_folder):
                os.makedirs(root_folder)

            # Sets the root and logs to the site's folder
            server_block.add(nginx.Key('root', root_folder))
            server_block.add(nginx.Key('access_log', os.path.join(site_folder, 'access.log')))
            server_block.add(nginx.Key('error_log', os.path.join(site_folder, 'error.log')))

            if 'index' in config:
                server_block.add(nginx.Key('index', config['index']))

            # If the site is in maintenance mode, redirect everything to 503
            if maintenance_mode:
                server_block.add(nginx.Location('/',
                                    nginx.Key('return', 503)))
            else:
                for path, items in config['locations'].items():
                    location_items = []
                    for item, content in items.items():
                        if isinstance(content, tuple) or isinstance(content, list):
                            for c in content:
                                location_items.append(nginx.Key(item, c))
                        else:
                            location_items.append(nginx.Key(item, content))
                    server_block.add(nginx.Location(path, *location_items))

            # Error page blocks
            jack_static = os.path.join(self._jack_plugin.data_folder, 'static/')
            server_block.add(nginx.Key('error_page', '404 /error/404.html'))
            server_block.add(nginx.Location('= /error/404.html',
                        nginx.Key('root', jack_static),
                        nginx.Key('internal', '')))
            server_block.add(nginx.Key('error_page', '500 /error/500.html'))
            server_block.add(nginx.Location('= /error/500.html',
                        nginx.Key('root', jack_static),
                        nginx.Key('internal', '')))
            server_block.add(nginx.Key('error_page', '503 /error/503.html'))
            server_block.add(nginx.Location('= /error/503.html',
                        nginx.Key('root', jack_static),
                        nginx.Key('internal', '')))

            nginx_config.add(server_block)

            # Dump to nginx's config location
            nginx.dumpf(nginx_config, os.path.join(self.config_location, config['uuid'] + '.conf'))

        # Reload nginx so it picks up the changes
        prism.os_command('systemctl reload nginx.service')

# Jack automatically searches for this class within pugin files
# and adds them to possible default configurations
class SiteTypeConfig:
    def __init__(self, type_id, title, description, options=[]):
        self.disabled = False
        self.type_id = type_id
        self.title = title
        self.description = description

        # This defines the fields required when the user is creating the site
        self.options = [('site_id', 'Site ID', 'Example Site')] + options

    def generate(self, site_config, site_id):
        """ This is run when the user creates a site with this type;
        The fields are site_config followed by all field id's
        defined in self.options """
        pass

    def delete(self, site_config):
        """ This is run when the user deletes their site. Do some cleanup
        work if need be """
        pass

# Jack automatically searches for this class within pugin files
# and adds them to all site's tabs
class SiteTab:
    def __init__(self, title):
        self.uuid = prism.generate_random_string(8)
        self.title = title

    def render(self):
        """ Render the tab in the site's page """
        pass

    def post(self, request):
        """ Called when the user submits the form on the tab's page """
        pass


from .views import *
from .widgets import *
from .site_configs import *