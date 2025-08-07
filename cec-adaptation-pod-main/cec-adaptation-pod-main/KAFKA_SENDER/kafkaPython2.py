#!/usr/bin/python2
import argparse
import json
import logging
import logging.config
import os
import random
import socket
from collections import OrderedDict
from datetime import datetime
from kafka import SimpleProducer, KafkaClient
from KafkaDataSourceBuilder import DataSource, TABLE_KEY

SCRIPT_HOME = os.path.dirname(os.path.realpath(__file__))

SUCCESS_STATUS = 'SUCCESS'
FAIL_STATUS = 'FAIL'


def load_config(config_file_path):
    logging.info("Loading config file " + config_file_path)

    with open(config_file_path, 'r') as f:
        j = json.load(f)

    kafka_clusters = []
    for c in j['kafka']['clusters']:
        kafka_clusters.append((c['name'], c['addresses']))

    kafka_port = j['kafka']['port']
    message_topic = j['kafka']['message_topic']
    timeout_secs = j['kafka']['timeout_secs']

    return kafka_clusters, kafka_port, message_topic, timeout_secs


def load_data_source(file_path):
    logging.info("Loading data source file: " + file_path)

    with open(file_path, 'r') as f:
        j = json.load(f)

    data_source = DataSource()
    data_source.message = j['message']
    data_source.table = j['table']

    return data_source


def create_kafka_client(server_ips, kafka_port, timeout_secs, is_test_mode):
    # if is_test_mode:
    #     logging.info("Kafka client not created, as running in test mode, ips: {}".format(server_ips))
    #     return None

    servers = []

    for ip in server_ips:
        servers.append("{}:{}".format(ip, kafka_port))

    try:
        kafka = KafkaClient(servers,  client_id="remote-producer-tier2_cc_kpi_feed", timeout=timeout_secs)
        client = SimpleProducer(kafka)
        logging.info("Kafka client created, servers: {}".format(servers))
        return client
    except Exception as e:
        logging.exception("Exception connecting Kafka, servers: {}".format(servers))
        return None


def publish_message(cluster_name, client, message, message_topic, is_test_mode):
    status = SUCCESS_STATUS

    try:
        if is_test_mode:
            logging.info("Message not published, as running in test mode, destination: {}".format(cluster_name))
        else:
            if client:
                client.send_messages(message_topic, message.encode("UTF-8"))
                logging.info("Message published successfully to kafka, destination: {}".format(cluster_name))
            else:
                logging.info("Skip publishing to kafka as no connection established, destination: {}".format(cluster_name))
                status = FAIL_STATUS

    except Exception as e:
        logging.exception("Exception publishing message to kafka, destination: {}".format(cluster_name))
        status = FAIL_STATUS

    return status


def translate_value(value):
    if value == '{random}':
        return str(random.randint(1, 10000000))
    else:
        return value


def process(ds, config_file_path, status_file_path, is_test_mode):
    kafka_clusters, kafka_port, message_topic, timeout_secs = load_config(config_file_path)

    local_hostname = socket.gethostname()
    local_ip = socket.gethostbyname(local_hostname)

    logging.info("Starting kafka script " + 'in test mode' if is_test_mode else '')
    logging.info("local host: " + local_hostname + 'ip: ' + local_ip)

    if len(ds.table) == 0:
        logging.error("Data source has no records")
        return

    status_file_writer = open(status_file_path, "w")

    kafka_client_by_cluster_name = OrderedDict()
    for (cluster_name, server_ips) in kafka_clusters:
        kafka_client_by_cluster_name[cluster_name] = create_kafka_client(server_ips, kafka_port, timeout_secs, is_test_mode)

    msg_struct = dict()

    for rec_ix in range(len(ds.table)):
        for key, value in ds.message.items():
            if key == TABLE_KEY:
                for col_ix, col_name in enumerate(value):
                    msg_struct[col_name] = ds.table[rec_ix][col_ix]
            else:
                msg_struct[key] = translate_value(value)

        message = json.dumps(msg_struct)

        statuses = []
        for cluster_name, client in kafka_client_by_cluster_name.items():
            statuses.append(publish_message(cluster_name, client, message, message_topic, is_test_mode))

        final_status = FAIL_STATUS if FAIL_STATUS in statuses else SUCCESS_STATUS

        status_file_writer.write(message + '.' + final_status + '\n')

    for cluster_name, client in kafka_client_by_cluster_name.items():
        if client is not None:
            logging.info('Closing ' + cluster_name)
            client.stop()

    status_file_writer.close()


def setup_logging(app_dir, config_file_path):
    logging.info("Setup_logging, app dir: " + app_dir + ", Config path: " + config_file_path)

    log_path = os.path.join(app_dir, 'log')

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    with open(os.path.join(app_dir, config_file_path)) as f:
        config = json.load(f)

    for handler, body in config['handlers'].items():
        if body['filename']:
            filename = body['filename']
            filename = filename.replace('{app-path}', app_dir)
            body['filename'] = filename

    logging.config.dictConfig(config)


def parse_args():
    logging.info("Kafka 2: parse_args")

    parser = argparse.ArgumentParser(description="HELP Text for tool.")
    parser.add_argument("data_source_file_path", help="data source file path")
    parser.add_argument('config_file_path', help='configuration file path')
    parser.add_argument("-t", "--test", action='store_true', default=False, help="Run script in test mode")

    args = parser.parse_args()

    return args.data_source_file_path, args.config_file_path, args.test


def make_status_file_path(data_source_file_path, is_test_mode):
    status_filename = os.path.splitext(os.path.basename(data_source_file_path))[0]
    status_file_path = ARCHIVE_DIR + '/' + status_filename + '.status.' + TIMESTAMP + ('.test-mode' if is_test_mode else '')
    return status_file_path


if __name__ == '__main__':

    # SCRIPT_HOME = os.path.dirname(os.path.realpath(__file__))
    ARCHIVE_DIR = os.path.join(SCRIPT_HOME, 'archive')
    TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")

    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)

    try:
        setup_logging(SCRIPT_HOME, 'config/logger-config-kafka.json')
        data_source_file_path, config_file_path, is_test_mode = parse_args()

        logging.info('Data source file: ' + data_source_file_path + ', config file: ' + config_file_path + ', test mode: ' + str(is_test_mode))

        status_file_path = make_status_file_path(data_source_file_path, is_test_mode)
        data_source = load_data_source(data_source_file_path)

        process(data_source, config_file_path, status_file_path, is_test_mode)

        archive_filename = os.path.basename(data_source_file_path) + '.' + TIMESTAMP
        os.rename(data_source_file_path, os.path.join(ARCHIVE_DIR, archive_filename))
    except Exception as e:
        print("Fatal error: " + str(e))
        logging.exception("Fatal error")
