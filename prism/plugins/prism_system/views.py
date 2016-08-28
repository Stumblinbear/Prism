import os

import crontab
import crontabs
from crontab import CronTab
from crontabs import CronTabs
import psutil

import settings
from memorize import memorize
from api.view import BaseView, route, menu


class SystemView(BaseView):
    @menu('General Information', icon='square', order=0)
    def info(self):
        return ('general_info.html')

    @menu('Users', icon='users')
    def users(self):
        return ('users.html', { 'user_info': get_user_info() })

    @menu('Processes', icon='cog')
    @route('/processes')
    @route('/processes/<show>')
    def processes(self, show=False):
        if show == 'all':
            show = True

        cpu_count = get_cpu_count()
        return ('processes.html', {
                                    'panel_pid': settings.PANEL_PID,
                                    'cpu_count': cpu_count[0],
                                    'cpu_count_logical': cpu_count[1],
                                    'ram': psutil.virtual_memory()[0],
                                    'processes': get_processes(show, lambda x: x['memory_percent'] + x['cpu_percent'])
                                })

    @route('/processes')
    @route('/processes/<show>')
    def post(self, request, show=False):
        action = request.form['action']
        id = request.form['id']

        if action == 'kill':
            prism.command('kill -KILL %s' % id)
        elif action == 'terminate':
            prism.command('kill %s' % id)
        return ('system.processes')

    @route('/process/<int:process_id>')
    def process(self, process_id):
        try:
            p = psutil.Process(process_id)
        except:
            return ('system.processes')

        process = p.as_dict(attrs=[ 'pid', 'name', 'cwd', 'exe', 'username', 'nice',
                                   'cpu_percent', 'cpu_affinity', 'memory_full_info',
                                   'memory_percent', 'status', 'cpu_times', 'threads',
                                   'io_counters', 'open_files', 'create_time', 'cmdline',
                                   'connections' ])
        process['connections'] = p.connections(kind='all')

        cpu_count = get_cpu_count()
        return ('process.html', {
                                    'panel_pid': settings.PANEL_PID,
                                    'process_id': process_id,
                                    'cpu_count': cpu_count[0],
                                    'cpu_count_logical': cpu_count[1],
                                    'ram': psutil.virtual_memory()[0],
                                    'proc': process
                                })

    @route('/process/<int:process_id>')
    def post(self, request, process_id):
        import json
        try:
            p = psutil.Process(process_id)
        except:
            return { }
        process = p.as_dict(attrs=[ 'cpu_percent', 'memory_percent' ])
        return { 'cpu': process['cpu_percent'], 'memory': process['memory_percent'] }

    @menu('Disk Manager', icon='circle-o')
    def disk(self):
    	return ('disk.html', { 'file_systems': get_file_systems() })

    @menu('Network Monitor', icon='exchange')
    def network(self):
    	return ('network.html', { 'networks': get_networks() })

    @menu('Hosts', icon='cubes')
    def hosts(self):
    	return ('hosts.html', { 'hosts': get_hosts() })

    @menu('Cron Jobs', icon='cogs', order=3)
    def cron_jobs(self):
        return ('cron_jobs.html', { 'crontabs': CronTabs(), 'crontab_locations': get_cron_locations() })

    @route('/cron_jobs')
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
            obj = parse_cron_widget(CronTab(tabfile=tabfile))
            if obj != None:
                return obj

    @route('/cron_jobs/edit/<int:crontab_id>/<int:cron_id>')
    def cron_job_edit(self, crontab_id, cron_id):
    	try:
    		return ('cron_job_edit.html', { 'cron': CronTabs()[crontab_id - 1].crons[cron_id - 1] })
    	except:
    		return ('system.cron_jobs')

    @route('/cron_jobs/edit/<int:crontab_id>/<int:cron_id>')
    def post(self, request, crontab_id, cron_id):
        obj = parse_cron_widget(CronTabs()[crontab_id - 1], cron_id)
        if obj != None:
            return obj
        return ('system.cron_jobs')

@memorize(320)
def get_cron_locations():
	locs = []
	for thing,loc in crontabs.KNOWN_LOCATIONS:
		if os.path.isfile(loc):
			locs.append(loc)
	return locs

@memorize(60)
def get_user_info():
	user_info = { 'groups': {}, 'users': {} }
	with open("/etc/group", "r") as f:
		for line in f.readlines():
			info = line.replace('\n', ' ').replace('\r', '').split(':')
			user_info['groups'][info[2]] = { 'name': info[0], 'passwd': info[1], 'users': info[3] }
	with open("/etc/passwd", "r") as f:
		for line in f.readlines():
			info = line.replace('\n', ' ').replace('\r', '').split(':')
			user_info['users'][info[2]] = { 'name': info[0], 'passwd': info[1], 'group_id': info[3], 'info': info[4], 'home': info[5], 'shell': info[6] }
	return user_info

@memorize(120)
def get_cpu_count():
	cpu_count = psutil.cpu_count(logical=False)
	return (cpu_count, psutil.cpu_count(logical=True) - cpu_count)

@memorize(30)
def get_processes(show=False, sort=None):
	process_list = []
	for proc in psutil.process_iter():
		if not show and ('rcuob/' in proc.name() or 'rcuos/' in proc.name() or 'scsi_' in proc.name() or 'xfs-' in proc.name() or 'xfs_' in proc.name() or 'kworker/' in proc.name()):
			continue
		try:
			process = proc.as_dict(attrs=[ 'pid', 'name', 'cwd', 'exe', 'username', 'nice', 'num_threads', 'cpu_percent', 'cpu_affinity', 'memory_full_info', 'memory_percent' ])
			#process['net_connections'] = proc.connections(kind='all')
			process_list.append(process)
		except:
			continue

	if sort != None:
		process_list = sorted(process_list, key=sort, reverse=True)

	return process_list

_mount_options = {}
_mount_options['async'] = 'Allows the asynchronous input/output operations on the file system.'
_mount_options['auto'] = 'Allows the file system to be mounted automatically using the mount -a command. '
_mount_options['defaults'] = 'Provides an alias for async, auto, dev, exec, nouser, rw, and suid.'
_mount_options['exec'] = 'Allows the execution of binary files on the particular file system.'
_mount_options['loop'] = 'Mounts an image as a loop device.'
_mount_options['noauto'] = 'Default behavior disallows the automatic mount of the file system using the mount -a command.'
_mount_options['noexec'] = 'Disallows the execution of binary files on the particular file system.'
_mount_options['nouser'] = 'Disallows an ordinary user (that is, other than root) to mount and unmount the file system.'
_mount_options['remount'] = 'Remounts the file system in case it is already mounted.'
_mount_options['ro'] = 'Mounts the file system for reading only.'
_mount_options['rw'] = 'Mounts the file system for both reading and writing.'
_mount_options['user'] = 'Allows an ordinary user (that is, other than root) to mount and unmount the file system.'

_mount_options['relatime'] = 'The access time (atime) will not be written to the disc during every access.'
_mount_options['seclabel'] = 'An indicator added by the selinux code, that the filesystem is using xattrs for labels and that it supports label changes by setting the xattrs.'

_mount_options['attr2'] = 'Enables an "opportunistic" improvement to be made in the way inline extended attributes are stored on-disk.'
_mount_options['noattr2'] = 'Disables an "opportunistic" improvement to be made in the way inline extended attributes are stored on-disk.'
_mount_options['barrier'] = 'Enables the use of block layer write barriers for writes into the journal and for data integrity operations.'
_mount_options['nobarrier'] = 'Disables the use of block layer write barriers for writes into the journal and for data integrity operations.'
_mount_options['discard'] = 'Enables the issuing of commands to let the block device reclaim space freed by the filesystem.'
_mount_options['nodiscard'] = 'Disables the issuing of commands to let the block device reclaim space freed by the filesystem.'
_mount_options['filestreams'] = 'Make the data allocator use the filestreams allocation mode across the entire filesystem rather than just on directories configured to use it.'
_mount_options['ikeep'] = 'Does not delete empty inode clusters and keeps them around on disk.'
_mount_options['noikeep'] = 'Empty inode clusters are returned to the free space pool.'
_mount_options['inode32'] = 'Limits inode creation to locations which will not result in inode numbers with more than 32 bits of significance.'
_mount_options['inode64'] = 'Inodes will be placed in the location where their data is, minimizing disk seeks and fixing problems with large disks.'
_mount_options['largeio'] = 'Will return the "swidth" value (in bytes) in st_blksize. If the filesystem does not have a "swidth" specified but does specify an "allocsize" then "allocsize" (in bytes) will be returned instead. Otherwise the behaviour is the same as if "nolargeio" was specified.'
_mount_options['nolargeio'] = 'The optimal I/O reported in st_blksize by stat(2) will be as small as possible to allow user applications to avoid inefficient read/modify/write I/O.'
_mount_options['noalign'] = 'Data allocations will not be aligned at stripe unit boundaries.'
_mount_options['norecovery'] = 'Will be mounted without running log recovery.'
_mount_options['nouuid'] = 'Don\'t check for double mounted file systems using the file system uuid.'
_mount_options['noquota'] = 'Forcibly turns off all quota accounting and enforcement within the filesystem.'
_mount_options['uquota'] = 'User disk quota accounting enabled, and limits (optionally) enforced.'
_mount_options['usrquota'] = 'User disk quota accounting enabled, and limits (optionally) enforced.'
_mount_options['uqnoenforce'] = 'User disk quota accounting enabled, and limits (optionally) enforced.'
_mount_options['quota'] = 'User disk quota accounting enabled, and limits (optionally) enforced.'
_mount_options['gquota'] = 'Group disk quota accounting enabled and limits (optionally) enforced.'
_mount_options['grpquota'] = 'Group disk quota accounting enabled and limits (optionally) enforced.'
_mount_options['gqnoenforce'] = 'Group disk quota accounting enabled and limits (optionally) enforced.'
_mount_options['pquota'] = 'Project disk quota accounting enabled and limits (optionally) enforced.'
_mount_options['prjquota'] = 'Project disk quota accounting enabled and limits (optionally) enforced.'
_mount_options['pqnoenforce'] = 'Project disk quota accounting enabled and limits (optionally) enforced.'
_mount_options['swalloc'] = 'Data allocations will be rounded up to stripe width boundaries when the current end of file is being extended and the file size is larger than the stripe width size.'
_mount_options['wsync'] = 'When specified, all filesystem namespace operations are executed synchronously.'

@memorize(30)
def get_file_systems():
	systems = psutil.disk_partitions()

	for i in range(0, len(systems)):
		system = systems[i]

		system_options = {}
		for option in system.opts.split(','):
			if option in _mount_options:
				system_options[option] = _mount_options[option]
			else:
				system_options[option] = 'No known information on this option.'

		systems[i] = { 'device': system.device, 'mount_point': system.mountpoint, 'fs_type': system.fstype, 'options': system_options, 'usage': psutil.disk_usage(system.mountpoint) }

	return systems

@memorize(30)
def get_networks():
	return psutil.net_io_counters(pernic=True)

@memorize(5)
def get_hosts():
	hosts = {}
	with open('/etc/hosts') as f:
		for line in f.readlines():
			line = line.replace('\n', ' ').replace('\r', '')
			info = ' '.join(line.split()).split(' ')
			hosts[info[0]] = { 'hostname': info[1], 'aliases': info[2:] }
	return hosts

def parse_cron_widget(request, crontab_obj, cron_id=-1):
	editing = cron_id != -1

	minute = request.form['minute']
	if minute == None:
		minute = '*'

	hour = request.form['hour']
	if hour == None:
		hour = '*'

	day = request.form['day']
	if day == None:
		day = '*'

	month = request.form['month']
	if month == None:
		month = '*'

	weekday = request.form['weekday']
	if weekday == None:
		weekday = '*'

	year = request.form['year']
	if year == None:
		year = '*'

	user = request.form['user']
	if user == None:
		user = 'root'

	command = request.form['command']
	if command != None:
		if not editing:
			job = crontab_obj.new(user=user, command=command)
		else:
			job = crontab_obj.crons[cron_id - 1]
			job.set_command(command)
		job.setall(minute, hour, day, month, weekday, year)
		print(job.render())
		crontab_obj.write()

		if not editing:
			return ('core.restart', { 'return_url': 'system.cron_jobs' })
