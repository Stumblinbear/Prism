import pwd
from datetime import datetime
import os
import sys
import socket
import time

import prism
import prism.logging as logging
from .version import get_new_versions
from .config import JSONConfig, LocaleConfig

# The process ID of the panel
PANEL_PID = None
# The path to prism's base folder
PRISM_PATH = None
# The path to the tmp directory in prism's base folder
TMP_PATH = None

# Holds information regarding the current and dev versions
PRISM_VERSIONING = None

# Prism's own config information
CONFIG_FOLDER = None
PRISM_CONFIG = {
		'dev_mode': False,
		'secret_key': None,
		'host': None,
		'enabled': [],
		'locale': 'en_US',
		'enabled_plugins': []
	}

# Plugin path information
CORE_PLUGINS_PATH = None
PLUGINS_PATH = None
CONFIG_FOLDER_PLUGINS = None

# The current locale selected
PRISM_LOCALE = None

def is_dev():
	return 'dev_mode' in PRISM_CONFIG and PRISM_CONFIG['dev_mode']

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

	logging.info('Currently running in %s' % PRISM_PATH)
	logging.output()

	PRISM_VERSIONING = JSONConfig(path=os.path.join(TMP_PATH, 'VERSIONING-INFO'))

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
		logging.output(PRISM_LOCALE['start.hello.1'])
		logging.output(PRISM_LOCALE['start.hello.2'])
		subst = {}

		# IP Address/Hostname prompt
		subst['host'] = socket.gethostbyname(socket.gethostname())
		logging.output(PRISM_LOCALE['start.host'].format(**subst))
		PRISM_CONFIG['host'], used_default = prism.get_input(PRISM_LOCALE['start.host.prompt'], default=subst['host'])

		if used_default:
			logging.output()
			logging.output(PRISM_LOCALE['start.host.correct'])

		# Secret generation
		logging.output()
		logging.output(PRISM_LOCALE['start.secret'])
		subst['secret_key'], used_default = prism.get_input(PRISM_LOCALE['start.secret.prompt'])

		logging.output()
		if used_default:
			subst['secret_key'] = prism.generate_random_string(32)
			logging.output(PRISM_LOCALE['start.secret.generate'].format(**subst))
		else:
			logging.output(PRISM_LOCALE['start.secret.done'].format(**subst))

		PRISM_CONFIG['secret_key'] = subst['secret_key']

		# Dev check
		logging.output()
		logging.output(PRISM_LOCALE['start.dev_mode'])
		PRISM_CONFIG['dev_mode'] = prism.get_yesno(PRISM_LOCALE['start.dev_mode.prompt'])

		logging.output()
		logging.output(PRISM_LOCALE['start.done'])
		logging.output()

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
			logging.output(PRISM_LOCALE['start.missing.secret'])
			PRISM_CONFIG['secret_key'] = prism.generate_random_string(32)
			logging.output()

		if 'host' not in PRISM_CONFIG:
			host = socket.gethostbyname(socket.gethostname())
			logging.output(PRISM_LOCALE['start.missing.host'])
			PRISM_CONFIG['host'], used_default = prism.get_input(PRISM_LOCALE['start.host.prompt'], default=host)
			logging.output()

def post_init():
	try:
		pwd.getpwnam('prism')
	except KeyError:
		import crypt
		passwd = crypt.crypt(PRISM_CONFIG['secret_key'], "22")
		prism.os_command("useradd -p " + passwd + " -s /bin/bash -d /home/prism -m -c PrismCP prism")

	import prism.login as prism_login
	if prism_login.User.query.count() == 0:
		logging.output()

		# Username and Password prompt
		logging.output(PRISM_LOCALE['start.login.username'])
		username, used_default = prism.get_input(PRISM_LOCALE['start.login.username.prompt'], default='admin')
		password, used_default = prism.get_password(PRISM_LOCALE['start.login.password.prompt'], default='password')

		if used_default:
			logging.output()

			logging.output(PRISM_LOCALE['start.login.password.default.1'])
			time.sleep(2)
			logging.output(PRISM_LOCALE['start.login.password.default.2'])
			time.sleep(5)
			logging.output(PRISM_LOCALE['start.login.password.default.3'])

		logging.output()
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
	prism.os_command(script)

def ping_version(output=False):
	global PRISM_VERSIONING

	should_check = True
	if 'last_check' in PRISM_VERSIONING:
		should_check = ((datetime.now() - datetime.strptime(PRISM_VERSIONING['last_check'], "%Y-%m-%d %H:%M:%S")).seconds >= 60 * 60 * 2)

	if output or should_check:
		logging.up('Collecting version info...')

	if should_check:
		rate_limited, dev_changes, recent_releases, num_releases = get_new_versions(prism.__version__)

		if rate_limited:
			logging.error('Rate limited. Version info not checked.')

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
		if PRISM_VERSIONING['dev_changes'] is None:
			logging.error('Failed to check development version.')
		elif len(PRISM_VERSIONING['dev_changes']) > 0:
			logging.info('%s development commit(s) since the latest version.' % len(PRISM_VERSIONING['dev_changes']))
		if PRISM_VERSIONING['recent_releases'] is None:
			logging.error('Failed to check for latest version.')
		elif len(PRISM_VERSIONING['recent_releases']) != 0:
			logging.info('Current version: %s' % prism.__version__)
			if prism.__version__ != PRISM_VERSIONING['recent_releases'][0]['name']:
				logging.error('Your version is out of date. Latest version is %s' % PRISM_VERSIONING['recent_releases'][0]['name'])
			logging.down()
		logging.down()
