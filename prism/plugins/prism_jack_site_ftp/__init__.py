import flask
import prism
from prism.api.plugin import BasePlugin

from prism_jack import SiteTab

class JackFTPPlugin(BasePlugin):
    def init(self, prism_state):
        self.users = self.config('users', {})

        file_str = None
        with open('/etc/vsftpd/vsftpd.conf') as f:
            file_str = f.read()

        if file_str is not None:
            file_str = file_str.replace('anonymous_enable=YES', 'anonymous_enable=NO')
            file_str = file_str.replace('local_enable=NO', 'local_enable=YES')
            file_str = file_str.replace('write_enable=NO', 'write_enable=YES')
            file_str = file_str.replace('#chroot_local_user=YES', 'chroot_local_user=YES')
            if 'allow_writeable_chroot' not in file_str:
                file_str = file_str + '\nallow_writeable_chroot=YES\n'

            with open('/etc/vsftpd/vsftpd.conf', 'w') as f:
                f.write(file_str)

            prism.os_command('systemctl restart vsftpd')

    def user_add(self, site_uuid, username, password, comment, use_sftp):
        prism.os_command('useradd %s -d /var/www/%s -G nginx -c "Jack(%s) %s" %s' % ('' if use_sftp else '-s /sbin/nologin', site_uuid, site_uuid, comment if comment is not None else '', username))
        prism.os_command('echo %s | passwd %s --stdin' % (password, username))
        if site_uuid not in self.users:
            self.users[site_uuid] = {}
        self.users[site_uuid][username] = {'sftp': use_sftp, 'password': password, 'comment': comment}
        self.config['users'] = self.users

    def user_del(self, site_uuid, username):
        prism.os_command('userdel %s' % username)
        del self.users[site_uuid][username]
        if len(self.users) == 0:
            del self.users[site_uuid]
        self.config['users'] = self.users

class FTPTab(SiteTab):
    def __init__(self):
        SiteTab.__init__(self, 'FTP')

    def render(self, site_config):
        ftp_users = {}
        if site_config['uuid'] in JackFTPPlugin.get().users:
            ftp_users = JackFTPPlugin.get().users[site_config['uuid']]
        return ('tabs/ftp.html', {'ftp_users': ftp_users, 'generated_password': prism.generate_random_string(32)})

    def post(self, request, site_config):
        if 'user_new' in request.form:
            if not request.form['user_username']:
                return 'Username not specified.'
            if not request.form['user_password']:
                return 'Password not specified.'
            if site_config['uuid'] in JackFTPPlugin.get().users and request.form['user_username'] in JackFTPPlugin.get().users[site_config['uuid']]:
                return 'User already exists.'
            user_sftp = request.form['user_sftp'] == 'on' if 'user_sftp' in request.form else False
            JackFTPPlugin.get().user_add(site_config['uuid'], request.form['user_username'], request.form['user_password'], request.form['user_comment'] if 'user_comment' in request.form else None, user_sftp)
            flask.flash('New user created: %s' % request.form['user_username'])
        elif 'user_del' in request.form:
            JackFTPPlugin.get().user_del(site_config['uuid'], request.form['user_del'])
            flask.flash('User deleted: %s' % request.form['user_del'])

    def deleted(self, site_config):
        if site_config['uuid'] in JackFTPPlugin.get().users:
            for username in JackFTPPlugin.get().users[site_config['uuid']]:
                JackFTPPlugin.get().user_remove(site_config['uuid'], username)
