import os
import pty
import re
import select
import subprocess

import prism

class TerminalCommand(object):
    def __init__(self, command, return_url=None, restart=False):
        self.command = command
        self.return_url = return_url
        self.restart = restart

        self.running = False

        self.terminal_id = prism.generate_random_string(8)
        self.process = None

    def init(self):
        self.running = True

        self.master_fd, self.slave_fd = pty.openpty()
        self.process = subprocess.Popen(self.command,
                                            shell=True,
                                            universal_newlines=True,

                                            stdout=self.slave_fd,
                                            stdin=self.slave_fd,
                                            close_fds=True
                                        )

    def input(self, str):
        self.process.stdin.write(str + '\n')

    def output(self):
        ready, _, _ = select.select([self.master_fd], [], [], .04)
        if ready:
            data = os.read(self.master_fd, 512)
            if not data:
                return 0
            return re.sub('(?:\x1b\[[0-9;]*m|\x1b\(B)', '', data.decode('utf-8').replace('\n', '<br />').rstrip())
        elif self.process.poll() is not None:
            assert not select.select([self.master_fd], [], [], 0)[0]
            os.close(self.slave_fd)
            os.close(self.master_fd)
            return -1
        return 1
