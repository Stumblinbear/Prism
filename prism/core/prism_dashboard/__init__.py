import flask
import jinja2

import prism
from prism.api.plugin import BasePlugin

from .views import *


class DashboardPlugin(BasePlugin):
	def init(self, prism_state):
		self._available_widgets = {}
		self._widgets = self.config('widgets', {})

		# Search the plugins for Widget classes
		for plugin_id, plugin in prism_state.plugin_manager.plugins.items():
			for name, obj in prism_state.plugin_manager.get_classes(plugin._module, Widget):
				widget = obj()
				widget.plugin_id = plugin.plugin_id
				widget.widget_id = plugin.plugin_id + '.' + widget.widget_id
				self._available_widgets[widget.widget_id] = widget

				if widget.widget_id not in self._widgets:
					self._widgets[widget.widget_id] = {'shown': True, 'order': len(self._available_widgets)}

		prism.output('Registered %s widgets' % len(self._available_widgets))
		prism.flask_app().jinja_env.globals["render_widget"] = self.render_widget

	def get_widget(self, widget_id):
		return self._available_widgets[widget_id]

	def render_widget(self, widget_id):
		return self._available_widgets[widget_id].do_render()

	def is_widget_shown(self, id):
		return self._widgets[id].shown

	def get_widgets(self, all=False):
		ret_widgets = {}

		if all:
			for widget_id, widget_config in self._widgets.items():
				if widget_id not in self._available_widgets:
					continue
				ret_widgets[widget_config['order']] = (widget_id, self._available_widgets[widget_id], widget_config)
		else:
			for widget_id, widget_config in self._widgets.items():
				if widget_id not in self._available_widgets:
					continue
				if widget_config['shown']:
					ret_widgets[widget_config['order']] = (widget_id, self._available_widgets[widget_id])

		ret_widgets = sorted(ret_widgets.items(), key=lambda x: x[0])
		return [v[1] for v in ret_widgets]

	def save_widgets(self):
		self.config.save()

class Widget(object):
	_check_permissions = False

	def __init__(self, widget_id, size=4):
		self.widget_id = widget_id
		self.size = size

	def do_render(self):
		return jinja2.Markup(prism.handle_render(self.plugin_id, self.render))

	def render(self):
		pass
