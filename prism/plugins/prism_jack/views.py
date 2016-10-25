import os
import nginx
import flask

import prism
from prism.api.view import BaseView, subroute

from . import JackPlugin


class JackCreateSiteView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/create', title='New Site',
                                menu={'id': 'jack.create', 'icon': 'plus', 'order': 0,
                                        'parent': {'id': 'jack', 'text': 'Jack', 'icon': 'plug'}})

    def get(self, request):
        return ('create.html', {'default_configs': JackPlugin.get().default_configs})

    def post(self, request):
        # Every site needs a site ID. If it's empty, die.
        if not request.form['site_id']:
            flask.flash('No site ID specified.', 'error')
            return ('jack.JackCreateSiteView')

        # Fetch the defined default config. If none exists, die.
        default_config = JackPlugin.get().get_default_config(request.form['site_type'])
        if default_config is None:
            flask.flash('Unknown config type!', 'error')
            return ('jack.JackCreateSiteView')

        # Verify all the defined options in the config were filled out. If not, die.
        options = []
        for option in default_config.options:
            if not option[0] in request.form or not request.form[option[0]]:
                flask.flash('Did not fill in all required values.', 'error')
                return ('jack.JackCreateSiteView')
            options.append(request.form[option[0]])

        # Create the site using the NginxManager. This is also where the
        # generate function in the default config is called
        site_config = JackPlugin.get().nginx.create_site(default_config, request.form['site_id'], options)
        JackPlugin.get().nginx.rebuild_sites()
        return ('jack.JackSiteOverviewView', {'site_uuid': site_config['uuid']})

class JackSiteOverviewView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/view', title='View Site')

    @subroute('/<site_uuid>')
    def get(self, request, site_uuid=None):
        # If a valid site uuid wasn't specified, die.
        if site_uuid is None or site_uuid not in JackPlugin.get().nginx.configs:
            flask.flash('A site with that ID doesn\'t exist!', 'error')
            return ('dashboard.DashboardView')
        config = JackPlugin.get().nginx.configs[site_uuid]
        return ('view/%s.html' % config['type'], {'config': config, 'tabs': JackPlugin.get().site_tabs})

    @subroute('/<site_uuid>')
    def post(self, request, site_uuid):
        # If a valid site uuid wasn't specified, die.
        if not JackPlugin.get().nginx.configs[site_uuid]:
            flask.flash('A site with that ID doesn\'t exist!', 'error')
            return ('dashboard.DashboardView')

        # If a tab was submitted, handle it
        if 'tab' in request.form:
            pass
        # If the site was set to be deleted
        elif 'delete' in request.form:
            # Delete it. Duh.
            JackPlugin.get().nginx.delete_site(site_uuid)
            return ('dashboard.DashboardView')
        # If the first tab was submitted
        elif 'update' in request.form:
            if not request.form['hostname']:
                error = 'Must specify a hostname.'
            else:
                # Call the post method in the site's default config
                site_config = JackPlugin.get().nginx.configs[site_uuid]
                error = JackPlugin.get().get_default_config(site_config['type']).post(request, site_config)
            if error:
                flask.flash(error, 'error')
            else:
                # If all was sucessful, rebuild nginx's sites and reload
                JackPlugin.get().nginx.rebuild_sites()
        return ('jack.JackSiteOverviewView', {'site_uuid': site_uuid})