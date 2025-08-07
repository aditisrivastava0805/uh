import subprocess
import os
import signal
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

    def kill_proc(self, process_id):
        try:
            os.killpg(os.getpgid(process_id), signal.SIGTERM)
        except Exception as err:
            self._logger.error(f"Exception while kill_proc : {str(err)}")

    def execute_cmd_without_shell(self, cmd):
        try:
            result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = result.communicate()
            out = out.decode("utf-8")
            err = err.decode("utf-8")
            if out == "":
                return None, err
            return out, None
        except Exception as err:
            self._logger.error("Exception while executing command : " + str(err))

    def execute_with_blocking_method(self, cmd):
        try:
            subprocess.run(cmd, check=True, shell=True)
            return True
        except FileNotFoundError as exc:
            self._logger.error(f"Process failed because the executable could not be found.\n{exc}")
            return False
        except subprocess.CalledProcessError as exc:
            self._logger.info(f"Process failed because did not return a successful return code. Returned {exc.returncode}\n{exc}")
            return False
        except subprocess.TimeoutExpired as exc:
            self._logger.info(f"Process timed out.\n{exc}")
            return False
        except Exception as exc:
            self._logger.error("Exception while executing command : " + str(exc))
            return False

