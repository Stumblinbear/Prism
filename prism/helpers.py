import math
import os
import time

from datetime import datetime

import jinja2

import prism
flask_app = prism.flask()

def convert_bytes(size, format=False):
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
	return convert_bytes(size, True)

def next_color(i):
	colors = [ '#337AB7', '#00A65A', '#F39C12', '#DD4B39', '#4682B4', '#20B2AA', '#FFD700', '#00FA9A', '#7B68EE', '#FF00FF', '#20B2AA', '#BC8F8F', '#8B008B', '#008000', '#000080' ]
	return colors[i % len(colors)]
flask_app.jinja_env.globals["next_color"] = next_color

def include_static(name):
	directory = flask_app.static_folder
	desired_file = os.path.join(directory, name)
	with open(desired_file) as f:
		return jinja2.Markup(f.read())
flask_app.jinja_env.globals["include_static"] = include_static

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
