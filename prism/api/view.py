import flask
import jinja2

import prism
from prism.memorize import memorize

class BaseView(object):
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

class ViewObject(object):
	def __init__(self):
		self.children = []

	def add(self, child, size=0):
		child.size = size
		self.children.append(child)
		return self

	def render(self):
		pass

class ViewHTML(ViewObject):
	def __init__(self, html):
		ViewObject.__init__(self)
		self.html = html

	def render(self):
		return jinja2.Markup(self.html)

class ViewRow(ViewObject):
	def __init__(self):
		ViewObject.__init__(self)

	def render(self):
		return flask.render_template('views/object/row.html', view=self, children=self.children)

class ViewBox(ViewObject):
	def __init__(self, title=None, icon=None, padding=True):
		ViewObject.__init__(self)
		self.title = title
		self.icon = icon
		self.padding = padding

	def render(self):
		return flask.render_template('views/object/box.html', view=self, children=self.children)

class ViewTable(ViewObject):
	def __init__(self, headers=None, content=None):
		ViewObject.__init__(self)
		self.headers = headers
		self.content = content

	def render(self):
		return flask.render_template('views/object/table.html', view=self, children=self.children)

class ViewTableExtended(ViewObject):
	def __init__(self, headers=None, content=None):
		ViewObject.__init__(self)
		self.headers = headers
		self.content = content

	def render(self):
		return flask.render_template('views/object/table_extended.html', view=self, children=self.children)
