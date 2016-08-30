class BaseView(object):
	def __init__(self, endpoint='/'):
		if endpoint is None:
			exit('Fatal Error: Endpoint cannot be of type None! Offender: %s' % self)
		if not endpoint.startswith('/'):
			exit('Fatal Error: Endpoints must begin with a leading slash! Offender: %s' % self)

		self.endpoint = endpoint

	def index(self):
		return ('abort', 404)

def route(endpoint=None, methods=None, defaults=None):
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

def ignore(func):
	func.ignore = True
	return func

def menu(title, icon=None, order=999):
	def obj_wrapper(obj):
		obj.menu = {'title': title, 'icon': icon, 'order': order}
		return obj
	return obj_wrapper
