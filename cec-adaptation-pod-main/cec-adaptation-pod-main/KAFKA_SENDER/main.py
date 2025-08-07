#!/usr/bin/python3
import argparse
import json
import logging
import logging.config
import os
import random
import socket
import subprocess
from collections import OrderedDict
from datetime import datetime
from typing import List, Any, Dict

from KAFKA_SENDER.KafkaDataSourceBuilder import DataSource, TABLE_KEY

SCRIPT_HOME = os.path.dirname(os.path.realpath(__file__))

USE_KAFKA_PYTHON_2 = False

try:
    from kafka3 import KafkaProducer
except ModuleNotFoundError:
    USE_KAFKA_PYTHON_2 = True
    class KafkaProducer(object):
        def __init__(self):
            self.dummy = ""

    # package_path = os.path.join(SCRIPT_HOME, "kafka_python-2.0.2-py2.py3-none-any.whl")
    # pip.main(['install', package_path])
    # from kafka import KafkaProducer


SUCCESS_STATUS = 'SUCCESS'
FAIL_STATUS = 'FAIL'


def load_config(config_file_path: str):
    logging.info(f"Loading config file {config_file_path}")

    with open(config_file_path, 'r') as f:
        j = json.load(f)

    kafka_clusters = []
    for c in j['kafka']['clusters']:
        kafka_clusters.append((c['name'], c['addresses']))

    kafka_port = j['kafka']['port']
    message_topic = j['kafka']['message_topic']
    timeout_secs = j['kafka']['timeout_secs']

    return kafka_clusters, kafka_port, message_topic, timeout_secs


def load_data_source(file_path: str) -> DataSource:
    logging.info(f"Loading data source file {file_path}")

    with open(file_path, 'r') as f:
        j = json.load(f)

    data_source = DataSource()
    data_source.message = j['message']
    data_source.table = j['table']

    return data_source


def create_kafka_client(kafka_ips: List[str], kafka_port, timeout_secs, is_test_mode: bool):
    bootstrap_servers: List[str] = []

    for ip in kafka_ips:
        bootstrap_servers.append(f"{ip}:{kafka_port}")

    if is_test_mode:
        logging.info(f"Kafka client not created, as running in test mode, servers: {bootstrap_servers}")
        return None

    client = None

    try:
        client = KafkaProducer(bootstrap_servers=bootstrap_servers, client_id="remote-producer-tier2_cc_kpi_feed",  api_version=(1, 0, 0), request_timeout_ms=timeout_secs * 1000)
        logging.info(f"Kafka client created, servers: {bootstrap_servers}")
    except Exception as e:
        logging.exception(f"Failed connecting to Kafka, servers: {bootstrap_servers}")
    finally:
        return client


def publish_message(cluster_name, client: KafkaProducer, message, message_topic, timeout_secs, is_test_mode: bool):
    status = SUCCESS_STATUS

    if is_test_mode:
        logging.info(f"Message not published, as running in test mode, cluster: {cluster_name}")
        return status

    if client:
        try:
            logging.info(f"Sending message to kafka, cluster: {cluster_name}")
            future = client.send(message_topic, message.encode("UTF-8"))
            record_metadata = future.get(timeout=timeout_secs)
            logging.info(f"Message published successfully to kafka, cluster: {cluster_name}")
        except Exception:
            logging.exception(f"Exception publishing message to kafka, cluster: {cluster_name}")
            status = FAIL_STATUS
    else:
        logging.info(f"Skip publishing to kafka as no connection established, cluster: {cluster_name}")
        status = FAIL_STATUS

    return status


def translate_value(value: Any):
    if value == '{random}':
        return str(random.randint(1, 10000000))
    else:
        return value


def process(data_source_file_path: str, ds: DataSource, config_file_path: str, status_file_path: str, is_test_mode: bool):
    if USE_KAFKA_PYTHON_2:
        logging.info("Using Kafka Python 2")
        subprocess.call(f'{SCRIPT_HOME}/kafkaPython2.py {data_source_file_path} {config_file_path} {"-t" if is_test_mode else ""}', shell=True)
        return

    kafka_clusters, kafka_port, message_topic, timeout_secs = load_config(config_file_path)

    local_hostname = socket.gethostname()
    local_ip = socket.gethostbyname(local_hostname)

    logging.info(f"Starting kafka script {'in test mode' if is_test_mode else ''}")
    logging.info(f"local host: {local_hostname}, ip: {local_ip}")

    if len(ds.table) == 0:
        logging.error("Data source has no records")
        return

    status_file_writer = open(status_file_path, "w")

    kafka_client_by_cluster_name = OrderedDict()
    for (cluster_name, server_ips) in kafka_clusters:
        kafka_client_by_cluster_name[cluster_name] = create_kafka_client(server_ips, kafka_port, timeout_secs, is_test_mode)

    msg_struct: Dict[str, Any] = dict()

    for rec_ix, row in enumerate(ds.table):
        is_dummy_message = False

        if len(row) > 3:
            is_dummy_message = ds.table[rec_ix].pop(-1)

        if is_dummy_message:
            logging.info(f"Skipping KPI record {row[:3]} due to is_dummy_message=True")
            continue

        for key, value in ds.message.items():
            if key == TABLE_KEY:
                for col_ix, col_name in enumerate(value):
                    msg_struct[col_name] = ds.table[rec_ix][col_ix]
            else:
                msg_struct[key] = translate_value(value)

        message: str = json.dumps(msg_struct)

        statuses = []
        for cluster_name, client in kafka_client_by_cluster_name.items():
            statuses.append(publish_message(cluster_name, client, message, message_topic, timeout_secs, is_test_mode))

        final_status = FAIL_STATUS if FAIL_STATUS in statuses else SUCCESS_STATUS

        status_file_writer.write(f"{message}.{final_status}\n")

    for cluster_name, client in kafka_client_by_cluster_name.items():
        if client is not None:
            logging.info(f'Closing {cluster_name}')
            client.close()

    status_file_writer.close()


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


def parse_args():
    parser = argparse.ArgumentParser(description="HELP Text for tool.")
    parser.add_argument("data_source_file_path", help="data source file path")
    parser.add_argument('config_file_path', help='configuration file path')
    parser.add_argument("-t", "--test", action='store_true', default=False, help="Run script in test mode")

    args = parser.parse_args()

    return args.data_source_file_path, args.config_file_path, args.test


def make_status_file_path(data_source_file_path, is_test_mode: bool) -> str:
    status_filename = os.path.splitext(os.path.basename(data_source_file_path))[0]
    status_file_path = f"{ARCHIVE_DIR}/{status_filename}.status.{TIMESTAMP}{'.test-mode' if is_test_mode else ''}"
    return status_file_path


if __name__ == '__main__':

    # SCRIPT_HOME = os.path.dirname(os.path.realpath(__file__))
    ARCHIVE_DIR = os.path.join(SCRIPT_HOME, 'archive')
    TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")

    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    try:
        setup_logging(SCRIPT_HOME, 'config/logger-config-kafka.json')
        data_source_file_path, config_file_path, is_test_mode = parse_args()

        logging.info(f'Data source file: {data_source_file_path}, config file: {config_file_path}, test mode: {is_test_mode}')

        status_file_path = make_status_file_path(data_source_file_path, is_test_mode)
        data_source: DataSource = load_data_source(data_source_file_path)

        process(data_source_file_path, data_source, config_file_path, status_file_path, is_test_mode)

        archive_filename = f"{os.path.basename(data_source_file_path)}.{TIMESTAMP}"
        os.replace(data_source_file_path, os.path.join(ARCHIVE_DIR, archive_filename))
    except Exception as e:
        print("Fatal error: " + str(e))
        logging.exception("Fatal error")
