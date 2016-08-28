from flask import request, redirect, url_for, render_template, jsonify
from flask_menu import register_menu

import prism, settings
plugin_dashboard = prism.get_plugin('dashboard')
plugin_dashboard.init()

import dashboard
dashboard.init()

import json, base64

import threading

@plugin_dashboard.route('/dashboard', 'Dashboard', '.dashboard', icon='dashboard', order=0)
def home():
	return render_template('dashboard.html', widgets=dashboard.get().get_widgets())

@plugin_dashboard.route('/error', 'Internal Error', ignore=True)
@plugin_dashboard.route('/error/<path:error_json>', ignore=True)
def error(error_json=None):
	if error_json is None:
		return redirect(url_for('dashboard.home'))
	error_json = json.loads(base64.b64decode(error_json).decode('utf-8'))
	return render_template('error.html', error=error_json)

@plugin_dashboard.route('/restart', 'Restarting', methods=['GET', 'POST'], ignore=True)
@plugin_dashboard.route('/restart/<return_url>', methods=['GET', 'POST'], ignore=True)
def restart(return_url='dashboard.home'):
	if request.method == 'POST':
		action = request.form['action']
		if action == '0':
			threading.Timer(1, prism.restart).start()
			settings.save_config()
			return '0'
		else:
			return '1'
	return render_template('restart.html', return_url=return_url)

@plugin_dashboard.route('/command', ignore=True)
@plugin_dashboard.route('/command/<command>', ignore=True)
@plugin_dashboard.route('/command/<command>/<return_url>', ignore=True)
@plugin_dashboard.route('/command/<command>/<return_url>/<int:restart>', ignore=True)
def command(command=None, return_url=None, restart=0):
	return dashboard.command(command=command, return_url=return_url, restart=restart)

@plugin_dashboard.route('/terminal', 'Terminal', '.dashboard.terminal', methods=['GET', 'POST'], ignore=True)
@plugin_dashboard.route('/terminal/<id>', methods=['GET', 'POST'], ignore=True)
@plugin_dashboard.route('/terminal/<id>/<return_url>', methods=['GET', 'POST'], ignore=True)
@plugin_dashboard.route('/terminal/<id>/<return_url>/<int:restart>', methods=['GET', 'POST'], ignore=True)
def terminal(id=None, return_url=None, restart=0):
	terminal = None
	if id != None:
		terminal = dashboard.get().get_terminal(id)

	if request.method == 'POST':
		if terminal == None:
			return jsonify({ 'error': 'No terminal' })
		action = request.form['action']
		if action == 'input':
			input = request.form['input']
			terminal.input(input)
		elif action == 'output':
			output = terminal.output()
			if output == 0:
				terminal.destroy()
				return '0'
			return jsonify(output)
		return jsonify({ })

	return render_template('terminal.html', terminal=terminal, return_url=return_url, restart=restart)

@plugin_dashboard.route('/dashboard/edit', methods=['GET', 'POST'], ignore=True)
def dashboard_edit():
	if request.method == 'POST':
		action = request.form['action']

		prism_dashboard = dashboard.get()

		if action == 'show' or action == 'hide':
			id = request.form['id']

			if action == 'show':
				prism_dashboard.widgets[id] = dashboard.get().widgets['!%s' % id]
				del prism_dashboard.widgets['!%s' % id]
			else:
				prism_dashboard.widgets['!%s' % id] = dashboard.get().widgets[id]
				del prism_dashboard.widgets[id]
		elif action == 'order':
			data = request.form['data']
			for pack in data.split(','):
				pack = pack.split('=')

				if pack[0] in prism_dashboard.widgets:
					prism_dashboard.widgets[pack[0]] = int(pack[1])
				elif '!%s' % pack[0] in prism_dashboard.widgets:
					prism_dashboard.widgets['!%s' % pack[0]] = int(pack[1])

		dashboard.get().save_widgets()
		return '1'
	return render_template('dashboard_edit.html', widgets=dashboard.get().get_widgets(all=True))

@plugin_dashboard.route('/plugins', 'Plugins', '.plugins', icon='cubes', order=1)
def plugins_dummy():
	return redirect(url_for('dashboard.plugins_list'))

@plugin_dashboard.route('/plugins/list', 'Installed Plugins', '.plugins.list', icon='square', order=0)
def plugins_list():
	return render_template('plugins/list.html', plugins=prism.get().get_plugin_manager().get_plugins())

@plugin_dashboard.route('/plugins/list', methods=['POST'], ignore=True)
def plugins_edit():
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

@plugin_dashboard.route('/plugins/install', 'Install Plugins', '.plugins.install', icon='cube', order=1)
def plugins_install():
	return render_template('plugins/install.html')
