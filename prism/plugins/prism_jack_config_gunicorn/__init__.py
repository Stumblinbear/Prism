import flask
import os
import shutil
import prism
from prism.api.plugin import BasePlugin
from prism.pyversions import PythonVersions

from prism_crachit import Service
from prism_jack import JackPlugin, SiteTypeConfig

class JackGUnicornConfigPlugin(BasePlugin):
    pass

class GUnicornConfig(SiteTypeConfig):
    def __init__(self):
        SiteTypeConfig.__init__(self, 'gunicorn', 'GUnicorn', 'Use this option if you wish to set up a website created using Python scripts.', [('hostname', 'Hostname', 'example.com'), ('python', 'Python', [(str(key), str(key)) for i, key in enumerate(PythonVersions.get().versions)]), ('library', 'Library', [('flask', 'Flask'), ('django', 'Django')])])

    def create(self, site_config, site_id, hostname, python, library):
        if not hostname:
            return 'Must specify a hostname.'
        site_config['hostname'] = hostname
        site_config['locations']['/'] = {
                            'proxy_pass': 'http://unix:/var/www/%s/%s.sock' % (site_config['uuid'], site_config['uuid']),
                            'proxy_set_header' : (
                                            'Host $http_host',
                                            'X-Real-IP $remote_addr',
                                            'X-Forwarded-For $proxy_add_x_forwarded_for',
                                            'X-Forwarded-Proto $scheme')
                        }

        site_loc = os.path.join(JackPlugin.get().site_files_location, site_config['uuid'])
        script_loc = os.path.join(site_loc, 'script')

        # Copy the default files to the site's directory
        default_path = os.path.join(JackGUnicornConfigPlugin.get().plugin_folder, 'default/%s' % library)
        if not os.path.exists(script_loc):
            if os.path.exists(default_path):
                shutil.copytree(default_path, script_loc)
            else:
                os.makedirs(script_loc)

        python_version = None
        for version in PythonVersions.get().versions:
            if str(version) == python:
                python_version = version
        if python_version is None:
            return 'The selected python version doesn\'t exist.'

        # Create the virtualenv as the prism user
        out, err = prism.os_commands([
                    'cd %s' % site_loc,
                    'virtualenv -p "%s" %s_env' % (python_version.path, site_config['uuid']),
                    'source %s_env/bin/activate' % site_config['uuid'],
                    'pip install gunicorn %s' % library,
                    'deactivate'
                ], scl=python_version.scl, user='prism')
        if err:
            prism.error(err)
            return 'Problem creating virtual environment.'

        # GUnicorn options
        site_config['gunicorn'] = {
                        'workers': 3,
                        'python': {
                            'path': python_version.path,
                            'scl': python_version.scl
                        }
                    }

    def save(self, site_config):
        site_loc = os.path.join(JackPlugin.get().site_files_location, site_config['uuid'])
        script_loc = os.path.join(site_loc, 'script')

        exec_start = '%s/%s_env/bin/gunicorn --workers %i --bind unix:../%s.sock -m 007 wsgi' % (site_loc, site_config['uuid'], site_config['gunicorn']['workers'], site_config['uuid'])
        if site_config['gunicorn']['python']['scl']:
            exec_start = '/usr/bin/scl enable %s "%s"' % (site_config['gunicorn']['python']['scl'], exec_start)

        # Create the service
        service = Service('gunicorn-%s' % site_config['uuid'],
                    {
                        'Unit': {
                            'Description': 'GUnicorn instance to serve %s (%s)' % (site_config['id'], site_config['uuid']),
                            'After': 'network.target'
                        },
                        'Service': {
                            'User': 'prism',
                            'Group': 'nginx',
                            'WorkingDirectory': script_loc,
                            'Environment': '"PATH=%s/bin"' % os.path.join(site_loc, site_config['uuid'] + '_env'),
                            'ExecStart': exec_start
                        },
                        'Install': {
                            'WantedBy': 'multi-user.target'
                        }
                    }
                )
        service.save()
        # Start the service
        service.start()

    def delete(self, site_config):
        site_loc = os.path.join(JackPlugin.get().site_files_location, site_config['uuid'])
        prism.os_command('rm -rf %s' % site_loc)

        Service('gunicorn-%s' % site_config['uuid']).delete()

    def update(self, request, site_config):
        site_config['gunicorn']['workers'] = int(request.form['workers'])

    def post(self, request, site_config):
        if 'gunicorn_restart' in request.form:
            Service('gunicorn-%s' % site_config['uuid']).restart()
            flask.flash('GUnicorn is restarting...', 'danger')
        elif 'gunicorn_start' in request.form:
            print(Service('gunicorn-%s' % site_config['uuid']).start())
            flask.flash('Attempting to start GUnicorn...', 'warning')
        elif 'gunicorn_enable' in request.form:
            print(Service('gunicorn-%s' % site_config['uuid']).enable())
            flask.flash('Setting GUncorn to start on boot...', 'success')
        elif 'gunicorn_disable' in request.form:
            print(Service('gunicorn-%s' % site_config['uuid']).disable())
            flask.flash('GUnicorn will no longer start on boot...', 'danger')
        pass

    def get(self, site_config):
        service = Service('gunicorn-%s' % site_config['uuid'])
        return {'status': service.status, 'enabled': service.enabled}
