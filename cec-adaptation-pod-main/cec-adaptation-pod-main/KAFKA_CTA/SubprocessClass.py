import logging
import subprocess
from typing import Tuple, Optional


class SubprocessClass:

    def execute_cmd(self, cmd, is_shell: bool = True) -> Tuple[Optional[str], Optional[str]]:
        out = None

        try:
            result = subprocess.Popen(cmd, shell=is_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = result.communicate()
            out = out.decode("utf-8")
            err = err.decode("utf-8")
            if out == "":
                out = None
            if err == "":
                err = None
            return out, err
        except Exception as err:
            logging.error(f"Exception while executing command : {str(err)}")
            return out, str(err)

    def execute_cmd_without_shell(self, cmd):
        return self.execute_cmd(cmd, is_shell=False)

    @staticmethod
    def get_output(cmd):
        try:
            result = subprocess.check_output(cmd, shell=True)
            return result.decode("utf-8")
        except Exception as err:
            logging.exception(f"Exception in get_output() : {str(err)}")

    @staticmethod
    def get_output_with_run(cmd):
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
                                    executable='/bin/bash')
            return result.stdout.decode("utf-8"), result.stderr.decode("utf-8")
        except Exception as err:
            logging.exception(f"Exception in get_output() : {str(err)}")
