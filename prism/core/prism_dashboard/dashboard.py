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

def url_restart(return_url=None):
	return url_for('dashboard.restart', return_url=return_url)
flask_app.jinja_env.globals["url_restart"] = url_restart

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