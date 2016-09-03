import json

import prism
import prism.settings
import prism.helpers

from prism.api.view import BaseView, subroute


class DashboardView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/home', title='Dashboard',
                                menu={'id': 'dashboard', 'icon': 'home', 'order': 0})

    def get(self, request):
        return ('dashboard.html', {'widgets': prism.get_plugin('dashboard').get_widgets()})

    @subroute('/edit')
    def edit_get(self, request):
        return ('dashboard_edit.html', {'widgets': prism.get_plugin('dashboard').get_widgets(all=True)})

    @subroute('/edit')
    def edit_post(self, request):
        prism_dashboard = prism.get_plugin('dashboard')

        action = request.form['action']
        if action == 'show' or action == 'hide':
            widget_id = request.form['id']
            if action == 'show':
                prism_dashboard._widgets[widget_id]['shown'] = True
            else:
                prism_dashboard._widgets[widget_id]['shown'] = False
        elif action == 'order':
            data = request.form['data']

            for pack in data.split(','):
                if pack == '':
                    continue
                pack = pack.split('=')
                prism_dashboard._widgets[pack[0]]['order'] = int(pack[1])

        prism_dashboard.save_widgets()
        return '1'

class PluginListView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/plugins/list', title='Installed Plugins',
                                menu={'id': 'plugins.list', 'icon': 'square', 'order': 0,
                                        'parent': {'id': 'plugins', 'text': 'Plugins', 'icon': 'cubes', 'order': 1}})

    def get(self, request):
        return ('plugins/list.html', {'plugins': prism.plugin_manager().get_sorted_plugins()})

    def post(self, request):
        plugin_id = request.form['id']
        plugin = prism.get_plugin(plugin_id)

        action = request.form['action']
        if plugin is not None and action is not None:
            if action == 'get_settings':
                options = {}
                for option_id, option in plugin.settings.options.items():
                    options[option_id] = option
                    options[option_id]['locale'] = prism.helpers.locale_(plugin_id, 'setting.' + option_id)
                return plugin.settings.options
            elif action == 'set_settings':
                settings = json.loads(request.form['settings'])
                for setting, value in settings.items():
                    plugin.settings[setting] = value
                return ''
            elif action == 'enable':
                if plugin_id not in prism.settings.PRISM_CONFIG['enabled_plugins']:
                    prism.settings.PRISM_CONFIG['enabled_plugins'].append(plugin_id)
            elif action == 'disable':
                if plugin_id in prism.settings.PRISM_CONFIG['enabled_plugins']:
                    prism.settings.PRISM_CONFIG['enabled_plugins'].remove(plugin_id)
            return ('core.RestartView', {'return_url': 'dashboard.PluginListView'})
        return ('dashboard.PluginListView')

class PluginInstallView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/plugins/install', title='Install Plugins',
                                menu={'id': 'plugins.install', 'icon': 'cube', 'order': 1})

    def get(self, request):
        return ('plugins/install.html')
