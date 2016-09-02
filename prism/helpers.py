import math
import os
import time
from datetime import datetime

from docutils.core import publish_string
from docutils.writers.html4css1 import Writer, HTMLTranslator
import flask
import jinja2

import prism
import prism.settings


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

def include_static(name):
	""" Load a file from the /static/ directory """
	desired_file = os.path.join(flask_app.static_folder, name)
	with open(desired_file) as f:
		return jinja2.Markup(f.read())
flask_app.jinja_env.globals["include_static"] = include_static

def do_convert_bytes(size, format=False):
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

@flask_app.template_filter()
def locale(s):
	""" Used for localization """
	plugin_id = flask.g.current_plugin
	if plugin_id is None:
		plugin_id = 'prism'
	elif not plugin_id.startswith('prism_'):
		plugin_id = 'prism_' + plugin_id

	# Allow setting their own plugin id (Iunno why, but it might be useful)
	if ':' in s:
		plugin_id, s = s.split(':', 1)

	# Search the plugin that's rendering the template for the requested locale
	if plugin_id == 'prism':
		s = prism.settings.PRISM_LOCALE[s]
	else:
		plugin = prism.get_plugin(plugin_id)

		if plugin is None:
			prism.output('Unknown plugin ID. Offender: %s' % plugin_id)
			return s

		s = plugin.locale[s]

	s = publish_string(s, writer=html_fragment_writer).decode('utf-8').rstrip('\r\n')
	s = s.split('<p>', 1)[1]
	s = s[:s.rfind('</p>')]
	return jinja2.Markup(s)

@flask_app.template_filter()
def convert_bytes(size):
	return do_convert_bytes(size, True)

@flask_app.template_filter()
def ctime(s):
	return time.ctime(s)

@flask_app.template_filter()
def timesince(dt, past_="ago", future_="from now", default="just now"):
	if isinstance(dt, int) or isinstance(dt, float):
		dt = datetime.strptime(ctime(dt), '%a %b %d %H:%M:%S %Y')

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
