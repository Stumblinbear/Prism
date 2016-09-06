from datetime import datetime
import os
import sys
import socket
import time

import prism
from .version import get_new_versions
from .config import JSONConfig, LocaleConfig


PANEL_PID = None
PRISM_PATH = None
TMP_PATH = None

PRISM_VERSIONING = None

CORE_PLUGINS_PATH = None
PLUGINS_PATH = None
CONFIG_FOLDER_PLUGINS = None

CONFIG_FOLDER = None
PRISM_CONFIG = {
		'secret_key': None,
		'host': None,
		'enabled': [],
		'locale': 'en_US',
		'enabled_plugins': []
	}

PRISM_LOCALE = None

def import_folders(path):
	# Snippet to import libraries.
	#
	# This adds all folders within a folder.
	# It is done like this to keep dependencies split
	# and with their required libraries.
	sys.path.append(path)
	for file_name in os.listdir(path):
		import_folder(os.path.join(path, file_name))

def import_folder(path):
	if not os.path.isfile(path):
		sys.path.append(path)

def init(pid):
	global PANEL_PID, PRISM_PATH, TMP_PATH, PRISM_VERSIONING, CORE_PLUGINS_PATH, \
			PLUGINS_PATH, CONFIG_FOLDER_PLUGINS, CONFIG_FOLDER, PRISM_CONFIG, PRISM_LOCALE

	PANEL_PID = pid
	PRISM_PATH = os.path.dirname(os.path.realpath(__file__))

	CORE_PLUGINS_PATH = os.path.join(PRISM_PATH, 'core')
	if not os.path.exists(CORE_PLUGINS_PATH):
		os.makedirs(CORE_PLUGINS_PATH)

	PLUGINS_PATH = os.path.join(PRISM_PATH, 'plugins')
	if not os.path.exists(PLUGINS_PATH):
		os.makedirs(PLUGINS_PATH)

	TMP_PATH = os.path.join(PRISM_PATH, 'tmp')
	if not os.path.exists(TMP_PATH):
		os.makedirs(TMP_PATH)

	prism.output('Currently running in %s' % PRISM_PATH)
	prism.output('')

	PRISM_VERSIONING = JSONConfig(path=os.path.join(TMP_PATH, 'VERSIONING-INFO'))
	ping_version(True)
	prism.output('')

	# Load Prism's config
	CONFIG_FOLDER = os.path.join(PRISM_PATH, 'config')
	if not os.path.exists(CONFIG_FOLDER):
		os.makedirs(CONFIG_FOLDER)
	config_file = os.path.join(CONFIG_FOLDER, 'config.json')

	CONFIG_FOLDER_PLUGINS = os.path.join(CONFIG_FOLDER, 'plugins')
	if not os.path.exists(CONFIG_FOLDER_PLUGINS):
		os.makedirs(CONFIG_FOLDER_PLUGINS)

	PRISM_LOCALE = LocaleConfig(PRISM_PATH)

	# Generate default config values if the file doesn't exist
	# Also, prompt and generate a few of the config values that
	# must be done on first run.
	if not os.path.exists(config_file):
		# I have no idea what came over me when making this section,
		# but it's fabulous and I loved every second of it. I hope
		# I never have to change it. xD
		prism.output(PRISM_LOCALE['start.hello.1'])
		prism.output(PRISM_LOCALE['start.hello.2'])
		subst = {}

		# IP Address/Hostname prompt
		subst['host'] = socket.gethostbyname(socket.gethostname())
		prism.output(PRISM_LOCALE['start.host'].format(**subst))
		PRISM_CONFIG['host'], used_default = prism.get_input(PRISM_LOCALE['start.host.prompt'], default=subst['host'])

		if used_default:
			prism.output('')
			prism.output(PRISM_LOCALE['start.host.correct'])

		# Secret generation
		prism.output('')
		prism.output(PRISM_LOCALE['start.secret'])
		subst['secret_key'], used_default = prism.get_input(PRISM_LOCALE['start.secret.prompt'])

		prism.output('')
		if used_default:
			secret_key = prism.generate_random_string(32)
			prism.output(PRISM_LOCALE['start.secret.generate'].format(**subst))
		else:
			prism.output(PRISM_LOCALE['start.secret.done'].format(**subst))

		PRISM_CONFIG['secret_key'] = secret_key

		# Username and Password prompt
		prism.output('')
		prism.output(PRISM_LOCALE['start.login.username'])
		username, used_default = prism.get_input(PRISM_LOCALE['start.login.username.prompt'], default='admin')
		password, used_default = prism.get_input(PRISM_LOCALE['start.login.password.prompt'], default='password')
		if used_default:
			prism.output(PRISM_LOCALE['start.login.password.default.1'])
			time.sleep(2)
			prism.output(PRISM_LOCALE['start.login.password.default.2'])
			time.sleep(5)
			prism.output(PRISM_LOCALE['start.login.password.default.3'])
			prism.output('')

		prism_login.create_user(username, password, username.capitalize(), 'Main Administrator', ['*'])

		prism.output('')
		prism.output(PRISM_LOCALE['start.done'])
		conf = JSONConfig(path=config_file)
		for key, value in PRISM_CONFIG.items():
			conf[key] = value
		PRISM_CONFIG = conf
	else:
		# Load prism's config
		PRISM_CONFIG = JSONConfig(path=config_file)

		if 'locale' not in PRISM_CONFIG:
			PRISM_CONFIG['locale'] = 'en_US'

		if 'enabled_plugins' not in PRISM_CONFIG:
			PRISM_CONFIG['enabled_plugins'] = [F]

		# Make sure some VERY imporant values are set
		if 'secret_key' not in PRISM_CONFIG:
			prism.output(PRISM_LOCALE['start.missing.secret'])
			PRISM_CONFIG['secret_key'] = prism.generate_random_string(32)
			prism.output('')

		if 'host' not in PRISM_CONFIG:
			host = socket.gethostbyname(socket.gethostname())
			prism.output(PRISM_LOCALE['start.missing.host'])
			PRISM_CONFIG['host'], used_default = prism.get_input(PRISM_LOCALE['start.host.prompt'], default=host)
			prism.output('')

def post_init():
	import prism.login as prism_login
	if prism_login.User.query.count() == 0:
		prism.output('')
		prism.output(PRISM_LOCALE['start.missing.login'])
		username, used_default = prism.get_input(PRISM_LOCALE['start.login.username.prompt'], default='admin')
		password, used_default = prism.get_input(PRISM_LOCALE['start.login.password.prompt'], default='password')
		prism.output('')
		prism_login.create_user(username, password, username.capitalize(), 'Main Administrator', ['*'])

def generate_certificate():
	import subprocess

	script = """
		cd {0}/tmp;
		openssl genrsa -des3 -out prism.key -passout pass:1234 2048;
		openssl req -new -key prism.key -out prism.csr -passin pass:1234 -subj /C=US/ST=NA/L=Nowhere/O=Prism\\ Inc/OU=IT/CN={1}/;
		cp prism.key prism.key.org;
		openssl rsa -in prism.key.org -out prism.key -passin pass:1234;
		openssl x509 -req -days 365 -in prism.csr -signkey prism.key -out prism.crt -passin pass:1234;
		cat prism.key > {2}/prism-ssl.key;
		cat prism.crt > {2}/prism-ssl.crt;
		rm prism.*;
	""".format(PRISM_PATH, PRISM_CONFIG['host'], CONFIG_FOLDER)
	subprocess.call(script, shell=True)

def ping_version(output=False):
	global PRISM_VERSIONING

	should_check = True
	if 'last_check' in PRISM_VERSIONING:
		should_check = ((datetime.now() - datetime.strptime(PRISM_VERSIONING['last_check'], "%Y-%m-%d %H:%M:%S")).seconds >= 60 * 60 * 2)

	if output or should_check:
		prism.poof('Collecting version info...')

	if should_check:
		rate_limited, dev_changes, recent_releases, num_releases = get_new_versions(prism.__version__)

		if rate_limited:
			prism.output('Rate limited. Version info not checked.')

			# If no values made yet, apply some defaults
			if 'dev_changes' not in PRISM_VERSIONING:
				PRISM_VERSIONING['dev_changes'] = []
			if 'recent_releases' not in PRISM_VERSIONING:
				PRISM_VERSIONING['recent_releases'] = []
			if 'num_releases' not in PRISM_VERSIONING:
				PRISM_VERSIONING['num_releases'] = 0
		else:
			# Reset and reapply cached versioning info
			PRISM_VERSIONING['dev_changes'] = []
			PRISM_VERSIONING['recent_releases'] = []
			PRISM_VERSIONING['num_releases'] = 0

			if 'dev_changes' is not None:
				PRISM_VERSIONING['dev_changes'] = dev_changes
			if 'recent_releases' is not None:
				PRISM_VERSIONING['recent_releases'] = recent_releases
			if 'num_releases' is not None:
				PRISM_VERSIONING['num_releases'] = num_releases

			if 'dev_changes' is not None or 'recent_releases' is not None or 'num_releases' is not None:
				PRISM_VERSIONING['last_check'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	if output or should_check:
		if len(PRISM_VERSIONING['dev_changes']) > 0:
			prism.output('%s development commit(s) since the latest version.' % len(PRISM_VERSIONING['dev_changes']))
		if len(PRISM_VERSIONING['recent_releases']) != 0:
			prism.poof('Current version: %s' % prism.__version__)
			if prism.__version__ != PRISM_VERSIONING['recent_releases'][0]['name']:
				prism.output('Your version is out of date. Latest version is %s' % PRISM_VERSIONING['recent_releases'][0]['name'])
			prism.paaf()
		prism.paaf()
