import base64
import json
import threading

import prism
import settings
from api.view import BaseView, route


class Core(BaseView):
    def __init__(self):
        BaseView.__init__(self, '/')

    @route('/restart')
    def restart(self, return_url='dashboard.home'):
        return ('restart.html', { 'return_url': return_url })

    @route('/restart')
    def post(self, request):
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
        return ('error.html', { error: error_json })
