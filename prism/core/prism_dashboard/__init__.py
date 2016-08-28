from flask import render_template

from api import BasePlugin

class DashboardPlugin(BasePlugin):
	def __init__(self):
		BasePlugin.__init__(self, display_name = 'Dashboard', order = 0)

	def init(self, prism_state):
		self._available_widgets = { }
		self._widgets = self.config('widgets', { })

		# Search the plugins for Widget classes
		for plugin_id, plugin in prism_state.plugin_manager.plugins.items():
			for name, obj in prism_state.plugin_manager.get_classes(plugin._module, Widget):
				widget = obj()
				widget.widget_id = plugin_id + '.' + widget.widget_id
				self._available_widgets[widget.widget_id] = widget

				if widget.widget_id not in self._widgets:
					self._widgets[widget.widget_id] = { 'shown': True, 'order': len(self._available_widgets) }

		prism.output('Registered %s widgets' % len(self._available_widgets))
		prism.flask().jinja_env.globals["render_widget"] = self.render_widget

	def get_widget(self, widget_id):
		return self._available_widgets[widget_id]

	def render_widget(self, widget_id):
		return self._available_widgets[widget_id].do_render()

	def is_widget_shown(self, id):
		return self._widgets[id].shown

	def get_widgets(self, all=False):
		ret_widgets = []

		if all:
			for widget_id, widget_config in self._widgets.items():
				ret_widgets.insert(widget_config['order'], (widget_id, self._available_widgets[widget_id], widget_config))
		else:
			for widget_id, widget_config in self._widgets.items():
				if widget_config['shown']:
					ret_widgets.insert(widget_config['order'], (widget_id, self._available_widgets[widget_id]))

		return ret_widgets

	def save_widgets(self):
		self.config.save()

class Widget(object):
	def __init__(self, widget_id):
		self.widget_id = widget_id

	def do_render(self):
		obj = self.render()

		if isinstance(obj, tuple):
			page_args = { }
			if len(obj) > 1:
				page_args = obj[1]

			if obj[0].endswith('.html'):
				return render_template(obj[0], **page_args)
		return obj

	def render(self):
		pass

from .views import *
