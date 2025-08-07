import os, sys
import json
from datetime import datetime
from typing import List
import concurrent.futures
import argparse
import time
from Logger import LoggingHandler
import AIR_STAT
from SubprocessClass import SubprocessClass

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.process_check.ProcessCheck import ProcessCheck
from lib.Namespace import get_application_namespace, get_adaptation_namespace


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def parse_args():
    parser = argparse.ArgumentParser(description="STAT - Kafka")
    parser.add_argument("--wait", action='store_true', default=False,
                        help="Start processing after configured time lapse")
    args = parser.parse_args()

    return args.wait


def load_config(config_file_path: str):
    logger.info(f"Loading config file {config_file_path}")

    with open(config_file_path, 'r') as f:
        j = json.load(f)

    wait_to_start_secs = j["wait_to_start_secs"]
    pod = j["pod"]
    file_newer_than_min = j["file_newer_than_min"]
    max_processes = j["max_processes"]
    whitelist_pod_enable = j["whitelist_pod_enable"]
    whitelist_pods = j["whitelist_pods"]
    splunk_user_group = j["splunk"]["splunk_user_group"]
    splunk_container = j["splunk"]["splunk_container"]
    sftp_user = j["sftp"]["user"]
    sftp_password = j["sftp"]["password"]
    dir_lookup = j["dir_lookup"]
    blacklist_pods = j["blacklist_pods"]

    return pod, whitelist_pod_enable, whitelist_pods, splunk_user_group, splunk_container, sftp_user, sftp_password, dir_lookup, file_newer_than_min, max_processes, wait_to_start_secs, blacklist_pods


def eval_value(raw_value: str) -> str:
    CMD_KEY = 'cmd:'

    if raw_value.startswith(CMD_KEY):
        command = raw_value.split(CMD_KEY)[-1]
        value, err = subprocess_obj.execute_cmd(command)

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


def get_splunk_ip(ns: str):
    try:
        cmd = f"""kubectl get all -n {ns} | grep splunkfwd | awk 'FNR == 2 {{print $4}}' """
        out, error = subprocess_obj.execute_cmd(cmd)
        logger.info(f"Splunk Forwarder IP Command Output ::: {str(out)} and Error : {str(error)}")
        if out is not None:
            out = str(out).strip()
            return out
        logger.error(f"No Splunk Forwarder IP Available Error ::: {str(error)}")
        sys.exit(-1)
    except Exception as err:
        logger.error("Exception in update_command ::: " + str(err))


def get_splunk(ns: str):
    """
    Getting Splunk Forwarder name and creating a list.

    :return: List of Splunk Forwarder pods.
    """
    try:
        # Get Splunk Pod- Name
        splunk_name_list = []
        cmd = f"""kubectl get pods -n {ns} | grep splunk | awk -F' ' '{{print $1}}' """
        out, error = subprocess_obj.execute_cmd(cmd)
        if out is not None:
            out = out.splitlines()
        else:
            logger.info("No Splunk Forwarder Available")
            sys.exit(-1)
        for splunk in out:
            if splunk:
                splunk_name_list.append(str(splunk).strip())
        logger.info(f"splunk_list : {splunk_name_list}")
        return splunk_name_list
    except Exception as err:
        logger.error("Exception in get_splunk ::: " + str(err))


def get_uid_gid_from_splunk(splunk_list: List[str], splunk_container: str, splunk_user_group: str, ns: str):
    """
    Getting User ID and Group ID of the Splunk Forwarder directory.

    :return: UserID and GroupID of the Splunk Forwarder Directory.
    """
    try:
        # Get the UID and GID for the user
        if splunk_list:
            cmd = f"""kubectl exec -it {splunk_list[0]} -n {ns} -c {splunk_container} -- getent passwd {splunk_user_group} | awk -F':' '{{print $3 "," $4}}'"""
            logger.info(f"{cmd}")
            out, error = subprocess_obj.execute_cmd(cmd)
            logger.info(f"{out}")
            out = str(out).split(",")
            uid = out[0]
            gid = str(out[1]).strip()
            return int(uid), int(gid)
        logger.error(f"No Splunk....Can't get UID and GID, Splunk-List : {str(splunk_list)}")
        return "", ""
    except Exception as err:
        logger.error("Exception in get_uid_gid_from_splunk ::: " + str(err))
        return 0, 0


def available_pods(namespace: str, pod: str, whitelist_enabled: str, whitelist_pod_list: list, blacklistPodList) -> \
List[str]:
    try:
        pods_list = []
        cmd = f'kubectl get pods -n {namespace} | grep c{pod} | grep -v gui | grep -v upgrade'
        pods, error = subprocess_obj.execute_cmd(cmd)

        if error:
            logger.error(f'Failed fetching pods, cmd: {cmd}')
            return []

        if not pods:
            logger.error(f'No pods are found, namespace: {namespace}, pod pattern: {pod}')
            return []

        for pod in pods.splitlines():
            pod_name, running_number, running_status, restart, up_time = pod.split(maxsplit=4)
            if running_status == "Running" and running_number == "1/1":
                if str(pod_name).strip() in blacklistPodList:
                    continue

                if whitelist_enabled == "true" or whitelist_enabled == "True":
                    if str(pod_name).strip() in whitelist_pod_list:
                        pods_list.append(str(pod_name).strip())
                else:
                    pods_list.append(str(pod_name).strip())
        logger.info(f'Available pods: {pods_list}')
        return pods_list
    except Exception as err:
        logger.exception(f"Failed fetching pods : {str(err)}")


def execute(namespace, pod_name: str, script_dir, sftp_user, sftp_password, splunk_ip, file_newer_than_min, output_dir,
            dir_lookup, uid, gid):
    print("In execute() ......")
    sdp_stat_obj = AIR_STAT.AIR_STAT(namespace, script_dir, sftp_user, sftp_password, splunk_ip, file_newer_than_min, output_dir,
                                     dir_lookup, uid, gid)
    sdp_stat_obj.main(pod_name)


def main(namespace: str, main_pod: str, script_dir: str, output_dir: str, archive_dir: str, log_dir: str,
         whitelist_enabled: str, whitelist_pod_list: list, sftp_user: str, sftp_password: str, dir_lookup,
         file_newer_than_min, splunk_ip, uid, gid, max_processes: int, blacklistPodList):
    # Running all air kpi's

    with concurrent.futures.ProcessPoolExecutor(max_processes) as exe:
        for pod in available_pods(namespace, main_pod, whitelist_enabled, whitelist_pod_list, blacklistPodList):
            exe.submit(execute, namespace, pod, script_dir, sftp_user, sftp_password, splunk_ip, file_newer_than_min, output_dir,
                       dir_lookup, uid, gid)
        # exe.map(sdp_stat_obj.main, POD_LIST)
    logger.info("ALL PROCESSES ARE DONE")


def wait_to_start(wait_to_start_secs: int):
    logger.info(f"Waiting {wait_to_start_secs} seconds ... to allow pm data files to arrive")
    time.sleep(wait_to_start_secs)


if __name__ == '__main__':
    try:
        pc = ProcessCheck(
            os.path.join("/", "tmp", os.path.basename(os.path.dirname(os.path.abspath(__file__))) + ".pid"))
        pc.start()
        subprocess_obj = SubprocessClass()
        # starting main method
        # Taking the current directory path
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        # Creating the logger object and getting the logger
        LOG_DIR = os.path.join(SCRIPT_DIR, "log")
        make_dir(LOG_DIR)
        logger_obj = LoggingHandler(SCRIPT_DIR)
        logger = logger_obj.get_logger(__name__)
        OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
        make_dir(OUTPUT_DIR)
        ARCHIVE_DIR = os.path.join(SCRIPT_DIR, "archive")
        make_dir(ARCHIVE_DIR)
        WAIT = parse_args()

        TIMESTAMP = timestamp()
        CONFIG_FILE_PATH = os.path.join(SCRIPT_DIR, 'config/config.json')
        POD, WHITELIST_ENABLED, WHITELIST_PODS_LIST, SPLUNK_GROUP_USER, SPLUNK_CONTAINER, SFTP_USER, SFTP_PASSWORD, DIR_LOOKUP, FILE_NEWER_THAN_MIN, MAX_PROCESSES, WAIT_TO_START, BLACKLIST_POD = load_config(
            CONFIG_FILE_PATH)
        APP_NAMESPACE = get_application_namespace()
        ADA_NAMESPACE = get_adaptation_namespace()
        SPLUNK_IP = get_splunk_ip(ADA_NAMESPACE)
        SPLUNK_NAME_LIST = get_splunk(ADA_NAMESPACE)
        UID, GID = get_uid_gid_from_splunk(SPLUNK_NAME_LIST, SPLUNK_CONTAINER, SPLUNK_GROUP_USER, ADA_NAMESPACE)
        if WAIT:
            wait_to_start(WAIT_TO_START)

        main(APP_NAMESPACE, POD, SCRIPT_DIR, OUTPUT_DIR, ARCHIVE_DIR, LOG_DIR, WHITELIST_ENABLED, WHITELIST_PODS_LIST,
             SFTP_USER, SFTP_PASSWORD, DIR_LOOKUP, FILE_NEWER_THAN_MIN, SPLUNK_IP, UID, GID, MAX_PROCESSES,
             BLACKLIST_POD)
        pc.stop()
    except Exception as ex:
        print("Failed execution", str(ex))
