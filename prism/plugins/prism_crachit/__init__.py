import os
import prism
from prism.helpers import repeat

from prism.api.plugin import BasePlugin


class CrachitPlugin(BasePlugin):
    service_manager = None

    def register_monitor(self, service_name, monitor):
        CrachitPlugin.service_manager.register_monitor(service_name, monitor)

    @repeat(0, 5)
    def process_check():
        if CrachitPlugin.service_manager is None:
            CrachitPlugin.service_manager = ServiceManager()
        CrachitPlugin.service_manager.ping_processes()

class Service:
    def __init__(self, service_name, options=None):
        self.service_name = service_name
        self.options = options

        self.service_file = os.path.join('/usr/lib/systemd/system/', self.service_name + '.service')
        if self.options is not None:
            if not os.path.exists(self.service_file):
                self.save()
        elif os.path.exists(self.service_file):
            self.options = {}
            with open(self.service_file, 'r') as lines:
                group = None
                for line in lines:
                    line = line.rstrip('\n')
                    if len(line) == 0:
                        continue
                    if line[0] == '[':
                        group = line[1:-1]
                    else:
                        key, value = line.split('=', 1)
                        self.options[key] = value

    def register_monitor(self, monitor):
        CrachitPlugin.service_manager.register_monitor(self.service_name, monitor)

    def save(self):
        existed = os.path.exists(self.service_file)

        file = open(self.service_file, 'w')
        for category, options in self.options.items():
            file.write('[%s]\n' % category)
            for option, value in options.items():
                file.write('%s=%s\n' % (option, value))
            file.write('\n')
        file.close()

        # If the service already existed, make systemctl update
        prism.os_command('systemctl daemon-reload')

    def delete(self):
        if os.path.exists(self.service_file):
            os.remove(self.service_file)

    def enable(self):
        return prism.os_command('systemctl enable %s' % self.service_name)

    def disable(self):
        return prism.os_command('systemctl disable %s' % self.service_name)

    def start(self):
        return prism.os_command('systemctl start %s' % self.service_name)

    def restart(self):
        return prism.os_command('systemctl restart %s' % self.service_name)

    def stop(self):
        return prism.os_command('systemctl stop %s' % self.service_name)

    @property
    def status(self):
        if self.service_name in CrachitPlugin.service_manager.processes:
            return 'online'
        return 'offline'

    @property
    def enabled(self):
        return self.service_name in CrachitPlugin.service_manager.enabled

class ServiceManager:
    def __init__(self):
        self.processes = None
        self.enabled = None
        self.monitors = {}

        self.ping_processes()

    def register_monitor(self, service_name, monitor):
        if service_name not in self.monitors:
            self.monitors[service_name] = []
        self.monitors[service_name].append(monitor)

    def ping_processes(self):
        enabled_processes = []
        result, err = prism.os_command('systemctl list-unit-files --type=service | grep enabled')
        for proc in result.decode().split('\n')[:-1]:
            enabled_processes.append('.'.join(proc.split()[0].split('.')[:-1]))
        self.enabled = enabled_processes

        pinged_processes = []

        result, err = prism.os_command('systemctl | grep .service | grep running')
        for proc in result.decode().split('\n')[:-1]:
            proc = proc.split()
            i = 1 if proc[0] == '●' else 0
            pinged_processes.append('.'.join(proc[i].split('.')[:-1]))

        if not self.processes:
            self.processes = pinged_processes
            return

        new_processes = [x for x in pinged_processes if x not in self.processes]
        dead_processes = [x for x in self.processes if x not in pinged_processes]

        for process in new_processes:
            if process in self.monitors:
                for monitor in self.monitors[process]:
                    monitor.on_start()

        for process in dead_processes:
            if process in self.monitors:
                for monitor in self.monitors[process]:
                    monitor.on_dead()

        self.processes = pinged_processes

class ServiceMonitor:
    def on_start(self):
        pass

    def on_dead(self):
        pass
