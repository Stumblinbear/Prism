import os

import crontab
import crontabs
from crontab import CronTab
from crontabs import CronTabs
import psutil

import prism.helpers
import prism.settings
from prism.memorize import memorize
from prism.api.view import BaseView, subroute, View, RowElement, BoxElement, TableElement, TableExtendedElement


class SystemGeneralInfoView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/general', title='General Information',
                                menu={'id': 'system.overview', 'icon': 'circle', 'order': 0,
                                        'parent': {'id': 'system', 'text': 'System', 'icon': 'television'}})

    def get(self, request):
        return ('general_info.html')

class SystemUsersView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/users', title='Users',
                                menu={'id': 'system.users', 'icon': 'users'})

    def get(self, request):
        user_info = self.get_user_info()
        view = View()
        row = RowElement()

        row1box = BoxElement(title='users.list.header', icon='user', padding=False)
        row1box.add(TableExtendedElement(
                            ['users.list.id', 'users.list.group', 'users.list.username'],
                            [(
                                user_id,
                                user_info['groups'][user['group_id']]['name'] if user_info['groups'][user['group_id']]['name'] != user['name'] else '',
                                user['name'],
                                TableElement(content=[('user.info', user['info']),
                                            ('user.home', user['home']),
                                            ('user.shell', user['shell'])
                                        ])
                            ) for user_id, user in user_info['users'].items()]
                    ))
        row.add(row1box)

        row2box = BoxElement(title='groups.list.header', icon='users', padding=False)
        row2box.add(TableElement(
                        ['groups.list.id', 'groups.list.name', 'groups.list.users'],
                        [(group_id, group['name'], group['users']) for group_id, group in user_info['groups'].items()]
                    ))
        row.add(row2box)

        view.add(row)

        return view

    @memorize(60)
    def get_user_info(self):
        user_info = {'groups': {}, 'users': {}}
        with open("/etc/group", "r") as f:
            for line in f.readlines():
                info = line.replace('\n', ' ').replace('\r', '').split(':')
                user_info['groups'][info[2]] = {'name': info[0], 'passwd': info[1], 'users': info[3]}
        with open("/etc/passwd", "r") as f:
            for line in f.readlines():
                info = line.replace('\n', ' ').replace('\r', '').split(':')
                user_info['users'][info[2]] = {'name': info[0], 'passwd': info[1],
                                                'group_id': info[3], 'info': info[4],
                                                'home': info[5], 'shell': info[6]}
        return user_info

class SystemProcessesView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/processes', title='Processes',
                                menu={'id': 'system.processes', 'icon': 'cog'})

    @subroute('/<show>')
    def get(self, request, show=False):
        if show == 'all':
            show = True

        cpu_count = get_cpu_count()
        return ('processes.html', {
                                    'panel_pid': prism.settings.PANEL_PID,
                                    'cpu_count': cpu_count[0],
                                    'cpu_count_logical': cpu_count[1],
                                    'ram': psutil.virtual_memory()[0],
                                    'processes': self.get_processes(show,
                                                lambda x: x['memory_percent'] + x['cpu_percent'])
                                })

    @memorize(30)
    def get_processes(self, show=False, sort=None):
        process_list = []
        for proc in psutil.process_iter():
            if not show and ('rcuob/' in proc.name() or
                            'rcuos/' in proc.name() or
                            'scsi_' in proc.name() or
                            'xfs-' in proc.name() or
                            'xfs_' in proc.name() or
                            'kworker/' in proc.name()):
                continue
            try:
                process = proc.as_dict(attrs=['pid', 'name', 'cwd', 'exe', 'username', 'nice',
                                                'num_threads', 'cpu_percent', 'cpu_affinity',
                                                'memory_full_info', 'memory_percent'])
                try:
                    process['net_connections'] = proc.connections(kind='all')
                    process['access_denied'] = False
                except:
                    process['access_denied'] = True
                process_list.append(process)
            except:
                continue

        if sort is not None:
            process_list = sorted(process_list, key=sort, reverse=True)

        return process_list

    @subroute('/<show>')
    def post(self, request, show=False):
        action = request.form['action']
        id = request.form['id']

        if action == 'kill':
            prism.command('kill -KILL %s' % id)
        elif action == 'terminate':
            prism.command('kill %s' % id)
        return ('system.SystemProcessView')

class SystemProcessView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/process', title='View Process')

    @subroute('/<int:process_id>')
    def get(self, request, process_id):
        try:
            p = psutil.Process(process_id)
        except:
            return ('system.SystemProcessesView')

        process = p.as_dict(attrs=['pid', 'name', 'cwd', 'exe', 'username', 'nice',
                                   'cpu_percent', 'cpu_affinity', 'memory_full_info',
                                   'memory_percent', 'status', 'cpu_times', 'threads',
                                   'io_counters', 'open_files', 'create_time', 'cmdline',
                                   'connections'])
        process['connections'] = p.connections(kind='all')

        cpu_count = get_cpu_count()
        return ('process.html', {
                                    'panel_pid': prism.settings.PANEL_PID,
                                    'process_id': process_id,
                                    'cpu_count': cpu_count[0],
                                    'cpu_count_logical': cpu_count[1],
                                    'ram': psutil.virtual_memory()[0],
                                    'proc': process
                                })

    @subroute('/<int:process_id>')
    def post(self, request, process_id):
        import json
        try:
            p = psutil.Process(process_id)
        except:
            return {}
        process = p.as_dict(attrs=['cpu_percent', 'memory_percent'])
        return {'cpu': process['cpu_percent'], 'memory': process['memory_percent']}

class SystemDiskManagerView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/disk', title='Disk Manager',
                                menu={'id': 'system.disk', 'icon': 'circle-o'})

    def get(self, request):
        return ('disk.html', {'file_systems': self.get_file_systems()})

    @memorize(30)
    def get_file_systems(self):
        systems = psutil.disk_partitions()

        for i in range(0, len(systems)):
            system = systems[i]

            system_options = {}
            for option in system.opts.split(','):
                option_local = prism.helpers.locale_('system', 'mount.options.' + option)
                if option != option_local:
                    system_options[option] = option_local
                else:
                    system_options[option] = prism.helpers.locale_('system', 'mount.options.unknown')

            systems[i] = {'device': system.device, 'mount_point': system.mountpoint,
                            'fs_type': system.fstype, 'options': system_options,
                            'usage': psutil.disk_usage(system.mountpoint)}

        return systems

class SystemNetworkMonitorView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/network', title='Network Monitor',
                                menu={'id': 'system.network', 'icon': 'exchange'})

    def get(self, request):
        view = View()

        box = BoxElement(title='networks.list.header', icon='exchange', padding=False)
        box.add(TableElement(
                    ['networks.list.id', 'networks.list.total.sent', 'networks.list.total.received'],
                    [(network_id, prism.helpers.convert_bytes(network.bytes_sent), prism.helpers.convert_bytes(network.bytes_recv)) for network_id, network in self.get_networks().items()]
                ))

        view.add(box)

        return view

    @memorize(30)
    def get_networks(self):
        return psutil.net_io_counters(pernic=True)

class SystemHostsView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/hosts', title='Hosts',
                                menu={'id': 'system.hosts', 'icon': 'cubes'})

    def get(self, request):
        view = View()

        box = BoxElement(title='hosts.list.header', icon='cubes', padding=False)
        box.add(TableElement(
                    ['hosts.list.address', 'hosts.list.host', 'hosts.list.aliases'],
                    [(address, host['hostname'], ', '.join(host['aliases'])) for address, host in self.get_hosts().items()]
                ))

        view.add(box)

        return view

    @memorize(5)
    def get_hosts(self):
        hosts = {}
        with open('/etc/hosts') as f:
            for line in f.readlines():
                line = line.replace('\n', ' ').replace('\r', '')
                info = ' '.join(line.split()).split(' ')
                hosts[info[0]] = {'hostname': info[1], 'aliases': info[2:]}
        return hosts

class SystemCronJobsView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/cron', title='Cron Jobs',
                                menu={'id': 'system.cron', 'icon': 'cogs'})

    def get(self, request):
        return ('cron_jobs.html', {'crontabs': CronTabs(), 'locations': self.get_cron_locations()})

    @memorize(320)
    def get_cron_locations(self):
        locs = []
        for thing, loc in crontabs.KNOWN_LOCATIONS:
            if os.path.isfile(loc):
                locs.append(loc)
        return locs

    def post(self, request):
        action = request.form['action']
        if action == 'delete':
            crontab_id = int(request.form['crontab_id'])
            cron_id = int(request.form['cron_id'])

            crontab = CronTabs()[crontab_id - 1]
            job = crontab.crons[cron_id - 1]
            crontab.remove(job)
            crontab.write()
            return ('system.cron_jobs')
        else:
            tabfile = request.form['tabfile']
            obj = parse_cron_widget(request, CronTab(tabfile=tabfile))
            if obj is not None:
                return obj

    @subroute('/edit/<int:crontab_id>/<int:cron_id>')
    def edit_get(self, request, crontab_id, cron_id):
        try:
            return ('cron_job_edit.html', {'cron': CronTabs()[crontab_id - 1].crons[cron_id - 1]})
        except:
            return ('system.SystemCronJobsView')

    @subroute('/edit/<int:crontab_id>/<int:cron_id>')
    def edit_post(self, request, crontab_id, cron_id):
        obj = parse_cron_widget(request, CronTabs()[crontab_id - 1], cron_id)
        if obj is not None:
            return obj
        return ('system.SystemCronJobsView')

@memorize(120)
def get_cpu_count():
    cpu_count = psutil.cpu_count(logical=False)
    return (cpu_count, psutil.cpu_count(logical=True) - cpu_count)

def parse_cron_widget(request, crontab_obj, cron_id=-1):
    editing = cron_id != -1

    minute = request.form['minute']
    if minute is None:
        minute = '*'

    hour = request.form['hour']
    if hour is None:
        hour = '*'

    day = request.form['day']
    if day is None:
        day = '*'

    month = request.form['month']
    if month is None:
        month = '*'

    weekday = request.form['weekday']
    if weekday is None:
        weekday = '*'

    year = request.form['year']
    if year is None:
        year = '*'

    user = request.form['user']
    if user is None:
        user = 'root'

    command = request.form['command']
    if command is not None:
        if not editing:
            job = crontab_obj.new(user=user, command=command)
        else:
            job = crontab_obj.crons[cron_id - 1]
            job.set_command(command)
        job.setall(minute, hour, day, month, weekday, year)
        print(job.render())
        crontab_obj.write()

        if not editing:
            return ('core.restart', {'return_url': 'system.cron_jobs'})
