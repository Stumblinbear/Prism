import base64
import json
import subprocess
import threading
import time

import flask

import prism
import prism.settings

from prism.api.view import BaseView, route, ignore

from prism_core.terminal import TerminalCommand

class CoreView(BaseView):
    def __init__(self):
        BaseView.__init__(self)

        self.terminals = {}

    @route('/restart')
    @route('/restart/<return_url>')
    def restart(self, return_url='dashboard.home'):
        return ('restart.html', {'return_url': return_url})

    @route('/restart')
    def restart_post(self, request):
        action = request.form['action']
        if action == '0':
            threading.Timer(1, prism.restart).start()
            prism.settings.PRISM_CONFIG.save()
            return '0'
        else:
            return '1'

    @route('/error/<path:error_json>')
    def error(self, error_json):
        error_json = json.loads(base64.b64decode(error_json).decode('utf-8'))
        return ('error.html', {'error': error_json})

    @route('/terminal/install/<install_type>/<install_name>')
    @route('/terminal/install/<install_type>/<install_name>/<return_url>')
    @route('/terminal/install/<install_type>/<install_name>/<restart>/<return_url>')
    def terminal_install(self, install_type, install_name, restart=False, return_url=None):
        if install_type == 'binary':
            cmd = prism.get_os_command('yum install %s', 'apt-get install %s', 'pkg_add -v %s')
        elif install_type == 'module':
            cmd = 'pip install %s'
        else:
            return ('error')
        return ('core.terminal_command', {'command': cmd % install_name, 'restart': restart, 'return_url': return_url})

    @route('/terminal/command/')
    @route('/terminal/command/<command>')
    @route('/terminal/command/<command>/<return_url>')
    @route('/terminal/command/<command>/<restart>')
    @route('/terminal/command/<command>/<restart>/<return_url>')
    def terminal_command(self, command=None, restart=False, return_url=None):
        if command is None:
            return ('error', {
                                'title': 'Terminal',
                                'error': 'No command specified.'
                            }
                    )
        terminal = TerminalCommand(command, return_url=return_url, restart=bool(restart))
        self.terminals[terminal.terminal_id] = terminal
        return ('core.terminal', {'terminal_id': terminal.terminal_id})

    @route('/terminal')
    @route('/terminal/<terminal_id>')
    def terminal(self, terminal_id=None):
        terminal = None

        if terminal_id is None:
            return ('error', {
                                'title': 'Terminal',
                                'error': 'No command specified.'
                            }
                    )
        else:
            terminal = self.get_terminal(terminal_id)
            if isinstance(terminal, tuple):
                return terminal

        return ('terminal.html', {'terminal': terminal})

    @route('/terminal/stream')
    @route('/terminal/stream/<terminal_id>')
    def terminal_stream(self, terminal_id=None):
        terminal = self.get_terminal(terminal_id)
        if isinstance(terminal, tuple):
            return terminal

        resp = terminal.output()
        if resp == -1:
            del self.terminals[terminal.terminal_id]
            return {'type': 'dead'}

        return {'type': 'data', 'data': resp}

    @route('/terminal/stream')
    @route('/terminal/stream/<terminal_id>')
    def terminal_stream_post(self, request, terminal_id):
        terminal = self.get_terminal(terminal_id)
        if isinstance(terminal, tuple):
            return terminal

        user_input = request.form['in']

        if not terminal.running:
            if user_input == '1':
                terminal.init()
            else:
                del self.terminals[terminal.terminal_id]
            return 0

        if user_input != '':
            terminal.input(user_input)
        return 0

    @ignore
    def get_terminal(self, terminal_id):
        if terminal_id is None:
            return ('error', 404)

        if terminal_id not in self.terminals:
            return ('error', {
                                'title': 'Terminal',
                                'error': 'A terminal with that ID doesn\'t exist.'
                            }
                    )

        terminal = self.terminals[terminal_id]
        if terminal.running and terminal.process is None:
            del self.terminals[terminal.terminal_id]
            return ('error', {
                                'title': 'Terminal',
                                'error': 'Terminal process dead.'
                            }
                    )

        return terminal
