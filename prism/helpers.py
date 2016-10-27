import math
import os
import time
import threading
from functools import wraps
from datetime import datetime

from docutils.core import publish_string
from docutils.writers.html4css1 import Writer, HTMLTranslator
import flask
import jinja2

import prism
import prism.settings

from prism.pyversions import PythonVersions


# Initialize the class so it doesn't hang later
prism.poof('Detecting python versions')
pyversions = PythonVersions.get()

prism.poof('Found %d version%s' % (len(pyversions.versions), 's' if len(pyversions.versions) != 1 else ''))
for version in pyversions.versions:
	prism.output(version)
prism.paaf()
prism.paaf()


flask_app = prism.flask_app()

def next_color(i):
	""" Provides a way to loop through a list of colors in templates """
	colors = ['#337AB7', '#00A65A', '#F39C12',
				'#DD4B39', '#4682B4', '#20B2AA',
				'#FFD700', '#00FA9A', '#7B68EE',
				'#FF00FF', '#20B2AA', '#BC8F8F',
				'#8B008B', '#008000', '#000080']
	return colors[i % len(colors)]
flask_app.jinja_env.globals["next_color"] = next_color

flask_app.jinja_env.globals["generate_random_string"] = prism.generate_random_string

def include_static(name):
	""" Load a file from the /static/ directory """
	desired_file = os.path.join(flask_app.static_folder, name)
	with open(desired_file) as f:
		return jinja2.Markup(f.read())
flask_app.jinja_env.globals["include_static"] = include_static

def is_list(value):
	return isinstance(value, list)
flask_app.jinja_env.globals["is_list"] = is_list

def convert_bytes_format(size, format):
	""" Convert amount of bytes, size, to its easier to read representation """
	if(size == 0):
		if format:
			return '0b'
		return (0, "b")
	size_name = ("b", "kb", "mb", "gb", "tb", "pb", "eb", "zb", "yb")
	i = int(math.floor(math.log(size, 1024)))
	p = math.pow(1024, i)
	s = round(size / p, 2)
	if format:
		return '%s%s' % (int(s), size_name[i])
	return (int(s), size_name[i])

@flask_app.template_filter()
def convert_bytes(size):
	return convert_bytes_format(size, True)

@flask_app.template_filter()
def hide_none(size):
	""" A filter to hide the value if it is python's 'None' value """
	return size if size is not None else ''

class HTMLFragmentTranslator(HTMLTranslator):
	def __init__(self, document):
		HTMLTranslator.__init__(self, document)
		self.head_prefix = ['', '', '', '', '']
		self.body_prefix = []
		self.body_suffix = []
		self.stylesheet = []

	def astext(self):
		return ''.join(self.body)

html_fragment_writer = Writer()
html_fragment_writer.translator_class = HTMLFragmentTranslator

def locale_(plugin_id, s):
	""" Search the plugin that's rendering the template
	for the requested locale """
	if plugin_id == 'prism':
		ns = prism.settings.PRISM_LOCALE[s]
	else:
		plugin = prism.get_plugin(plugin_id)

		if plugin is None:
			prism.output('Unknown plugin ID. Offender: %s' % plugin_id)
			return s

		ns = plugin.locale[s]

	if s == ns:
		return s

	ns = publish_string(ns, writer=html_fragment_writer).decode('utf-8').rstrip('\r\n')
	if '<p>' not in ns:
		return ''

	ns = ns.split('<p>', 1)[1]
	ns = ns[:ns.rfind('</p>')]
	return jinja2.Markup(ns)

@flask_app.template_filter()
def locale(s):
	""" Used for localization """
	if not isinstance(s, str):
		return repr(s)

	plugin_id = flask.g.current_plugin
	if plugin_id is None:
		plugin_id = 'prism'

	# Allow setting their own plugin id (Iunno why, but it might be useful)
	if ':' in s:
		new_plugin_id, ns = s.split(':', 1)

		if new_plugin_id == 'prism' or prism.get_plugin(new_plugin_id) is not None:
			plugin_id = new_plugin_id
			s = ns

	return locale_(plugin_id, s)

@flask_app.template_filter()
def ctime(s):
	return time.ctime(s)

@flask_app.template_filter()
def timesince(dt, past_="ago", future_="from now", default="just now"):
	if isinstance(dt, int) or isinstance(dt, float):
		dt = datetime.strptime(ctime(dt), '%a %b %d %H:%M:%S %Y')
	elif isinstance(dt, str):
		dt = ' '.join(dt.split('T'))
		if dt.endswith('Z'):
			dt = dt[:-1]
		dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')

	now = datetime.utcnow()
	if now > dt:
		diff = now - dt
		dt_is_past = True
	else:
		diff = dt - now
		dt_is_past = False

	periods = (
		(diff.days / 365, "year", "years"),
		(diff.days / 30, "month", "months"),
		(diff.days / 7, "week", "weeks"),
		(diff.days, "day", "days"),
		(diff.seconds / 3600, "hour", "hours"),
		(diff.seconds / 60, "minute", "minutes"),
		(diff.seconds, "second", "seconds"),
	)

	for period, singular, plural in periods:
		if period >= 1:
			return "%d %s %s" % (period, singular if period == 1 else plural, past_ if dt_is_past else future_)

	return default

def repeat(start_time, repeat_time):
	if repeat_time < 1:
		prism.error('Repeating function must have a repeat time greater than 1 second')

		def repeat_inner(func):
			return func
		return repeat_inner

	def repeat_inner(func):
		@wraps(func)
		def func_inner():
			t = threading.Timer(repeat_time, func_inner)
			t.daemon = True
			t.start()
			return func()
		t = threading.Timer(start_time, func_inner)
		t.daemon = True
		t.start()
		return func_inner
	return repeat_inner
