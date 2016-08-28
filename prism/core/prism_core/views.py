import base64
import json
import threading

import prism
import settings
from api.view import BaseView, route


class CoreView(BaseView):
    @route('/restart')
    @route('/restart/<return_url>')
    def restart(self, return_url='dashboard.home'):
        return ('restart.html', {'return_url': return_url})

    @route('/restart')
    def post(self, request):
        print(request)
        action = request.form['action']
        if action == '0':
            threading.Timer(1, prism.restart).start()
            settings.save_config(settings.CONFIG_FILE, settings.PRISM_CONFIG)
            return '0'
        else:
            return '1'

    @route('/error/<path:error_json>')
    def error(self, error_json):
        error_json = json.loads(base64.b64decode(error_json).decode('utf-8'))
        return ('error.html', {'error': error_json})

    @route('/command/<command>')
    @route('/command/<command>/<return_url>')
    @route('/command/<command>/<int:restart>')
    @route('/command/<command>/<int:restart>/<return_url>')
    def command(self, command, return_url, restart=False):
        error_json = json.loads(base64.b64decode(error_json).decode('utf-8'))
        return ('error.html', {'error': error_json})

    @route('/command/install/<type>/<install>')
    def install(self, type, install):
        error_json = json.loads(base64.b64decode(error_json).decode('utf-8'))
        return ('error.html', {'error': error_json})
