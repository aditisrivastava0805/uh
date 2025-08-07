#!/usr/bin/python3
import argparse
import json
import logging
import logging.config
import os
import sys
import time
from datetime import datetime
from typing import List, Dict

from KPI_CAF import KPI_CAF
from SubprocessClass import SubprocessClass
from KPI_Helper import banner

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.process_check.ProcessCheck import ProcessCheck
from KAFKA_SENDER.KafkaDataSourceBuilder import KafkaDataSourceBuilder
from KAFKA_SENDER.main import process as kafka_process


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def parse_args():
    parser = argparse.ArgumentParser(description="CAF KPI - Kafka")
    parser.add_argument('config_file_path', help='CAF KPI configuration file path')
    parser.add_argument('kafka_config_file_path', help='Kafka configuration file path')
    parser.add_argument("--wait", action='store_true', default=False,
                        help="Start processing after configured time lapse")
    parser.add_argument("-t", "--test", action='store_true', default=False, help="Run script in test mode")

    args = parser.parse_args()

    return args.config_file_path, args.kafka_config_file_path, args.wait, args.test


def load_config(config_file_path: str):
    logging.info(f"Loading config file {config_file_path}")

    with open(config_file_path, 'r') as f:
        j = json.load(f)

    wait_to_start_secs = j["wait_to_start_secs"]
    namespace_command = j["namespace_command"]
    pod = j["pod"]
    dir_lookup = j["dir_lookup"]
    perf_data_files_local_dir = j["perf_data_files_local_dir"]
    execution_period_mins = j["execution_period_mins"]
    kafka_message_template = j["kafka_message_template"]

    return wait_to_start_secs, namespace_command, pod, dir_lookup, perf_data_files_local_dir, execution_period_mins, kafka_message_template


def read_alarm_kpi_config(config_path: str):
    logging.info(f"Loading config file {config_path}")

    with open(config_path, 'r') as f:
        j = json.load(f)
    return j


def read_latency_kpi_config(config_path: str):
    logging.info(f"Loading config file {config_path}")

    with open(config_path, 'r') as f:
        j = json.load(f)
    return j


def read_counter_value_kpi_config(config_path: str):
    logging.info(f"Loading config file {config_path}")

    with open(config_path, 'r') as f:
        j = json.load(f)
    return j


def read_script_kpi_config(config_path: str):
    logging.info(f"Loading config file {config_path}")

    with open(config_path, 'r') as f:
        j = json.load(f)
    return j


def read_success_kpi_config(config_path: str):
    logging.info(f"Loading config file {config_path}")

    with open(config_path, 'r') as f:
        j = json.load(f)
    return j


def fetch_namespace(ns_command: str):
    namespace, error = SubprocessClass().execute_cmd(ns_command)
    if error:
        logging.error(f"Failed fetching hostname, cmd: {ns_command}")
        return "undefined-hostname"
    namespace = namespace.strip()
    logging.info(f'namespace: {namespace}')
    if error:
        raise Exception(f'namespace could not be determined, error: {error}')
    return namespace


def fetch_hostname(ns: str, pm_bulk: str):
    # cmd = f"""helm get values `helm ls -n {ns} | grep {ns} |  awk '{{print $1}}'` -n {ns} | grep applicationId | awk  '{{print $2}}' | awk -F- '{{print $1}}'"""
    cmd = f"echo $HOSTNAME"
    hostname, error = SubprocessClass().execute_cmd(cmd)
    if error:
        logging.error(f"Failed fetching hostname, cmd: {cmd}")
        return "UNDEFINED_HOSTNAME"
    if hostname:
        hostname = hostname.strip()
        logging.info(f'Hostname: {hostname}')
        return hostname
    return "UNDEFINED_HOSTNAME"


def fetch_ip_by_hostname(ns: str, hostname: str, pm_bulk: str):
    cmd = f"""grep {hostname} /etc/hosts | awk -F' ' '{{print $1}}' """
    ip, error = SubprocessClass().execute_cmd(cmd)
    if error:
        logging.error(f"Failed fetching hostname, cmd: {cmd}")
        return "UNDEFINED_HOSTNAME"

    if ip:
        ip = ip.strip().upper()
        logging.info(f'Hostname: {hostname}')
        return ip
    return "UNDEFINED_HOSTNAME"


def setup():
    logging.info(f'Home directory: {SCRIPT_DIR}')

    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR, exist_ok=True)


def available_pods(namespace: str, pod: str) -> List[str]:
    try:
        pods = []
        cmd = f'kubectl get pods -n {namespace} | grep {pod}'
        csa_pods, error = SubprocessClass().execute_cmd(cmd)

        if error:
            logging.error(f'Failed fetching pods, cmd: {cmd}')
            return []

        if not csa_pods:
            logging.error(f'No pods are found, namespace: {namespace}, pod pattern: {pod}')
            return []

        for pod in csa_pods.splitlines():
            pod_name, balancer, ip, p_ip, port = pod.split(maxsplit=4)
            pods.append(str(pod_name))
        logging.info('Available pods: {pods}')
        return pods
    except Exception as err:
        logging.exception(f"Failed fetching pods ::: {str(err)}")


def make_kafka_data_source_file_path(air, hostname: str) -> str:
    today_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    kafka_file_path = os.path.join(ARCHIVE_DIR, f'{hostname}_{air}_KPI.txt.{today_timestamp}')
    return kafka_file_path


def main(namespace: str, pod: str, perf_data_files_local_dir, execution_period_mins,
         kafka_message_template: Dict[str, object], is_test_mode: bool):
    logging.info(f"Running in test mode: {is_test_mode}")
    for pod in available_pods(namespace, pod):
        hostname = fetch_hostname(namespace, pod)
        ip = fetch_ip_by_hostname(namespace, hostname, pod)
        STATUS_FILE_PATH = os.path.join(ARCHIVE_DIR, f'{hostname}_KPI.status.{TIMESTAMP}')
        kafka_data_source_builder = KafkaDataSourceBuilder(kafka_message_template)
        kpi_caf_obj = KPI_CAF(SCRIPT_DIR, hostname, namespace, execution_period_mins, perf_data_files_local_dir,
                              kafka_data_source_builder, is_test_mode)
        kpi_caf_obj.main(pod, namespace, hostname, ip, kafka_data_source_builder, ALARM_KPI_CONFIG, LATENCY_KPI_CONFIG,
                         SCRIPT_KPI_CONFIG, SUCCESS_KPI_CONFIG, COUNTER_KPI_CONFIG)
        kafka_data_source_file_path = make_kafka_data_source_file_path(pod, hostname)
        kafka_data_source_builder.write_to_file(kafka_data_source_file_path)
        kafka_process(kafka_data_source_file_path, kafka_data_source_builder.data_source(), KAFKA_CONFIG_FILE_PATH,
                      STATUS_FILE_PATH, is_test_mode)


def wait_to_start(wait_to_start_secs: int):
    logging.info(f"Waiting {wait_to_start_secs} seconds ... to allow pm data files to arrive")
    time.sleep(wait_to_start_secs)


def setup_logging(app_dir, config_file_path):
    log_path = os.path.join(app_dir, 'log')

    os.makedirs(log_path, exist_ok=True)

    with open(os.path.join(app_dir, config_file_path)) as f:
        config = json.load(f)

    for handler, body in config['handlers'].items():
        if body['filename']:
            filename = body['filename']
            filename = filename.replace('{app-path}', app_dir)
            body['filename'] = filename

    logging.config.dictConfig(config)


if __name__ == '__main__':

    try:
        pc = ProcessCheck(
            os.path.join("/", "tmp", os.path.basename(os.path.dirname(os.path.abspath(__file__))) + ".pid"))
        pc.start()
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        setup_logging(SCRIPT_DIR, 'config/logger-config.json')

        logging.info(banner("Start application"))

        CONFIG_FILE_PATH, KAFKA_CONFIG_FILE_PATH, WAIT, IS_TEST_MODE = parse_args()
        WAIT_TO_START_SECS, NAMESPACE_CMD, POD, DIR_LOOKUP, PERF_DATA_FILES_LOCAL_DIR, EXECUTION_PERIOD_MINS, KAFKA_MESSAGE_TEMPLATE = load_config(
            CONFIG_FILE_PATH)

        ALARM_KPI_CONFIG_PATH = os.path.join(SCRIPT_DIR, "config/Alarm_Kpi_Config.json")
        ALARM_KPI_CONFIG = read_alarm_kpi_config(ALARM_KPI_CONFIG_PATH)

        LATENCY_KPI_CONFIG_PATH = os.path.join(SCRIPT_DIR, "config/Latency_Kpis_Config.json")
        LATENCY_KPI_CONFIG = read_latency_kpi_config(LATENCY_KPI_CONFIG_PATH)

        SCRIPT_KPI_CONFIG_PATH = os.path.join(SCRIPT_DIR, "config/Script_Based_Kpi_Config.json")
        SCRIPT_KPI_CONFIG = read_script_kpi_config(SCRIPT_KPI_CONFIG_PATH)

        SUCCESS_KPI_CONFIG_PATH = os.path.join(SCRIPT_DIR, "config/Success_Rate_Kpis_Config.json")
        SUCCESS_KPI_CONFIG = read_success_kpi_config(SUCCESS_KPI_CONFIG_PATH)

        COUNTER_KPI_CONFIG_PATH = os.path.join(SCRIPT_DIR, "config/Counter_Value_Kpis_Config.json")
        COUNTER_KPI_CONFIG = read_counter_value_kpi_config(COUNTER_KPI_CONFIG_PATH)

        NAMESPACE = fetch_namespace(NAMESPACE_CMD)
        TIMESTAMP = timestamp()
        ARCHIVE_DIR = os.path.join(SCRIPT_DIR, "archive")

        if WAIT:
            wait_to_start(WAIT_TO_START_SECS)
        setup()
        main(NAMESPACE, POD, PERF_DATA_FILES_LOCAL_DIR, EXECUTION_PERIOD_MINS, KAFKA_MESSAGE_TEMPLATE, IS_TEST_MODE)
        pc.stop()

        logging.info(banner("End application"))
    except Exception as ex:
        logging.exception(f"Failed execution ::: {str(ex)}")
