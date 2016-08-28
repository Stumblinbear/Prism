from api import BasePlugin

class DashboardPlugin(BasePlugin):
	def __init__(self):
		BasePlugin.__init__(self,
					plugin_id = 'prism_dashboard',
					name = 'Dashboard',
					version = [ 1, 0, 0, 'indev' ],
					description = 'Handles Prism\'s main dashboard view as well as plugin management.',
					author = 'Stumblinbear',
					homepage = 'http://prismcp.org/',

					icon = 'dashboard', order = 0)

	def init(self, prism):
		self.possible_widgets = { }
		self.widgets = self.config('widgets', { })

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
		self.config.save()

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

def Widget(object):
	def render(self):
		pass

from .views import *
