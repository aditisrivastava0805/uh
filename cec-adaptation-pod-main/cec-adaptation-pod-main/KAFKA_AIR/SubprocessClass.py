import subprocess

from Logger import LoggingHandler


class SubprocessClass:
    def __init__(self):
        self._logger = LoggingHandler.get_logger(self.__class__.__name__)

    def execute_cmd(self, cmd):
        result = None
        try:
            result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = result.communicate()
            out = out.decode("utf-8")
            err = err.decode("utf-8")
            if out == "":
                return None, err
            return out, None
        except Exception as err:
            self._logger.error("Exception while executing command : " + str(err))
        finally:
            result.terminate()  # send sigterm, or ...
            result.kill()

    def execute_cmd_without_shell(self, cmd):
        try:
            result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = result.communicate()
            out = out.decode("utf-8")
            err = err.decode("utf-8")
            if out == "":
                out = None
            if err == "":
                err = None
            return out, err
        except Exception as err:
            self._logger.error("Exception while executing command : " + str(err))