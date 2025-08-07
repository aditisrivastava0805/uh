import os, sys
import socket
import json
import argparse
import time
from datetime import datetime
from typing import Dict

from Logger import LoggingHandler
from KPI_PLATFORM import KPI_PLATFORM
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
    parser.add_argument("--wait", action='store_true', default=False, help="Start processing after configured time lapse")
    parser.add_argument("-t", "--test", action='store_true', default=False, help="Run script in test mode")
    args = parser.parse_args()

    return args.kafka_config_file_path, args.wait, args.test

def load_config(config_file_path: str):
    logger.info(f"Loading config file {config_file_path}")

    with open(config_file_path, 'r') as f:
        j = json.load(f)

    wait_to_start_secs = j["wait_to_start_secs"]
    max_processes = j["max_processes"]
    max_threshold_value = int(j["max_threshold_value"])
    kafka_data_source_template = j["kafka_message_template"]

    return wait_to_start_secs, kafka_data_source_template, max_processes, max_threshold_value

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

def available_pods() -> Dict:
    try:
        cem_dict = {}
        val_dict = {
            "node_type": "",
            "cpu_usage_percentage": 0,
            "mem_usage_percentage": 0
        }
        cmd = f'kubectl top nodes --no-headers --use-protocol-buffers'
        pods, error = subprocess_obj.execute_cmd(cmd)

        if error:
            logger.error(f'Failed fetching pods, cmd: {cmd}')
            return {}

        if not pods:
            logger.error(f'No pods are found')
            return {}

        for pod in pods.splitlines():
            try:
                node_name, cpu_usage, cpu_usage_percentage, mem_usage, mem_usage_percentage = pod.split(maxsplit=4)
                if node_name != "" or node_name is not None:
                    cluster_name = str(node_name).split("-")[-2]
                    cem_dict.update({"cluster_name": cluster_name})
                    if "mn" in node_name:
                        val_dict["node_type"] = "master_node"
                    elif "wn" in node_name:
                        val_dict["node_type"] = "worker_node"
                    val_dict["cpu_usage_percentage"] = int(str(cpu_usage_percentage).replace("%", ""))
                    val_dict["mem_usage_percentage"] = int(str(mem_usage_percentage).replace("%", ""))
                    cem_dict.update({str(node_name): val_dict})
            except Exception as errr:
                logger.error(f"Error while reading pods .... {str(errr)}")
        logger.info(f'Available pods: {cem_dict}')
        return cem_dict
    except Exception as err:
        logger.exception(f"Failed fetching pods : {str(err)}")

def make_kafka_data_source_file_path() -> str:
    today_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    kafka_file_path = os.path.join(ARCHIVE_DIR, f'{HOSTNAME}_KPI.txt.{today_timestamp}')
    return kafka_file_path

def execute(cem_dict, kafka_data_source_template, hostname, script_dir, output_dir, archive_dir, log_dir, kafka_config_file_path, status_file_path, is_test_mode, max_threshold_value):
    kpi_platform_obj = KPI_PLATFORM(hostname, script_dir, output_dir, archive_dir, log_dir)
    kafka_data_source_builder = KafkaDataSourceBuilder(kafka_data_source_template)
    kpi_platform_obj.main((cem_dict, kafka_data_source_builder, max_threshold_value))
    kafka_data_source_file_path = make_kafka_data_source_file_path()
    kafka_data_source_builder.write_to_file(kafka_data_source_file_path)
    kafka_process(kafka_data_source_file_path, kafka_data_source_builder.data_source(), kafka_config_file_path, STATUS_FILE_PATH, is_test_mode)

def main(hostname: str, kafka_data_source_template, script_dir: str, output_dir: str, archive_dir: str, log_dir: str, status_file_path: str, kafka_config_file_path: str, is_test_mode: bool, max_processes: int, max_threshold_value: int):
    # Running all kpi's
    cem_dict = available_pods()
    execute(cem_dict, kafka_data_source_template, hostname, script_dir, output_dir, archive_dir, log_dir, kafka_config_file_path, status_file_path, is_test_mode, max_threshold_value)
    logger.info("ALL PROCESSES ARE DONE")

if __name__ == '__main__':
    try:
        pc = ProcessCheck(os.path.join("/", "tmp", os.path.basename(os.path.dirname(os.path.abspath(__file__))) + ".pid"))
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
        STATUS_FILE_PATH = os.path.join(ARCHIVE_DIR, f'{HOSTNAME}_KPI.status.{TIMESTAMP}')
        CONFIG_FILE_PATH = os.path.join(SCRIPT_DIR, 'config/config.json')
        WAIT_TO_START_SECS, KAFKA_DATA_SOURCE_TEMPLATE, MAX_PROCESSES, MAX_THRESHOLD_VALUE = load_config(CONFIG_FILE_PATH)
        if WAIT:
            wait_to_start(WAIT_TO_START_SECS)
        main(HOSTNAME, KAFKA_DATA_SOURCE_TEMPLATE, SCRIPT_DIR, OUTPUT_DIR, ARCHIVE_DIR, LOG_DIR, STATUS_FILE_PATH, KAFKA_CONFIG_FILE_PATH, IS_TEST_MODE, MAX_PROCESSES, MAX_THRESHOLD_VALUE)
        pc.stop()
    except Exception as ex:
        print("Failed execution", str(ex))
