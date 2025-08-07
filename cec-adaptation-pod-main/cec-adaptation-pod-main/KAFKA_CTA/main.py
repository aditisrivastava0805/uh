#!/usr/bin/sudo /usr/bin/python3
import argparse
import json
import logging
import logging.config
import os
import sys
import time
from datetime import datetime
from typing import List

from KPI_CTA import KPI_CTA
from SubprocessClass import SubprocessClass
from KPI_Helper import banner, delete_files_older_than_days

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.process_check.ProcessCheck import ProcessCheck
from KAFKA_SENDER.KafkaDataSourceBuilder import KafkaDataSourceBuilder
from KAFKA_SENDER.main import process as kafka_process


def timespatmp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def parse_args():
    parser = argparse.ArgumentParser(description="CTA KPI - Kafka")
    parser.add_argument('config_file_path', help='CTA KPI configuration file path')
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
    namespace = j["namespace"]
    pod = j["pod"]
    dir_lookup = j["dir_lookup"]
    perf_data_files_local_dir = j["perf_data_files_local_dir"]
    dsc_credentials = j["dsc_credentials"]
    execution_period_mins = j["execution_period_mins"]
    kafka_data_source_builder = KafkaDataSourceBuilder(j["kafka_message_template"])

    return wait_to_start_secs, namespace, pod, dir_lookup, perf_data_files_local_dir, execution_period_mins, kafka_data_source_builder, dsc_credentials


def fetch_hostname(ns: str):
    cmd = f"""helm get values `helm ls -n {ns} | grep eric-cloud-native-base | awk '{{print $1}}'` -n {ns} | grep applicationId | tail -n 1 | awk '{{print $2}}'"""
    hostname, error = SubprocessClass().execute_cmd(cmd)
    if error:
        logging.error(f"Failed fetching hostname, cmd: {cmd}")
        sys.exit(1)
        # return "undefined-hostname"

    hostname = hostname.strip().upper()
    logging.info(f'Hostname: {hostname}')
    if hostname == "":
        logging.info(f"No hostname found, cmd: {cmd}")
        sys.exit(1)
    if error:
        raise Exception(f'Hostname could not be determined, error: {error}')
    return hostname


def get_namespace(cmd: str):
    ns, error = SubprocessClass().execute_cmd(cmd)

    if error:
        logging.error(f"Failed fetching Namespace, cmd: {cmd}")
        return "undefined-namespace"

    ns = str(ns).strip()
    logging.info(f'Namespace: {ns}')

    return ns


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


def make_kafka_data_source_file_path(air) -> str:
    today_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    kafka_file_path = os.path.join(ARCHIVE_DIR, f'{HOSTNAME}_{air}_KPI.txt.{today_timestamp}')
    return kafka_file_path


def main(hostname: str, namespace: str, pod: str, perf_data_files_local_dir, execution_period_mins,
         kafka_data_source_builder: KafkaDataSourceBuilder, dsc_ip: str, dsc_user: str, dsc_pass: str,
         is_test_mode: bool):
    logging.info(f"Running in test mode: {is_test_mode}")
    kpi_cta_obj = KPI_CTA(SCRIPT_DIR, hostname, namespace, execution_period_mins, perf_data_files_local_dir,
                          is_test_mode)
    for pod in available_pods(namespace, pod):
        kpi_cta_obj.main(pod, kafka_data_source_builder, dsc_ip, dsc_user, dsc_pass)
        kafka_data_source_file_path = make_kafka_data_source_file_path(pod)
        kafka_data_source_builder.write_to_file(kafka_data_source_file_path)
        kafka_process(kafka_data_source_file_path, kafka_data_source_builder.data_source(), KAFKA_CONFIG_FILE_PATH,
                      STATUS_FILE_PATH, is_test_mode)

    delete_files_older_than_days(ARCHIVE_DIR, 7)


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

        TIMESTAMP = timespatmp()
        ARCHIVE_DIR = os.path.join(SCRIPT_DIR, "archive")
        CONFIG_FILE_PATH, KAFKA_CONFIG_FILE_PATH, WAIT, IS_TEST_MODE = parse_args()
        WAIT_TO_START_SECS, NAMESPACE, POD, DIR_LOOKUP, PERF_DATA_FILES_LOCAL_DIR, EXECUTION_PERIOD_MINS, KAFKA_DATA_SOURCE_BUILDER, DSC_CREDENTIALS = load_config(
            CONFIG_FILE_PATH)

        # Get namespace from command
        NAMESPACE = get_namespace(NAMESPACE)
        DSC_IP = DSC_CREDENTIALS[NAMESPACE]["dsc_admin_ip"]
        DSC_USER = DSC_CREDENTIALS[NAMESPACE]["dsc_admin_user"]
        DSC_PASS = DSC_CREDENTIALS[NAMESPACE]["dsc_admin_pass"]
        HOSTNAME = fetch_hostname(NAMESPACE)
        STATUS_FILE_PATH = os.path.join(ARCHIVE_DIR, f'{HOSTNAME}_KPI.status.{TIMESTAMP}')
        if WAIT:
            wait_to_start(WAIT_TO_START_SECS)
        setup()
        main(HOSTNAME, NAMESPACE, POD, PERF_DATA_FILES_LOCAL_DIR, EXECUTION_PERIOD_MINS, KAFKA_DATA_SOURCE_BUILDER,
             DSC_IP, DSC_USER, DSC_PASS, IS_TEST_MODE)
        pc.stop()

        logging.info(banner("End application"))
    except Exception as ex:
        logging.exception(f"Failed execution {str(ex)}")
        sys.exit(1)
