#!/usr/bin/python3

import argparse
import glob
import json
import logging
import logging.config
import os
import time
from os import stat_result
from typing import Tuple, Optional

from kubernetes import helm_hostname
from proc2 import eval_value
from collector import collect_files
from forwarder import forward_files

HOSTNAME_UNDEFINED = "hostname_undefined"

def parse_args():
    parser = argparse.ArgumentParser(description="Tool for fetching files from PODs")
    parser.add_argument("--wait", action='store_true', default=False, help="Start processing after configured time lapse")
    parser.add_argument('config_file', help='configuration file path')

    args = parser.parse_args()

    return args.wait, args.config_file


def setup_logging(app_dir, app_name, config_file_path):
    log_path = os.path.join(app_dir, 'log')

    os.makedirs(log_path, exist_ok=True)

    with open(os.path.join(app_dir, config_file_path)) as f:
        config = json.load(f)

    for handler, body in config['handlers'].items():
        if body['filename']:
            filename = body['filename']
            filename = filename.replace('{app-path}', app_dir)
            filename = filename.replace('{app-name}', app_name)
            body['filename'] = filename

    logging.config.dictConfig(config)


def load_config(config_file_path):
    logging.info("Loading app configuration")

    with open(config_file_path) as f:
        j = json.load(f)

    WAIT_TO_START_SECS = j['WAIT_TO_START_SECS']
    CONTAINER_PATTERN = j['CONTAINER_PATTERN']
    POD_PATTERN = j['POD_PATTERN']
    NAMESPACE_PATTERN = eval_value(j['NAMESPACE_PATTERN'])
    SOURCE_FOLDER = j['SOURCE_FOLDER']
    FILE_NEWER_THAN_MINS = j['FILE_NEWER_THAN_MINS']
    DESTINATION_FOLDER = j['DESTINATION_FOLDER']
    DESTINATION_FILENAME = j['DESTINATION_FILENAME']
    FORWARD_STRUCTS = j['FORWARD_STRUCTS']
    SFTP_DICT = j['SFTP']

    return WAIT_TO_START_SECS, CONTAINER_PATTERN, POD_PATTERN, NAMESPACE_PATTERN, SOURCE_FOLDER, FILE_NEWER_THAN_MINS, DESTINATION_FOLDER, DESTINATION_FILENAME, FORWARD_STRUCTS, SFTP_DICT


def onwer_and_group(path) -> Tuple[int, int]:
    stat: stat_result = os.stat(path)
    return stat.st_uid, stat.st_gid


def wait_to_start(wait_to_start_secs):
    logging.info(f"Waiting {wait_to_start_secs} seconds ...")
    time.sleep(wait_to_start_secs)


def fetch_hostname_from_previous_valid_file(source_dir: str) -> Optional[str]:
    for file_path in sorted(filter(os.path.isfile, glob.glob(os.path.join(source_dir, '*'))), key=os.path.getmtime, reverse=True):
        filename = os.path.basename(file_path)
        if '_' in filename and not filename.startswith(HOSTNAME_UNDEFINED):
            hostname = filename.split('_')[0]
            logging.info(f"Using hostname from prefix of previous valid file: {filename}, prefix (hostname): {hostname} ")
            return hostname
    return None


def hostname(namespace_pattern: str, source_dir: str):
    hostname = helm_hostname(namespace_pattern)

    if hostname:
        return hostname

    hostname = fetch_hostname_from_previous_valid_file(source_dir)

    if hostname:
        return hostname

    return HOSTNAME_UNDEFINED

if __name__ == "__main__":
    SCRIPT_HOME = os.path.dirname(os.path.realpath(__file__))

    try:
        wait, config_file_path = parse_args()
        app_name = os.path.basename(config_file_path).replace("config-", "").replace(".json", "")
        setup_logging(SCRIPT_HOME, app_name, 'config/logger-config.json')
        wait_to_start_secs, container_pattern, pod_pattern, namespace_pattern, source_folder, file_newer_than_mins, dest_folder, dest_filename, forward_structs, sftp_dict = load_config(config_file_path)

        if wait:
            wait_to_start(wait_to_start_secs)

        # Creating output directory to store xml file
        script_path = os.path.join(SCRIPT_HOME, app_name)
        output_path = os.path.join(script_path, "output")
        if not os.path.isdir(output_path):
            # Creating the folder if not there
            os.makedirs(output_path, exist_ok=True)

        logging.info("--- Application Start ---")
        owner, group = onwer_and_group(dest_folder)

        hostname = hostname(namespace_pattern, dest_folder)

        file_paths = collect_files(hostname, container_pattern, pod_pattern, namespace_pattern, source_folder, file_newer_than_mins, dest_folder, dest_filename, owner, group, sftp_dict)

        if file_paths:
            forward_files(file_paths, forward_structs, output_path)

        logging.info("--- Application End ---")
    except Exception as ex:
        logging.exception("Fatal error")
