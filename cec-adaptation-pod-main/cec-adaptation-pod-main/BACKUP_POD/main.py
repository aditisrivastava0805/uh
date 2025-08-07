import os, sys
import json
import logging
from datetime import datetime, date
from typing import List, Dict
from SftpClass import SftpClass
import zipfile
import glob
import subprocess

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.process_check.ProcessCheck import ProcessCheck
from lib.Namespace import get_application_namespace, get_adaptation_namespace


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def execute_cmd(cmd):
    result = None
    try:
        result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = result.communicate()
        out = out.decode("utf-8")
        err = err.decode("utf-8")
        if out:
            return out, None
        return None, err
    except Exception as err:
        logging.error(f"Exception while executing command : {str(err)}")
    finally:
        result.terminate()  # send sigterm, or ...
        result.kill()


def load_config(config_file_path: str):
    logging.info(f"Loading config file {config_file_path}")

    with open(config_file_path, 'r') as f:
        j = json.load(f)

    backup_path = j["backup_path"]
    backup_filename = j["backup_filename"]
    script_path = j["script_path"]
    skip_directories = j["skip_directories"]
    backup_server_sftp_config = j["backup_server_sftp_config"]

    return backup_path, backup_filename, script_path, backup_server_sftp_config, skip_directories


def eval_value(raw_value: str) -> str:
    CMD_KEY = 'cmd:'

    if raw_value.startswith(CMD_KEY):
        command = raw_value.split(CMD_KEY)[-1]
        value, err = execute_cmd(command)

        if err:
            raise OSError(err)

        value = str(value).splitlines()

        if len(value) > 1:
            return str(value[-1]).strip()
        return str(value[0]).strip()
    else:
        return raw_value


def make_dir(path: str):
    if not os.path.isdir(path):
        # Creating the folder if not there
        os.makedirs(path, exist_ok=True)


def fetch_hostname():
    cmd = """hostname"""
    hostname, error = execute_cmd(cmd)
    if error:
        logging.error(f"Failed fetching hostname, cmd: {cmd}")
        return "undefined-hostname"

    hostname = hostname.strip().upper()
    logging.info(f'Hostname: {hostname}')
    if error:
        raise Exception(f'Hostname could not be determined, error: {error}')
    return hostname


def fetch_application_server_name():
    cmd = "kubectl get nodes --no-headers | awk -F '-' 'FNR==1{print $3}' "
    app_name, error = execute_cmd(cmd)

    if error:
        raise Exception(str(error))

    app_name = str(app_name).strip() if app_name else ""

    return app_name


def fetch_sftp_info_from_config_data(config_data, app_name: str):
    for app in config_data.keys():
        app_list = str(app).split("|")
        if app_list[0] in app_name or app_list[1] in app_name:
            bck_ip = config_data[app]["backup_server_ip"]
            bck_user = config_data[app]["backup_server_user"]
            bck_pass = config_data[app]["backup_server_password"]

            return bck_ip, bck_user, bck_pass
    raise Exception("NO BACKUP SERVER CONFIGURATION FOUND!")


def get_adaptation_pod_name(namespace: str):
    cmd = f"kubectl get pod -n {namespace} | grep adap | awk -F' ' '{{print $1}}'"
    pod, error = execute_cmd(cmd)
    pod = str(pod).strip() if pod else ""

    if error:
        logging.error(f'Failed fetching adaptation pod name, cmd: {cmd}')
        return ""
    return pod


def get_cron_configmap_name(namespace: str, pod_name: str):
    cmd = f"kubectl describe pod {pod_name} -n {namespace} | grep cm-cron | awk -F' ' '{{print $2}}'"
    pod, error = execute_cmd(cmd)
    pod = str(pod).strip() if pod else ""

    if error:
        logging.error(f'Failed fetching Cron-Config-Map pod name, cmd: {cmd}')
        return ""
    return pod


def backup_cron():
    pass


def backup_scripts(scripts_path: str, zip_file: str, archive_dir: str, skip_directories):
    try:
        if not str(scripts_path).endswith("/"):
            scripts_path = scripts_path + "/"

        if not str(archive_dir).endswith("/"):
            archive_dir = archive_dir + "/"

        archive_dir = archive_dir + zip_file
        # print(f"script_dir : {str(archive_dir)}")
        # print(f"scripts_path : {str(scripts_path)}")
        with zipfile.ZipFile(archive_dir, 'w') as f:
            for file in glob.glob(scripts_path + "**/*", recursive=True):
                # print(file)
                if any(word in file for word in skip_directories):
                    continue

                f.write(file)

        return archive_dir
    except Exception as err:
        logging.error(f"Exception in backup_scripts ::: {str(err)}")


def main(script_dir: str, backup_path: str, backup_filename: str, scripts_path: str,
         backup_server_ip: str, backup_server_user: str, backup_server_password: str, archive_dir: str,
         skip_directories):
    # Backup all scripts
    zip_file_path = backup_scripts(scripts_path, backup_filename, archive_dir, skip_directories)

    # Uploading zip file to server
    sftp_class_obj = SftpClass(backup_server_user, backup_server_password, backup_server_ip)
    sftp_con = sftp_class_obj.connection()
    if not str(backup_path).endswith("/"):
        backup_path = backup_path + "/"
    backup_path = backup_path + backup_filename
    sftp_class_obj.upload_files(sftp_con, zip_file_path, backup_path)
    sftp_con.close()

    logging.info("ALL PROCESSES ARE DONE")


if __name__ == '__main__':
    try:
        pc = ProcessCheck(
            os.path.join("/", "tmp", os.path.basename(os.path.dirname(os.path.abspath(__file__))) + ".pid"))
        pc.start()
        # starting main method
        # Taking the current directory path
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        # Creating the logger object and getting the logger
        LOG_DIR = os.path.join(SCRIPT_DIR, "log")
        make_dir(LOG_DIR)

        ARCHIVE_DIR = os.path.join(SCRIPT_DIR, "archive")
        make_dir(ARCHIVE_DIR)

        APPLICATION_SERVER_NAME = fetch_application_server_name()

        CONFIG_FILE_PATH = os.path.join(SCRIPT_DIR, 'config/config.json')
        BACKUP_PATH, BACKUP_FILENAME, SCRIPT_PATH, BACKUP_SERVER_CONFIG, SKIP_DIRECTORIES = load_config(
            CONFIG_FILE_PATH)

        APP_NAMESPACE = get_application_namespace()
        ADA_NAMESPACE = get_adaptation_namespace()

        BACKUP_SERVER_IP, BACKUP_SERVER_USER, BACKUP_SERVER_PASSWORD = fetch_sftp_info_from_config_data(
            BACKUP_SERVER_CONFIG, APPLICATION_SERVER_NAME)

        BACKUP_FILENAME = BACKUP_FILENAME + "_" + str(ADA_NAMESPACE) + ".zip"
        main(SCRIPT_DIR, BACKUP_PATH, BACKUP_FILENAME, SCRIPT_PATH, BACKUP_SERVER_IP, BACKUP_SERVER_USER,
             BACKUP_SERVER_PASSWORD, ARCHIVE_DIR, SKIP_DIRECTORIES)
        pc.stop()
    except Exception as ex:
        logging.error(f"Failed execution {str(ex)}")
