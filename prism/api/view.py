import flask
import jinja2

import prism
from prism.memorize import memorize

class BaseView(object):
	_check_permissions = True

	def __init__(self, endpoint, title=None, menu=None):
		assert endpoint.startswith('/'), 'Endpoint does not begin with a /! Offender: %s' % endpoint
		assert '<' not in endpoint, 'Endpoint should not contain arguments. Offender: %s' % endpoint

		self.endpoint = endpoint
		self.title = title

		if menu is not None:
			assert 'id' in menu, '%s has a menu item, but the id has not been set!' % endpoint
			if 'icon' not in menu:
				menu['icon'] = 'circle-o'
			if 'order' not in menu:
				menu['order'] = 999

			if 'parent' in menu:
				assert 'id' in menu['parent'], '%s has a parent menu item, but the id has not been set!' % endpoint
				assert 'text' in menu['parent'], '%s has a parent menu item, but the text has not been set!' % endpoint
				if 'icon' not in menu['parent']:
					menu['parent']['icon'] = 'circle-o'
				if 'order' not in menu['parent']:
					menu['parent']['order'] = 999

		self.menu = menu

def subroute(endpoint=None, methods=None, defaults=None):
	def func_wrapper(func):
		route = {}

		if endpoint is not None:
			route['endpoint'] = endpoint
		if methods is not None:
			route['http_methods'] = methods
		if defaults is not None:
			route['defaults'] = defaults

		if not hasattr(func, 'routes'):
			func.routes = list()
		func.routes.append(route)

		return func
	return func_wrapper

class View(object):
	def __init__(self, view_type='main'):
		self.view_type = view_type
		self.content = []

	def add(self, view, size=0):
		view.size = size
		self.content.append(view)
		return self

	@memorize(60)
	def render(self):
		return flask.render_template('views/%s.html' % self.view_type, content=self.content)

class ViewElement(object):
	def __init__(self):
		self.children = []

	def add(self, child, size=0):
		child.size = size
		self.children.append(child)
		return self

	def render(self):
		pass

class HTMLElement(ViewElement):
	def __init__(self, html=''):
		ViewElement.__init__(self)
		self.html = html

	def render(self):
		return flask.render_template('views/elements/html.html', view=self, children=self.children)

class LocaleElement(ViewElement):
	def __init__(self, locale):
		ViewElement.__init__(self)
		self.locale = locale

	def render(self):
		import prism.helpers
		return prism.helpers.locale(self.locale)

class RowElement(ViewElement):
	def __init__(self):
		ViewElement.__init__(self)

	def render(self):
		return flask.render_template('views/elements/row.html', view=self, children=self.children)

class BoxElement(ViewElement):
	def __init__(self, title=None, icon=None, padding=True):
		ViewElement.__init__(self)
		self.title = title
		self.icon = icon
		self.padding = padding

	def render(self):
		return flask.render_template('views/elements/box.html', view=self, children=self.children)

class TableElement(ViewElement):
	def __init__(self, headers=None, content=None):
		ViewElement.__init__(self)
		self.headers = headers
		self.content = content

	def render(self):
		return flask.render_template('views/elements/table.html', view=self, children=self.children)

class TableExtendedElement(ViewElement):
	def __init__(self, headers=None, content=None):
		ViewElement.__init__(self)
		self.headers = headers
		self.content = content

	def render(self):
		return flask.render_template('views/elements/table_extended.html', view=self, children=self.children)

class FormElement(ViewElement):
	def __init__(self, inline=False):
		ViewElement.__init__(self)
		self.inline = inline

	def render(self):
		return flask.render_template('views/elements/form/form.html', view=self, children=self.children)

class InputElement(ViewElement):
	def __init__(self, label, name, input_type='text', placeholder='', help_text=None):
		ViewElement.__init__(self)
		self.label = label
		self.name = name
		self.input_type = input_type
		self.placeholder = placeholder
		self.help_text = help_text

		self.unique_id = prism.generate_random_string(6)

	def render(self):
		return flask.render_template('views/elements/form/input.html', view=self, children=self.children, unique_id=self.unique_id, label=self.label, name=self.name, input_type=self.input_type, placeholder=self.placeholder)

class ButtonElement(ViewElement):
	def __init__(self, text='Submit', name='', is_submit=True, button_type='default'):
		ViewElement.__init__(self)
		self.text = text
		self.is_submit = is_submit
		self.button_type = button_type

	def render(self):
		return flask.render_template('views/elements/form/button.html', view=self, children=self.children, text=self.text, is_submit=self.is_submit, button_type=self.button_type)
