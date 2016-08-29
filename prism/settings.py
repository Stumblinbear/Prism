import os
import sys
import socket
import time

import prism
from .config import JSONConfig, LocaleConfig


PANEL_PID = None
PRISM_PATH = None
TMP_PATH = None

CORE_PLUGINS_PATH = None
PLUGINS_PATH = None
CONFIG_FOLDER_PLUGINS = None

CONFIG_FOLDER = None
CONFIG_FILE = None
PRISM_CONFIG = {
		'first_run': True,
		'secret_key': None,
		'host': None,
		'username': 'admin',
		'password': 'admin',
		'enabled': [],
		'locale': 'en_US'
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
	global PANEL_PID, PRISM_PATH, TMP_PATH, CORE_PLUGINS_PATH, PLUGINS_PATH, \
			CONFIG_FOLDER_PLUGINS, CONFIG_FOLDER, CONFIG_FILE, PRISM_CONFIG, PRISM_LOCALE

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

	# Load Prism's config
	CONFIG_FOLDER = os.path.join(PRISM_PATH, 'config')
	if not os.path.exists(CONFIG_FOLDER):
		os.makedirs(CONFIG_FOLDER)
	CONFIG_FILE = os.path.join(CONFIG_FOLDER, 'config.json')

	CONFIG_FOLDER_PLUGINS = os.path.join(CONFIG_FOLDER, 'plugins')
	if not os.path.exists(CONFIG_FOLDER_PLUGINS):
		os.makedirs(CONFIG_FOLDER_PLUGINS)

	PRISM_LOCALE = LocaleConfig(PRISM_PATH)

	# Generate default config values if the file doesn't exist
	# Also, prompt and generate a few of the config values that
	# must be done on first run.
	if not os.path.exists(CONFIG_FILE):
		# I have no idea what came over me when making this section,
		# but it's fabulous and I loved every second of it. I hope
		# I never have to change it. xD
		prism.output(PRISM_LOCALE['start.hello.1'])
		prism.output(PRISM_LOCALE['start.hello.2'])

		# IP Address/Hostname prompt
		host = socket.gethostbyname(socket.gethostname())
		prism.output(PRISM_LOCALE['start.host'] % host)
		PRISM_CONFIG['host'], used_default = prism.get_input(PRISM_LOCALE['start.host.prompt'], default=host)

		if used_default:
			prism.output('')
			prism.output(PRISM_LOCALE['start.host.correct'])

		# Secret generation
		prism.output('')
		prism.output(PRISM_LOCALE['start.secret'])
		secret_key, used_default = prism.get_input(PRISM_LOCALE['start.secret.prompt'])

		prism.output('')
		if used_default:
			secret_key = prism.generate_random_string(32)
			prism.output(PRISM_LOCALE['start.secret.generate'] % secret_key)
		else:
			prism.output(PRISM_LOCALE['start.secret.done'] % secret_key)

		PRISM_CONFIG['secret_key'] = secret_key

		# Username and Password prompt
		prism.output('')
		prism.output(PRISM_LOCALE['start.login.username'])
		PRISM_CONFIG['username'], used_default = prism.get_input(PRISM_LOCALE['start.login.username.prompt'], default='admin')
		PRISM_CONFIG['password'], used_default = prism.get_input(PRISM_LOCALE['start.login.password.prompt'], default='password')
		if used_default:
			prism.output(PRISM_LOCALE['start.login.password.default.1'])
			time.sleep(2)
			prism.output(PRISM_LOCALE['start.login.password.default.2'])
			time.sleep(5)
			prism.output(PRISM_LOCALE['start.login.password.default.3'])
			prism.output('')

		prism.output('')
		prism.output(PRISM_LOCALE['start.done'])
	else:
		# Load prism's config
		PRISM_CONFIG = JSONConfig(path=CONFIG_FILE)

		if 'locale' not in PRISM_CONFIG:
			PRISM_CONFIG['locale'] = 'en_US'

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

		if 'username' not in PRISM_CONFIG:
			prism.output(PRISM_LOCALE['start.missing.username'])
			PRISM_CONFIG['username'], used_default = prism.get_input(PRISM_LOCALE['start.login.username.prompt'], default='admin')
			prism.output('')

		if 'password' not in PRISM_CONFIG:
			prism.output(PRISM_LOCALE['start.missing.password'])
			PRISM_CONFIG['password'], used_default = prism.get_input(PRISM_LOCALE['start.login.password.prompt'], default='password')
			prism.output('')

	# Detect if the password isn't md5'd. If not, hash it. This allows
	# the user to reset their password at any time within the config.
	if not prism.is_crypted(PRISM_CONFIG['password']):
		PRISM_CONFIG['password'] = prism.crypt_string(PRISM_CONFIG['password'])

	PRISM_CONFIG.save()

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
