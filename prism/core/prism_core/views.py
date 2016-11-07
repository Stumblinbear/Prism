import base64
import json
import subprocess
import threading
import time

import flask

import prism
import prism.settings

from prism.api.view import BaseView, subroute

from prism_core.terminal import Terminal

class ErrorView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/error', title='Fatal Error')

    @subroute('/<path:error_json>')
    def get(self, request, error_json):
        error_json = json.loads(base64.b64decode(error_json).decode('utf-8'))
        return ('error.html', {'error': error_json})

class RestartView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/restart', title='Restarting')

    @subroute('/<return_url>')
    def get(self, request, return_url='dashboard.DashboardView'):
        return ('restart.html', {'return_url': return_url})

    def post(self, request):
        action = request.form['action']
        if action == '0':
            prism.settings.PRISM_CONFIG.save()
            flask.request.environ.get('werkzeug.server.shutdown')()
            threading.Timer(.5, self.restart).start()
            return '0'
        else:
            return '1'

    def restart(self):
        """ Safely restart prism """
        import os
        import sys
        import psutil
        import logging

        try:
            p = psutil.Process(os.getpid())
            for handler in p.open_files() + p.connections():
                os.close(handler.fd)
        except Exception as e:
            logging.error(e)

        python = sys.executable
        os.execl(python, python, *sys.argv)

class TerminalView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/terminal', title='Terminal')

        self.terminals = {}

    @subroute('/<terminal_id>')
    def get(self, request, terminal_id=None):
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

    @subroute('/install/<install_type>/<install_name>')
    @subroute('/install/<install_type>/<install_name>/<return_url>')
    @subroute('/install/<install_type>/<install_name>/<restart>/<return_url>')
    def install_get(self, request, install_type, install_name, restart=False, return_url=None):
        if install_type == 'binary':
            cmd = prism.get_os_command('yum -y install %s', 'apt-get -y install %s')
        elif install_type == 'module':
            cmd = 'pip install %s'
        else:
            return ('error')
        return ('core.TerminalView:command', {'command': cmd % install_name, 'restart': restart, 'return_url': return_url})

    @subroute('/command/')
    @subroute('/command/<command>')
    @subroute('/command/<command>/<return_url>')
    @subroute('/command/<command>/<restart>')
    @subroute('/command/<command>/<restart>/<return_url>')
    def command_get(self, request, command=None, restart=False, return_url=None):
        if command is None:
            return ('error', {
                                'title': 'Terminal',
                                'error': 'No command specified.'
                            }
                    )
        terminal = Terminal(command, return_url=return_url, restart=bool(restart))
        self.terminals[terminal.terminal_id] = terminal
        return ('core.TerminalView', {'terminal_id': terminal.terminal_id})

    @subroute('/stream')
    @subroute('/stream/<terminal_id>')
    def stream_get(self, request, terminal_id=None):
        terminal = self.get_terminal(terminal_id)
        if isinstance(terminal, tuple):
            return {'type': 'error', 'data': terminal[1]['error']}

        resp = terminal.read()
        if not resp and not terminal.alive:
            del self.terminals[terminal.terminal_id]
            return {'type': 'dead'}

        return {'type': 'data', 'data': resp}

    @subroute('/stream')
    @subroute('/stream/<terminal_id>')
    def stream_post(self, request, terminal_id):
        terminal = self.get_terminal(terminal_id)
        if isinstance(terminal, tuple):
            return terminal[1]['error']

        user_input = request.form['in']
        if terminal.command is not None:
            if user_input == '1':
                terminal.write(terminal.command)
                terminal.command = None
            elif user_input == '0':
                del self.terminals[terminal.terminal_id]
        elif user_input != '':
            terminal.write(user_input)

        return '0'

    def get_terminal(self, terminal_id):
        if terminal_id is None:
            return ('error', 404)

        if terminal_id not in self.terminals:
            return ('error', {
                                'title': 'Terminal',
                                'error': 'A terminal with that ID doesn\'t exist.'
                            }
                    )

        return self.terminals[terminal_id]
