import os
import prism

class PythonVersions:
    instance = None

    def __init__(self):
        # Attempt to find all installed python versions
        results = prism.os_command('find / -path "*bin/python*" | grep "[^gm]$"')[0]
        # Split newlines and remove the last blank entry
        results = results.decode().split('\n')[:-1]

        self.versions = []

        for path in results:
            if path[:4] == '/usr' or path[:4] == '/opt':
                if not os.path.islink(path):
                    self.versions.append(PythonVersion(path))

    def get():
        if PythonVersions.instance is None:
            PythonVersions.instance = PythonVersions()
        return PythonVersions.instance

class PythonVersion:
    def __init__(self, path):
        self.path = path

        path_arr = path.split('/')[1:]
        self.cmd = path_arr[len(path_arr) - 1]

        if path_arr[0] == 'opt' and path_arr[1] != 'prism-panel':
            self.scl = path_arr[2]

            # If it's an scl, attach it and grab the version
            out, result = prism.os_commands((
                        self.bind_cmd(),
                        '%s -V' % self.cmd
                    ))
        else:
            self.scl = False

            # If it's just a version, it's pretty simple to grab the version
            py3, result = prism.os_command('%s -V' % path)
            if py3:
                result = py3

        self.version = result.decode().split('\n')[0]

    def bind_cmd(self):
        if self.scl:
            return 'source %s/%s/enable' % (self.path.split('/%s/' % self.scl)[0], self.scl)
        else:
            return ''

    def __str__(self):
        return ('' if not self.scl else '[SCL] ') + self.version + ': ' + self.cmd + ' (' + self.path + ')'
