import os

from flask import Flask
from flask.templating import DispatchingJinjaLoader

import jinja2
import flask_menu

import prism
import prism.settings
import prism.logging as logging


class ModifiedLoader(DispatchingJinjaLoader):
	def _iter_loaders(self, template):
		for blueprint in self.app.iter_blueprints():
			loader = blueprint.jinja_loader
			if loader is not None:
				yield blueprint, loader

		loader = self.app.jinja_loader
		if loader is not None:
			yield self.app, loader

class Daemon:
	def __init__(self, should_bind=True):
		self.should_bind = should_bind

	def start(self, opts):
		logging.output('----------=\e[1mPrism\e[0m=----------')
		prism.settings.init(os.getpid())

		logging.up('Starting Prism')

		self.init_flask()
		self.jinja_options()
		self.init_flask_plugins()
		self.init_prism()

		prism.settings.post_init()

		self.start_http()

		return 0

	def init_flask(self):
		logging.output('Initializing Flask')
		self.flask_app = Flask(__name__, template_folder='templates')
		self.flask_app.secret_key = prism.settings.PRISM_CONFIG['secret_key']

	def jinja_options(self):
		# Override jinja's default templating
		self.flask_app.jinja_options = Flask.jinja_options.copy()
		self.flask_app.jinja_options['loader'] = ModifiedLoader(self.flask_app)

		# Automatically trip and strip jinja template lines
		self.flask_app.jinja_env.trim_blocks = True
		self.flask_app.jinja_env.lstrip_blocks = True

		# Add in some for loop controls
		self.flask_app.jinja_env.add_extension('jinja2.ext.loopcontrols')

	def init_flask_plugins(self):
		# Add flask menu
		flask_menu.Menu(app=self.flask_app)

	def init_prism(self):
		prism.init(self.flask_app, prism.settings.PRISM_CONFIG)

		# Load in prism's plugins
		logging.up('Starting plugin manager')
		prism.plugin_manager()
		logging.down()

	def start_http(self):
		logging.output('Verifying SSL')
		has_ssl = False

		try:
			from OpenSSL import SSL
			has_ssl = True
		except ImportError:
			pass

		if has_ssl:
			ssl_crt = os.path.join(prism.settings.CONFIG_FOLDER, 'prism-ssl.crt')
			ssl_key = os.path.join(prism.settings.CONFIG_FOLDER, 'prism-ssl.key')

			ssl_files_exist = os.path.exists(ssl_crt)
			if ssl_files_exist:
				ssl_files_exist = os.path.exists(ssl_key)

			# Generate certificate
			if not ssl_files_exist:
				logging.up()

				logging.up('Generating SSL certificate')
				prism.settings.generate_certificate()
				logging.down()

				logging.down()

			if self.should_bind:
				# Finally, start Prism under a self-signed SSL connection
				self.flask_app.run(host='::', port=9000, threaded=True, debug=prism.settings.is_dev(),
								ssl_context=(ssl_crt, ssl_key))
		else:
			if self.should_bind:
				logging.error('Warning: Prism is starting under an insecure connection!')
				self.flask_app.run(host='::', port=9000, threaded=True, debug=prism.settings.is_dev())
