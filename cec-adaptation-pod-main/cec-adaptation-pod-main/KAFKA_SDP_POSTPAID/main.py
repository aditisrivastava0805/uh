import os, sys
import socket
import json
import argparse
import time
from datetime import datetime
from typing import List
import concurrent.futures

from Logger import LoggingHandler
from KPI_SDP import KPI_SDP
from SubprocessClass import SubprocessClass

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.process_check.ProcessCheck import ProcessCheck
from KAFKA_SENDER.KafkaDataSourceBuilder import KafkaDataSourceBuilder
from KAFKA_SENDER.main import process as kafka_process


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def parse_args():
    parser = argparse.ArgumentParser(description="SDP KPI - Kafka")
    parser.add_argument('kafka_config_file_path', help='Kafka configuration file path')
    parser.add_argument("--wait", action='store_true', default=False,
                        help="Start processing after configured time lapse")
    parser.add_argument("-t", "--test", action='store_true', default=False, help="Run script in test mode")
    args = parser.parse_args()

    return args.kafka_config_file_path, args.wait, args.test


def load_config(config_file_path: str):
    logger.info(f"Loading config file {config_file_path}")

    with open(config_file_path, 'r') as f:
        j = json.load(f)

    wait_to_start_secs = j["wait_to_start_secs"]
    namespace = eval_value(j["namespace"])
    pod = j["pod"]
    pod_container = j["pod_container"]
    max_processes = j["max_processes"]
    whitelist_pod_enable = j["whitelist_pod_enable"]
    whitelist_pods = j["whitelist_pods"]
    kafka_data_source_template = j["kafka_message_template"]
    blacklist_pods = j["blacklist_pods"]

    return wait_to_start_secs, namespace, pod, kafka_data_source_template, whitelist_pod_enable, whitelist_pods, max_processes, pod_container, blacklist_pods


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


def wait_to_start(wait_to_start_secs: int):
    logger.info(f"Waiting {wait_to_start_secs} seconds ... to allow pm data files to arrive")
    time.sleep(wait_to_start_secs)


def make_dir(path: str):
    if not os.path.isdir(path):
        # Creating the folder if not there
        os.makedirs(path, exist_ok=True)


def fetch_hostname():
    cmd = """hostname"""
    hostname, error = SubprocessClass().execute_cmd(cmd)
    if error:
        logger.error(f"Failed fetching hostname, cmd: {cmd}")
        return "undefined-hostname"

    hostname = hostname.strip().upper()
    logger.info(f'Hostname: {hostname}')
    if error:
        raise Exception(f'Hostname could not be determined, error: {error}')
    return hostname


def available_pods(namespace: str, pod: str, whitelist_enabled: str, whitelist_pod_list: list, blacklist_pod_list) -> \
List[str]:
    try:
        pods_list = []
        cmd = f'kubectl get pods -n {namespace} | grep c{pod} | grep -i "csdp.*-0 " | grep -v "csdp.*c.*" | grep -v upgrade'
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
                if str(pod_name).strip() in blacklist_pod_list:
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


def make_kafka_data_source_file_path(pod) -> str:
    today_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    kafka_file_path = os.path.join(ARCHIVE_DIR, f'{HOSTNAME}_{pod}_KPI.txt.{today_timestamp}')
    return kafka_file_path


def execute(pod, counter, kafka_data_source_template, hostname, namespace, main_pod, script_dir, output_dir,
            archive_dir, log_dir, kafka_config_file_path, is_test_mode, pod_container):
    kpi_sdp_obj = KPI_SDP(hostname, namespace, main_pod, script_dir, output_dir,
                          archive_dir, log_dir, pod_container)
    kafka_data_source_builder = KafkaDataSourceBuilder(kafka_data_source_template)
    kpi_sdp_obj.main((pod, counter, kafka_data_source_builder))
    kafka_data_source_file_path = make_kafka_data_source_file_path(pod)
    kafka_data_source_builder.write_to_file(kafka_data_source_file_path)
    STATUS_FILE_PATH = os.path.join(ARCHIVE_DIR, f'{HOSTNAME}_{pod}_KPI.status.{TIMESTAMP}')
    kafka_process(kafka_data_source_file_path, kafka_data_source_builder.data_source(), kafka_config_file_path,
                  STATUS_FILE_PATH, is_test_mode)


def main(hostname: str, namespace: str, main_pod: str, kafka_data_source_template, script_dir: str, output_dir: str,
         archive_dir: str, log_dir: str, kafka_config_file_path: str, whitelist_enabled: str, whitelist_pod_list: list,
         is_test_mode: bool, max_processes: int, pod_container: str, blacklist_pod_list):
    # Running all air kpi's
    counter = 0
    with concurrent.futures.ProcessPoolExecutor(max_processes) as exe:
        for pod in available_pods(namespace, main_pod, whitelist_enabled, whitelist_pod_list, blacklist_pod_list):
            exe.submit(execute, pod, counter, kafka_data_source_template, hostname, namespace, main_pod, script_dir,
                       output_dir, archive_dir, log_dir, kafka_config_file_path, is_test_mode, pod_container)
            counter += 1
    logger.info("ALL PROCESSES ARE DONE")


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
        logger_obj = LoggingHandler(SCRIPT_DIR)
        logger = logger_obj.get_logger(__name__)
        OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
        make_dir(OUTPUT_DIR)
        ARCHIVE_DIR = os.path.join(SCRIPT_DIR, "archive")
        make_dir(ARCHIVE_DIR)
        subprocess_obj = SubprocessClass()

        HOSTNAME = socket.gethostname()
        KAFKA_CONFIG_FILE_PATH, WAIT, IS_TEST_MODE = parse_args()
        TIMESTAMP = timestamp()
        CONFIG_FILE_PATH = os.path.join(SCRIPT_DIR, 'config/config.json')
        WAIT_TO_START_SECS, NAMESPACE, POD, KAFKA_DATA_SOURCE_TEMPLATE, WHITELIST_ENABLED, WHITELIST_PODS_LIST, MAX_PROCESSES, POD_CONTAINER, BLACKLIST_POD = load_config(
            CONFIG_FILE_PATH)
        if WAIT:
            wait_to_start(WAIT_TO_START_SECS)
        main(HOSTNAME, NAMESPACE, POD, KAFKA_DATA_SOURCE_TEMPLATE, SCRIPT_DIR, OUTPUT_DIR, ARCHIVE_DIR, LOG_DIR,
             KAFKA_CONFIG_FILE_PATH, WHITELIST_ENABLED, WHITELIST_PODS_LIST, IS_TEST_MODE, MAX_PROCESSES, POD_CONTAINER,
             BLACKLIST_POD)
        pc.stop()
    except Exception as ex:
        print("Failed execution", str(ex))
