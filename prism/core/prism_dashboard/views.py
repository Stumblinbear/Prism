from api.view import BaseView, route, menu

import prism

class Dashboard(BaseView):
    def __init__(self):
        BaseView.__init__(self, '/')

    @menu('Home', icon='home', order=0)
    def home(self):
        return ('dashboard.html', { 'widgets': prism.get_plugin('prism_dashboard').get_widgets() })

    @route('/home/edit')
    def edit(self):
        return ('dashboard_edit.html', { 'widgets': prism.get_plugin('prism_dashboard').get_widgets(all=True) })

    def post(self, request):
        prism_dashboard = prism.get_plugin('prism_dashboard')

        action = request.form['action']
        if action == 'show' or action == 'hide':
            id = form['id']

            if action == 'show':
                prism_dashboard.widgets[id] = prism_dashboard.widgets['!%s' % id]
                del prism_dashboard.widgets['!%s' % id]
            else:
                prism_dashboard.widgets['!%s' % id] = prism_dashboard.widgets[id]
                del prism_dashboard.widgets[id]
        elif action == 'order':
            data = request.form['data']
            for pack in data.split(','):
                pack = pack.split('=')

                if pack[0] in prism_dashboard.widgets:
                    prism_dashboard.widgets[pack[0]] = int(pack[1])
                elif '!%s' % pack[0] in prism_dashboard.widgets:
                    prism_dashboard.widgets['!%s' % pack[0]] = int(pack[1])

        prism_dashboard.save_widgets()
        return '1'

@menu('Plugins', icon='cubes', order=1)
class Plugins(BaseView):
    def __init__(self):
        BaseView.__init__(self, '/plugins')

    @menu('Installed Plugins', icon='square', order=1)
    def list(self):
        plugin_manager = prism.plugin_manager()
        return ('plugins/list.html', { 'plugins': plugin_manager.plugins })

    @route('/list', methods=['POST'])
    def post(self, request):
        id = request.form['id']
        action = request.form['action']
        if id != None and action != None:
            if action == 'enable':
                if not id in settings.PRISM_CONFIG['enabled']:
                    settings.PRISM_CONFIG['enabled'].append(id)
            elif action == 'disable':
                if id in settings.PRISM_CONFIG['enabled']:
                    settings.PRISM_CONFIG['enabled'].remove(id)
            return dashboard.restart(return_url='dashboard.plugins_list')
        return redirect(url_for('dashboard.plugins_list'))

    @menu('Install Plugins', icon='cube', order=2)
    def install(self):
        return ('plugins/install.html')
