import os
import subprocess


def execute_cmd(cmd):
    result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = result.communicate()
    out = out.decode("utf-8")
    err = err.decode("utf-8")
    if out == "":
        out = None
    if err == "":
        err = None
    return out, err


def get_application_namespace():
    cmd = """cat /home/ericuser/.env | grep "APPLICATION_NAMESPACE"  | awk -F'=' '{print $2}' """
    out, err = execute_cmd(cmd)
    if err:
        return "No Namespace Found in File /home/ericuser/.env"
    return str(out).strip()
    # return os.environ.get("APPLICATION_NAMESPACE")


def get_adaptation_namespace():
    cmd = """cat /home/ericuser/.env | grep "ADAPTATION_NAMESPACE"  | awk -F'=' '{print $2}' """
    out, err = execute_cmd(cmd)
    if err:
        return "No Namespace Found in File /home/ericuser/.env"
    return str(out).strip()
    # return os.environ.get("ADAPTATION_NAMESPACE")


if __name__ == '__main__':
    print(get_application_namespace())
    print(get_adaptation_namespace())
