import json
import os
import sys

import prism


PANEL_PID = None

PRISM_PATH = None
CORE_PLUGINS_PATH = None
PLUGINS_PATH = None
TMP_PATH = None

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
		'widgets': []
	}

# Confing utilities
def load_config(path):
	# Load config
	if not os.path.exists(path):
		return {}
	return json.loads(open(path).read())

def save_config(path, config):
	if len(config) == 0:
		if os.path.exists(path):
			os.remove(path)
	else:
		# Write to config
		with open(path, 'w') as file:
			json.dump(config, file, indent=4, sort_keys=True)

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
	global PANEL_PID, PRISM_PATH, CORE_PLUGINS_PATH, PLUGINS_PATH, TMP_PATH,
			CONFIG_FOLDER, CONFIG_FILE, CONFIG_FOLDER_PLUGINS, PRISM_CONFIG

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

	# Load Prism's config
	CONFIG_FOLDER = os.path.join(PRISM_PATH, 'config')
	if not os.path.exists(CONFIG_FOLDER):
		os.makedirs(CONFIG_FOLDER)
	CONFIG_FILE = os.path.join(CONFIG_FOLDER, 'config.json')

	CONFIG_FOLDER_PLUGINS = os.path.join(CONFIG_FOLDER, 'plugins')
	if not os.path.exists(CONFIG_FOLDER_PLUGINS):
		os.makedirs(CONFIG_FOLDER_PLUGINS)

	prism.output('')

	# Generate default config values if the file doesn't exist
	# Also, prompt and generate a few of the config values that
	# must be done on first run.
	if not os.path.exists(CONFIG_FILE):
		# I have no idea what came over me when making this section,
		# but it's fabulous and I loved every second of it. I hope
		# I never have to change it. xD
		import time
		prism.output('Hello, I\'m Prism! I\'ll attempt to help you manage your server with ease~ Currently, I\'m only built to manage Python based websites, but in the future I might be taught more!')

		prism.output('Now that all the formalities are out of the way, lets get started on my inital setup.')

		# IP Address/Hostname prompt
		import socket
		host = socket.gethostbyname(socket.gethostname())
		prism.output('In order for me to establish a secure connection, I must generate an SSL certificate. Please input the IP address of your server. This will be the address that you use to connect to my web interface. I attempted to find your address; is %s correct? If not, please enter the corrected address. Otherwise press enter.' % host)
		PRISM_CONFIG['host'], used_default = prism.get_input('Hostname', default=host)

		if used_default:
			prism.output('')
			prism.output('I was right? Yay!')

		# Secret generation
		prism.output('')
		prism.output('Okay! *checks that off the list* Now, should I generate a secret for you? If not, please tell me one now.')
		secret_key, used_default = prism.get_input('Secret Key')

		prism.output('')
		if used_default:
			secret_key = prism.generate_random_string(32)
			prism.output('Hmm. Okay, I\'ll try... *thinks for a moment* How about %s? Yeah, that\'ll do. Why couldn\'t you do that? It\'s kinda fun!' % secret_key)
		else:
			prism.output('Oooo, %s? That\'s a very nice secret. I\'ll try not to tell anyone. *winks*' % secret_key)

		PRISM_CONFIG['secret_key'] = secret_key

		# Username and Password prompt
		prism.output('')

		prism.output('Okay, next. (Don\'t worry, I\'m as bored as you...) It says here I need to ask you for a username and password. So?')
		PRISM_CONFIG['username'], username_used_default = prism.get_input('Username', default='admin')
		if used_default:
			time.sleep(.5)
			prism.output('Fabulous.')
			time.sleep(1)

		PRISM_CONFIG['password'], password_used_default = prism.get_input('Password', default='default')
		if used_default:
			time.sleep(.5)
			prism.output('Amazing.')
			time.sleep(1)

		prism.output('')
		if username_used_default and password_used_default:
			prism.output('You\'ve done this before, haven\'t you? :3')
			time.sleep(.5)
			prism.output('...')
			time.sleep(.75)
			prism.output('...')
			time.sleep(1)
			prism.output('...')
			time.sleep(1)
			prism.output('Okay, I guess. In reality, that\'s really insecure, but whatever. Just don\'t do that in production, please? Either way, I\'m not responsible for your amazing security.')
			time.sleep(5)
			prism.output('... Anyways...')
			prism.output('')

		prism.output('All done! I\'ll write this to the config file and send you on your way~')
	else:
		# Load prism's config
		PRISM_CONFIG = load_config(CONFIG_FILE)

		# Make sure some VERY imporant values are set
		if 'secret_key' not in PRISM_CONFIG:
			prism.output('Your secret appears to be absent from your config! Don\'t worry, I\'ll generate one for you, just be mindful not to remove it in the future...')
			PRISM_CONFIG['secret_key'] = prism.generate_random_string(32)

		if 'host' not in PRISM_CONFIG:
			import socket
			host = socket.gethostbyname(socket.gethostname())
			prism.output('You don\'t have a host set in your config. Please tell me one, or nothing will work! ;-;')
			PRISM_CONFIG['host'], used_default = prism.get_input('Hostname', default=host)

		if 'username' not in PRISM_CONFIG:
			prism.output('You seem to have disappeared from the config! Who are you again?')
			PRISM_CONFIG['username'], used_default = prism.get_input('Username', default='admin')

		if 'password' not in PRISM_CONFIG:
			prism.output('You uhh... You don\'t have a password. Please set it before you continue.')
			PRISM_CONFIG['password'], used_default = prism.get_input('Password', default='default')

	# Detect if the password isn't md5'd. If not, hash it. This allows
	# the user to reset their password at any time within the config.
	if not prism.is_crypted(PRISM_CONFIG['password']):
		PRISM_CONFIG['password'] = prism.crypt_string(PRISM_CONFIG['password'])

	save_config(CONFIG_FILE, PRISM_CONFIG)

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
