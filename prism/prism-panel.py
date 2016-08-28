# -*- coding: utf-8 -*-
#
# *****************************************************************************
# Copyright (c) 2016 by the authors, see LICENSE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
# ****************************************************************************

import os
import sys

from flask import Flask
from flask.templating import DispatchingJinjaLoader

import jinja2
import flask_menu
import flask_sijax

import prism


def main(args=None):
    prism.output('----------=Prism=----------')
    import settings
    settings.init(os.getpid())

    prism.poof('Starting Prism')

    prism.output('Initializing Flask')
    flask_app = Flask(__name__, template_folder='templates')
    flask_app.secret_key = settings.PRISM_CONFIG['secret_key']

    # Overloading jinja's default templating
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

    # Automatically trip and strip jinja template lines
    flask_app.jinja_env.trim_blocks = True
    flask_app.jinja_env.lstrip_blocks = True

    # Add in some for loop controls
    flask_app.jinja_env.add_extension('jinja2.ext.loopcontrols')

    # Add sijax as a flask plugin
    flask_app.config['SIJAX_STATIC_PATH'] = os.path.join(settings.PRISM_PATH, 'static/js/sijax/')
    flask_app.config['SIJAX_JSON_URI'] = '/static/js/sijax/json2.js'
    flask_sijax.Sijax(flask_app)

    # Add flask menu
    flask_menu.Menu(app=flask_app)

    prism.init(flask_app, settings.PRISM_CONFIG)

    import login
    import views

    # Load in prism's plugins
    prism.poof('Starting plugin manager')
    prism.plugin_manager()
    prism.paaf()

    # Save the config in case anything changed
    settings.save_config(settings.CONFIG_FILE, settings.PRISM_CONFIG)

    prism.output('Verifying SSL')
    has_ssl = False

    try:
        from OpenSSL import SSL
        has_ssl = True
    except ImportError:
        pass

    if has_ssl:
        ssl_files_exist = os.path.exists(os.path.join(settings.CONFIG_FOLDER, 'prism-ssl.crt'))
        if ssl_files_exist:
            ssl_files_exist = os.path.exists(os.path.join(settings.CONFIG_FOLDER, 'prism-ssl.key'))
        # Generate certificate
        if not ssl_files_exist:
            prism.poof()

            prism.poof('Generating SSL certificate')
            settings.generate_certificate()
            prism.paaf()

            prism.paaf()

        # Finally, start Prism under a self-signed SSL connection
        flask_app.run(host='0.0.0.0', port=9000, debug=True,
                        ssl_context=('config/prism-ssl.crt', 'config/prism-ssl.key'))
    else:
        prism.output('Warning: Prism is starting under an insecure connection!')
        flask_app.run(host='0.0.0.0', port=9000, debug=True)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
