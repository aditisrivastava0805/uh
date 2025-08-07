import os
import signal


class ProcessCheck:
    def __init__(self, pidfile):
        self.pid = int(os.getpid())
        self.pidfile = pidfile

    @staticmethod
    def killPidRunning(pid):
        """Check For the existence of a unix pid."""
        try:
            # os.kill(pid, signal.SIGKILL)
            PGID = os.getpgid(pid)
            if PGID is not None:
                os.killpg(PGID, signal.SIGKILL)
            else:
                os.kill(pid, signal.SIGKILL)
            print(f"Process Killed PGID: {str(PGID)} and PID: {str(pid)}")
        except OSError:
            return False
        else:
            return True

    def start(self):
        if os.path.isfile(self.pidfile) and self.killPidRunning(int(open(self.pidfile, 'r').readlines()[0])):
            print("%s already exists, killed old process" % self.pidfile)
        open(self.pidfile, 'w').write(str(self.pid))

    def stop(self):
        os.unlink(self.pidfile)







