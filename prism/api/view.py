import prism

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
