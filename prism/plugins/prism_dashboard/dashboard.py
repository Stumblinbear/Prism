# If you know of a better way to handle this, be my guest.
import builtins, prism, settings

import json, base64

import subprocess, shlex, sys
from helpers import NonBlockingStreamReader

from flask import redirect, url_for
flask_app = prism.get().app()

def init():
	builtins.prism_dashboard = PrismDashboard(settings.PRISM_CONFIG)

def get():
	return builtins.prism_dashboard


def error(url_from, title, info, fix=None):
	error_json = { 'url_from': url_from, 'title': title, 'info': info, 'fix': fix }
	error_json = json.dumps(error_json)
	error_json = base64.b64encode(bytes(error_json, 'utf-8'))
	return redirect(url_for('dashboard.error', error_json=error_json))

def url_command(command, return_url=None, restart=0):
	return url_for('dashboard.command', command=command, return_url=return_url, restart=restart)
flask_app.jinja_env.globals["url_command"] = url_command

def command(command, return_url=None, restart=0):
	term = Terminal(command=command)
	return redirect(url_for('dashboard.terminal', id=term.get_id(), return_url=return_url, restart=restart))

def url_install_application(id, return_url=None):
	cmd = ''
	
	os = prism.get_general_os()
	if os == 'redhat':
		cmd = 'yum -y install'
	elif os == 'debian':
		cmd = 'apt-get -y install'
	else:
		cmd = 'pkg_add -r'
	
	return url_command(command='%s %s' % (cmd, id), return_url=return_url, restart=1)
flask_app.jinja_env.globals["url_install_application"] = url_install_application

def url_restart(return_url=None):
	return url_for('dashboard.restart', return_url=return_url)
flask_app.jinja_env.globals["url_restart"] = url_restart

def restart(return_url=None):
	return redirect(url_restart(return_url=return_url))


class PrismDashboard:
	def __init__(self, config):
		self.possible_widgets = {}
		
		if 'widgets' not in config:
			config['widgets'] = {}
		
		self.widgets = {}
		widgets = config['widgets']
		
		# Cleanup widgets
		for widget, order in self.widgets.items():
			if widget in self.widgets:
				continue
			if widget[:1] == '!':
				if not widget[1:] in widgets:
					self.widgets[widget] = order
			elif not '!%s' % widget in widgets:
				self.widgets[widget] = order
		
		self.terminals = {}
	
	def save_widgets(self):
		settings.PRISM_CONFIG['widgets'] = self.widgets
		settings.save_config()
	
	def widget_shown(self, id):
		return (not '!%s' % id in self.widgets.values() and id in self.widgets.values())
	
	def add_widget(self, id, f, order=999, default=False):
		self.possible_widgets[id] = { 'id': id, 'f': f, 'default': default}
		
		if not '%s' % id in self.widgets.values() and not '!%s' % id in self.widgets.values():
			if default:
				self.widgets[id] = order
			else:
				self.widgets['!%s' % id] = order
	
	def get_widgets(self, all=False):
		widgets = []
		
		if all:
			for widget, order in self.widgets.items():
				shown = True
				if widget[:1] == '!':
					widget = widget[1:]
					shown = False
				widgets.insert(order, (widget, self.possible_widgets[widget]['f'], order, shown))
		else:
			for widget, order in self.widgets.items():
				if widget[:1] != '!':
					widgets.insert(order, (widget, self.possible_widgets[widget]['f']))
		
		return widgets
	
	def get_terminal(self, id):
		if not id in self.terminals:
			return None
		return self.terminals[id]

class Terminal:
	def __init__(self, id=None, command=None):
		if id == None:
			id = prism.generate_random_string(8)
		
		self.id = id
		self.command = command
		
		self.process = None
		self.nsbr = None
		
		get().terminals[self.id] = self
	
	def get_id(self):
		return self.id
	
	def output(self):
		if self.process == None:
			self.run()
		
		output = []
		if self.process != None:
			if self.nbsr != None:
				for i in range(0, 10):
					line = self.nbsr.readline(0.1)
					if not line:
						break
					output.append(line)
			if len(output) == 0 and self.process.poll() is not None:
				return 0
		return output
	
	def input(self, input):
		self.process.stdin.write(input)
	
	def run(self):
		if self.command != None:
			self.process = subprocess.Popen(shlex.split(self.command), stdout=subprocess.PIPE, stdin=subprocess.PIPE, bufsize=1, universal_newlines=True)
		else:
			self.process = subprocess.Popen(sys.executable, creationflags=subprocess.CREATE_NEW_CONSOLE, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, bufsize=1, universal_newlines=True)
		
		self.nbsr = NonBlockingStreamReader(self.process.stdout)
	
	def destroy(self):
		del get().terminals[self.id]

class FlushFile(object):
    def __init__(self, fd):
        self.fd = fd

    def write(self, x):
        ret = self.fd.write(x)
        self.fd.flush()
        return ret

    def writelines(self, lines):
        ret = self.writelines(lines)
        self.fd.flush()
        return ret

    def flush(self):
        return self.fd.flush

    def close(self):
        return self.fd.close()

    def fileno(self):
        return self.fd.fileno()

sys.stdout = FlushFile(sys.__stdout__)