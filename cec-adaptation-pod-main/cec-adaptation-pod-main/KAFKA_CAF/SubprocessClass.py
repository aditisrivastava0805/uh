import logging
import subprocess
import time

class SubprocessClass:
    @staticmethod
    def execute_cmd(cmd):
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
            logging.error(f"Exception while executing command : {str(err)}")
        finally:
            result.terminate()  # send sigterm, or ...
            result.kill()

    @staticmethod
    def get_output(cmd):
        try:
            result = subprocess.check_output(cmd, shell=True)
            return result.decode("utf-8")
        except Exception as err:
            logging.exception(f"Exception in get_output() ::: {str(err)}")

    @staticmethod
    def get_output_with_child_run(cmd, childCmd):
        out = None
        childCmd = childCmd + "\n"
        childCmd = bytes(childCmd, encoding="utf-8")

        try:
            result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      stdin=subprocess.PIPE)
            time.sleep(3)
            result.stdin.write(b'peerlist\n')
            time.sleep(2)
            out, err = result.communicate()
            out = out.decode("utf-8")
            err = err.decode("utf-8")
            if out == "":
                out = None
            if err == "":
                err = None
            return out, err
        except Exception as err:
            logging.error("Exception while executing command get_output_with_child_run() : " + str(err))
            return out, str(err)
