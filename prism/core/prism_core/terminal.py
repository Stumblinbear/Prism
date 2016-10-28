import os
import re
import pty
import select
import subprocess

import prism

class Terminal:
    def __init__(self, command=None, return_url=None, restart=False):
        self.command = command
        self.terminal_id = prism.generate_random_string(8)
        self.return_url = return_url
        self.restart = restart
        self.process = TerminalProcess(*pty.openpty())

        prism.info('Terminal Opened: %s' % self.terminal_id)

    def write(self, data):
        self.process.write(data + '\n')

    def read(self, timeout=1):
        self.process.poke(timeout)
        return self.process.read()

    def kill(self):
        self.process.kill()

    @property
    def alive(self):
        return self.process is not None and self.process.alive

class TerminalProcess:
    def __init__(self, master, slave):
        self.master = master
        self.slave = slave

        self.alive = True

        self.process = None
        self.output = []

    def kill(self, data):
        os.close(self.slave)
        os.close(self.master)

    def write(self, data):
        if self.process is None:
            self.process = subprocess.Popen(data,
                                        shell=True,
                                        stdout=self.slave,
                                        stdin=self.slave,
                                        close_fds=True)
        else:
            self.process.stdin.write(data)

    def read(self):
        out = list(self.output)
        self.output.clear()
        return out

    def poke(self, timeout):
        has_data, _, _ = select.select([self.master], [], [], timeout)

        if has_data:
            try:
                data = os.read(self.master, 512)
                if data:
                    data = re.sub('(?:\x1b\[[0-9;]*m|\x1b\(B)', '', data.decode('UTF-8'))
                    self.output.append(data)
                    return None
            except UnicodeDecodeError:
                return None
            except IOError:
                pass

        self._verify()

    def _verify(self):
        if self.process is None:
            return

        try:
            pid, status = os.waitpid(self.process.pid, os.WNOHANG)
            if pid:
                self._dead(code=status)
        except OSError:
            self._dead(code=-1)

    def _dead(self, code=0):
        if not self.alive:
            return
        self.alive = False

        if code:
            self.output.append('\n\n\nXT> Process quit: %i' % code)
        else:
            self.output.append('\n\n\nXT> Process completed successfully')
