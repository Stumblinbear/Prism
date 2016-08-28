from flask import request, redirect, url_for, render_template
from flask_menu import register_menu

import prism, dashboard
plugin_firewall = prism.get_plugin('firewall')
plugin_firewall.init()

import netfilter

@plugin_firewall.route('/firewall', 'Firewall', '.firewall', icon='cubes')
def info():
	try:
		from netfilter.table import Table
		table = Table('raw')
		print(table.list_chains())
	except netfilter.table.IptablesError as e:
		return dashboard.error('firewall.info', 'IPTables', 'Unable to initialize IPTables. Do you need to insmod?',
								[
									{
										'text': 'IPTables must be inserted as a module into the linux kernel.',
										'command': 'modprobe ip_tables'
									}, {
										'text': 'Update your installed packages.',
										'command': 'yum -y update'
									}, {
										'text': 'Update your kernel. Then, restart your system.',
										'command': 'yum -y update kernel'
									}
								]
							)
	return render_template('firewall.html')