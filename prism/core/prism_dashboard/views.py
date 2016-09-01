import prism
import prism.settings

from prism.api.view import BaseView, subroute


class DashboardView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/home',
                                title='Dashboard',
                                menu={'id': 'dashboard', 'icon': 'home', 'order': 0})

    def get(self, request):
        return ('dashboard.html', {'widgets': prism.get_plugin('prism_dashboard').get_widgets()})

    @subroute('/edit')
    def edit_get(self, request):
        return ('dashboard_edit.html', {'widgets': prism.get_plugin('prism_dashboard').get_widgets(all=True)})

    @subroute('/edit')
    def edit_post(self, request):
        prism_dashboard = prism.get_plugin('prism_dashboard')

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
        BaseView.__init__(self, endpoint='/plugins/list',
                                title='Installed Plugins',
                                menu={'id': 'plugins.list', 'icon': 'square', 'order': 0,
                                        'parent': {'id': 'plugins', 'text': 'Plugins', 'icon': 'cubes', 'order': 1}})

    def get(self, request):
        return ('plugins/list.html', {'plugins': prism.plugin_manager().get_sorted_plugins()})

    def post(self, request):
        id = request.form['id']
        action = request.form['action']
        if id is not None and action is not None:
            if action == 'enable':
                if id not in prism.settings.PRISM_CONFIG['enabled_plugins']:
                    prism.settings.PRISM_CONFIG['enabled_plugins'].append(id)
            elif action == 'disable':
                if id in prism.settings.PRISM_CONFIG['enabled_plugins']:
                    prism.settings.PRISM_CONFIG['enabled_plugins'].remove(id)
            return ('core.RestartView', {'return_url': 'dashboard.PluginListView'})
        return ('dashboard.PluginListView')

class PluginInstallView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/plugins/install',
                                title='Install Plugins',
                                menu={'id': 'plugins.install', 'icon': 'cube', 'order': 1})

    def get(self, request):
        return ('plugins/install.html')
