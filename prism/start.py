import prism

def startup(args=None):
	if __name__ != "__main__":
		prism.output('Script attempted to import "start". This should never be done.')
		exit()

	import os, sys
	prism.output('----------=Prism=----------')
	# Prism is the script that holds the main instanced app and the config
	import settings
	settings.init(os.getpid())

	prism.output('Starting Prism')
	prism.poof()

	from flask import Flask
	prism.output('Initializing Flask')
	flask_app = Flask(__name__, template_folder='templates')
	flask_app.secret_key = settings.PRISM_CONFIG['secret_key']


	prism.poof()
	prism.output('Overloading jinja templating')
	import jinja2
	from flask.templating import DispatchingJinjaLoader

	class ModifiedLoader(DispatchingJinjaLoader):
		def _iter_loaders(self, template):
			for blueprint in self.app.iter_blueprints():
				loader = blueprint.jinja_loader
				if loader is not None:
					yield blueprint, loader
			
			loader = self.app.jinja_loader
			if loader is not None:
				yield self.app, loader

	flask_app.jinja_options = Flask.jinja_options.copy() 
	flask_app.jinja_options['loader'] = ModifiedLoader(flask_app)

	flask_app.jinja_env.trim_blocks = True
	flask_app.jinja_env.lstrip_blocks = True

	flask_app.jinja_env.add_extension('jinja2.ext.loopcontrols')

	prism.init(flask_app, settings.PRISM_CONFIG)

	prism.output('Initializing Flask-Sijax')
	import flask_sijax
	flask_app.config['SIJAX_STATIC_PATH'] = os.path.join(settings.PRISM_PATH, 'static/js/sijax/')
	flask_app.config['SIJAX_JSON_URI'] = '/static/js/sijax/json2.js'
	flask_sijax.Sijax(flask_app)


	prism.output('Initializing Flask-Menu')
	import flask_menu
	flask_menu.Menu(app=flask_app)
	prism.paaf()

	prism.output('Loading pages')
	import login, views


	prism.output('Loading plugins')

	prism.poof()
	settings.import_folders(settings.PLUGIN_PATH)

	plugin_manager = prism.get_plugin_manager()
	plugin_manager.load_plugins(settings.PLUGIN_PATH)

	prism.output('Registering blueprints')
	plugin_manager.register_blueprints(flask_app)
	prism.paaf()

	prism.paaf()

	settings.save_config()

	prism.output('Verifying SSL')
	has_ssl = False

	try:
		from OpenSSL import SSL
		has_ssl = True
	except ImportError:
		pass

	if has_ssl:
		# Generate certificate
		if not os.path.exists(os.path.join(settings.CONFIG_FOLDER, 'prism-ssl.crt')) or not os.path.exists(os.path.join(settings.CONFIG_FOLDER, 'prism-ssl.key')):
			prism.poof()
			
			prism.output('Generating SSL certificate')
			prism.poof()
			settings.generate_certificate()
			prism.paaf()
			
			prism.paaf()
		
		# Finally, start Prism under a self-signed SSL connection
		flask_app.run(host='0.0.0.0', port=9000, debug=True, ssl_context=('config/prism-ssl.crt', 'config/prism-ssl.key'))
	else:
		prism.output('Warning: Prism is starting under an insecure connection!')
		flask_app.run(host='0.0.0.0', port=9000, debug=True)

if __name__ == "__main__":
    startup()