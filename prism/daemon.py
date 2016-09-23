import os

from flask import Flask
from flask.templating import DispatchingJinjaLoader

import jinja2
import flask_menu

import prism
import prism.settings


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
	def start(self, *args):
		prism.output('----------=Prism=----------')
		prism.settings.init(os.getpid())

		prism.poof('Starting Prism')

		self.init_flask()
		self.jinja_options()
		self.init_flask_plugins()
		self.init_prism()

		prism.settings.post_init()

		self.start_http()

		return 0

	def init_flask(self):
		prism.output('Initializing Flask')
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
		prism.poof('Starting plugin manager')
		prism.plugin_manager()
		prism.paaf()

	def start_http(self):
		prism.output('Verifying SSL')
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
				prism.poof()

				prism.poof('Generating SSL certificate')
				prism.settings.generate_certificate()
				prism.paaf()

				prism.paaf()

			# Finally, start Prism under a self-signed SSL connection
			self.flask_app.run(host='0.0.0.0', port=9000, debug=prism.settings.is_dev(),
							ssl_context=(ssl_crt, ssl_key))
		else:
			prism.output('Warning: Prism is starting under an insecure connection!')
			self.flask_app.run(host='0.0.0.0', port=9000, debug=prism.settings.is_dev())
