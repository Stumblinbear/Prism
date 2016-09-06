import json

import prism
import prism.settings
import prism.helpers

from prism.api.view import BaseView, subroute, View, RowElement, BoxElement, HTMLElement, LocaleElement, TableElement, \
                            FormElement, InputElement, ButtonElement


class DashboardView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/home', title='Home',
                                menu={'id': 'dashboard.home', 'icon': 'home', 'order': 0,
                                        'parent': {'id': 'dashboard', 'text': 'Dashboard', 'icon': 'dashboard', 'order': 0}})

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

class UserListView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/users/list', title='User Management',
                                menu={'id': 'dashboard.users', 'icon': 'users', 'order': 1})

    def get(self, request):
        view = View()
        row = RowElement()

        box1 = BoxElement(title='Create New', icon='user')
        form = FormElement().add(InputElement('Name', 'name')) \
                            .add(InputElement('Info', 'info')) \
                            .add(InputElement('Username', 'username')) \
                            .add(InputElement('Password', 'password', input_type='password')) \
                            .add(ButtonElement('Create User', button_type='primary'))
        box1.add(form)
        row.add(box1, size=4)

        box2 = BoxElement(title='user.list.header', icon='users', padding=False)
        box2.add(TableElement(
                        ['user.list.name', 'user.list.username', 'user.list.actions'],
                        [(user.name, user.username, '<a href="/dashboard/users/edit/%s"><button class="btn btn-primary btn-sm">Edit User</button></a>' % user.user_id) for user in prism.login.User.query.all()]
                    ))
        row.add(box2)

        view.add(row)
        return view

    def post(self, request):
        prism.login.create_user(request.form['username'], request.form['password'], request.form['name'], request.form['info'])
        return ('dashboard.UserListView')

class UserEditView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/users/edit', title='User Editor')

    @subroute('/<user_id>')
    def get(self, request, user_id):
        return ('users/edit.html', {'user': prism.login.User.query.get(user_id), 'permissions': prism.plugin_manager().possible_permissions})

    @subroute('/<user_id>')
    def post(self, request, user_id):
        prism.login.User.query.get(user_id).update(request.form['username'], request.form['password'], request.form['name'], request.form['info'], request.form['permissions'])
        return ('dashboard.UserEditView', {'user_id': user_id})

class UserMeView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/users/me', title='Me')

    def get(self, request):
        return ('users/me.html')

class PluginListView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/plugins/list', title='Installed Plugins',
                                menu={'id': 'dashboard.plugins.list', 'icon': 'square', 'order': 0,
                                        'parent': {'id': 'dashboard.plugins', 'text': 'Plugins', 'icon': 'cubes', 'order': 2}})

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
                                menu={'id': 'dashboard.plugins.install', 'icon': 'cube', 'order': 1})

    def get(self, request):
        return ('plugins/install.html')

class UpdateView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/updates', title='View Update')

    @subroute('/<name>')
    def get(self, request, name=None):
        view = View()
        row = RowElement()

        if name is None:
            box1 = BoxElement(title='updates.info.header', icon='info')
            box1.add(HTMLElement().add(LocaleElement('updates.info.dev')))
            row.add(box1, size=3)

            box2 = BoxElement(title='updates.dev.commits.header', icon='archive', padding=False)
            box2.add(TableElement(
                            ['updates.commits.date', 'updates.commits.hash', 'updates.commits.changes'],
                            [('<span class="text-muted">%s</span>' % prism.helpers.timesince(change[3]), '<a href="%s" target="_blank">%s</a>' % (change[2], change[0]), change[1]) for change in prism.settings.PRISM_VERSIONING['dev_changes']]
                        ))
            row.add(box2)
        else:
            release = None

            for recent in prism.settings.PRISM_VERSIONING['recent_releases']:
                if recent['name'] == name:
                    release = recent
                    break

            if release is None:
                return ('dashboard.UpdateView')

            box1 = BoxElement(title='updates.info.header', icon='info', padding=False)
            box1.add(TableElement(
                            content=[
                                    ('updates.info.version', release['name']),
                                    ('updates.info.date', '<span class="text-muted">%s</span>' % prism.helpers.timesince(release['date']))
                                ]
                        ))
            row.add(box1, size=3)

            box2 = BoxElement(title='updates.commits.header', icon='archive', padding=False)
            box2.add(TableElement(
                            ['updates.commits.date', 'updates.commits.hash', 'updates.commits.changes'],
                            [('<span class="text-muted">%s</span>' % prism.helpers.timesince(change[3]), '<a href="%s" target="_blank">%s</a>' % (change[2], change[0]), change[1]) for change in release['changes']]
                        ))
            row.add(box2)

        view.add(row)
        return view
