import os
import nginx
import flask

import prism
from prism.api.view import BaseView, subroute

from . import JackPlugin
from .site_configs import ConfigWrapper


class JackCreateSiteView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/create', title='New Site',
                                menu={'id': 'jack.create', 'icon': 'plus', 'order': 0,
                                        'parent': {'id': 'jack', 'text': 'Jack', 'icon': 'plug'}})

    def get(self, request):
        return ('create.html', {'default_configs': JackPlugin.get().get_default_configs()})

    def post(self, request):
        if not request.form['site_id']:
            flask.flash('No site ID specified.', 'error')
            return ('jack.JackCreateSiteView')

        if JackPlugin.get().get_config(request.form['site_id']):
            flask.flash('A site with that ID already exists!', 'error')
            return ('jack.JackCreateSiteView')

        site_type = request.form['site_type']

        site_config = JackPlugin.get().get_default_config(site_type)
        if site_config == None:
            flask.flash('Unknown config type!', 'error')
            return ('jack.JackCreateSiteView')

        options = []
        for option in site_config.options:
            if not option[0] in request.form or not request.form[option[0]]:
                flask.flash('Did not fill in all required values.', 'error')
                return ('jack.JackCreateSiteView')
            options.append(request.form[option[0]])

        nginx_config = nginx.Conf()
        nginx_config.add(nginx.Comment('config=%s' % site_config.type_id))
        if not site_config.generate_config(nginx_config, *options):
            return ('jack.JackCreateSiteView')
        nginx.dumpf(nginx_config, JackPlugin.get().get_config_loc(request.form['site_id']))

        prism.os_command('systemctl restart nginx.service')

        return ('core.RestartView')

class JackSiteOverviewView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/view', title='View Site')

    @subroute('/<site_id>')
    def get(self, request, site_id):
        if not JackPlugin.get().get_config(site_id):
            flask.flash('A site with that ID doesn\'t exist!', 'error')
            return ('dashboard.DashboardView')
        wrapper = ConfigWrapper(site_id, JackPlugin.get().get_config(site_id))
        return ('view/%s.html' % wrapper.config.type_id, {'config': wrapper})

    @subroute('/<site_id>')
    def post(self, request, site_id):
        if not JackPlugin.get().get_config(site_id):
            flask.flash('A site with that ID doesn\'t exist!', 'error')
            return ('dashboard.DashboardView')

        if 'delete' in request.form:
            os.remove(os.path.join(JackPlugin.get().config('sites-loc', '/etc/nginx/conf.d/'), site_id + '.conf'))
        else:
            if not request.form['url_endpoint']:
                error = 'Must specify a URL endpoint.'
            else:
                wrapper = ConfigWrapper(site_id, JackPlugin.get().get_config(site_id))
                wrapper.nginx.server.keys[2].value = request.form['url_endpoint']
                error = wrapper.config.post(request, wrapper.nginx)
            if error:
                flask.flash(error, 'error')
                return ('jack.JackSiteOverviewView', {'site_id': site_id})
            else:
                nginx.dumpf(wrapper.nginx, JackPlugin.get().get_config_loc(site_id))

        prism.os_command('systemctl restart nginx.service')
        return ('core.RestartView')
