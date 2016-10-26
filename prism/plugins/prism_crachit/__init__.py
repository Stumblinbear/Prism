import psutil
import prism
from prism.helpers import repeat

from prism.api.plugin import BasePlugin


class CrachitPlugin(BasePlugin):
    service_manager = None

    def __init__(self):
        BasePlugin.__init__(self)

    def register_monitor(self, service_name, monitor):
        CrachitPlugin.service_manager.register_monitor(service_name, monitor)

    @repeat(0, 5)
    def process_check():
        if CrachitPlugin.service_manager is None:
            CrachitPlugin.service_manager = ServiceManager()
        CrachitPlugin.service_manager.ping_processes()

class Service:
    def __init__(self, service_name, options):
        self.name = service_name
        self.options = options

        self.service_file = os.path.join('/usr/lib/systemd/system/', self.service_name + '.service')
        if not os.path.exists(self.service_file):
            self.save()

    def register_monitor(self, monitor):
        CrachitPlugin.service_manager.register_monitor(self.service_name, monitor)

    def save(self):
        file = open(self.service_file, 'w')
        for category in options:
            file.write('[%s]' % category)
            for option, value in options:
                file.write('%s=%s' % (option, value))
            file.write('\n')
        file.close()

    def delete(self):
        os.remove(self.service_file)

class ServiceManager:
    def __init__(self):
        self.processes = {}
        for proc in psutil.process_iter():
            self.processes[proc.name()] = proc

        self.monitors = {}

    def register_monitor(self, service_name, monitor):
        if service_name not in self.monitors:
            self.monitors[service_name] = []
        self.monitors[service_name].append(monitor)

    def ping_processes(self):
        pinged_processes = {}

        for proc in psutil.process_iter():
            pinged_processes[proc.name()] = proc

        new_processes = [x for x in pinged_processes.keys() if x not in self.processes.keys()]
        dead_processes = [x for x in self.processes.keys() if x not in pinged_processes.keys()]

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
