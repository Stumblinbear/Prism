from api.view import BaseView, route, menu

import prism
import settings


class DashboardView(BaseView):
    @menu('Home', icon='home', order=0)
    def home(self):
        return ('dashboard.html', {'widgets': prism.get_plugin('prism_dashboard').get_widgets()})

    @route('/home/edit')
    def edit(self):
        return ('dashboard_edit.html', {'widgets': prism.get_plugin('prism_dashboard').get_widgets(all=True)})

    @route('/home/edit')
    def post(self, request):
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

@menu('Plugins', icon='cubes', order=1)
class PluginsView(BaseView):
    def __init__(self):
        BaseView.__init__(self, '/plugins')

    @menu('Installed Plugins', icon='square', order=1)
    def list(self):
        return ('plugins/list.html', {'plugins': prism.plugin_manager().get_sorted_plugins()})

    @route('/list', methods=['POST'])
    def post(self, request):
        id = request.form['id']
        action = request.form['action']
        if id is not None and action is not None:
            if action == 'enable':
                if id not in settings.PRISM_CONFIG['enabled_plugins']:
                    settings.PRISM_CONFIG['enabled_plugins'].append(id)
            elif action == 'disable':
                if id in settings.PRISM_CONFIG['enabled_plugins']:
                    settings.PRISM_CONFIG['enabled_plugins'].remove(id)
            return ('core.restart', {'return_url': 'dashboard.plugins.list'})
        return ('dashboard.plugins.list')

    @menu('Install Plugins', icon='cube', order=2)
    def install(self):
        return ('plugins/install.html')
