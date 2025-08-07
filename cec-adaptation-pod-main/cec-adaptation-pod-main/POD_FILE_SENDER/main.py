#!/usr/bin/python3

import argparse
import glob
import json
import logging
import logging.config
import os
import time

from proc2 import eval_value
from forwarder import forward_files
from collector import collect_files

HOSTNAME_UNDEFINED = "hostname_undefined"


def parse_args():
    parser = argparse.ArgumentParser(description="Tool for fetching files from PODs")
    parser.add_argument("--wait", action='store_true', default=False,
                        help="Start processing after configured time lapse")
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
    SOURCE_FOLDER = j['SOURCE_FOLDER']
    APPLICATION_NAME_PATTERN = eval_value(j['APPLICATION_NAME_PATTERN'])
    NUMBER_OF_LAST_UPDATED_FILES = j['NUMBER_OF_LAST_UPDATED_FILES']
    FORWARD_STRUCTS = j['FORWARD_STRUCTS']

    return WAIT_TO_START_SECS, SOURCE_FOLDER, NUMBER_OF_LAST_UPDATED_FILES, FORWARD_STRUCTS, APPLICATION_NAME_PATTERN


def wait_to_start(wait_to_start_secs):
    logging.info(f"Waiting {wait_to_start_secs} seconds ...")
    time.sleep(wait_to_start_secs)


if __name__ == "__main__":
    SCRIPT_HOME = os.path.dirname(os.path.realpath(__file__))

    try:
        wait, config_file_path = parse_args()
        app_name = os.path.basename(config_file_path).replace("config-", "").replace(".json", "")
        setup_logging(SCRIPT_HOME, app_name, 'config/logger-config.json')
        wait_to_start_secs, source_folder, number_of_last_updated_files, forward_structs, application_name_pattern = load_config(
            config_file_path)

        if wait:
            wait_to_start(wait_to_start_secs)

        # Creating output directory to store xml file
        script_path = os.path.join(SCRIPT_HOME, app_name)
        output_path = os.path.join(script_path, "output")
        if not os.path.isdir(output_path):
            # Creating the folder if not there
            os.makedirs(output_path, exist_ok=True)

        logging.info("--- Application Start ---")
        # owner, group = onwer_and_group(dest_folder)

        # hostname = hostname(namespace_pattern, dest_folder)

        file_paths = collect_files(source_folder, number_of_last_updated_files)

        if file_paths:
            forward_files(file_paths, forward_structs, output_path, application_name_pattern)

        logging.info("--- Application End ---")
    except Exception as ex:
        logging.exception("Fatal error")
