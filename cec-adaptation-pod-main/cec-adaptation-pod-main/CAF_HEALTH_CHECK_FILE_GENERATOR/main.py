#!/usr/bin/python3
import argparse
import json
import logging
import logging.config
import os
import sys

from KPI_SUCCESS import KPI_SUCCESS
from KPI_Helper import banner

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.process_check.ProcessCheck import ProcessCheck


def parse_args():
    parser = argparse.ArgumentParser(description="CAF HEALTH CHECK")
    parser.add_argument('execution_period_minutes', help='Enter the minutes')

    args = parser.parse_args()

    return int(args.execution_period_minutes)


def load_config(config_file_path: str):
    logging.info(f"Loading config file {config_file_path}")

    with open(config_file_path, 'r') as f:
        j = json.load(f)

    perf_data_files_local_dir = j["perf_data_files_local_dir"]

    return perf_data_files_local_dir


def read_success_kpi_config(config_path: str):
    logging.info(f"Loading config file {config_path}")

    with open(config_path, 'r') as f:
        j = json.load(f)
    return j


def setup():
    logging.info(f'Home directory: {SCRIPT_DIR}')

    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR, exist_ok=True)


def make_data_source_file_path() -> str:
    file_path = os.path.join(ARCHIVE_DIR, f'success_kpi.csv')
    return file_path


def main(perf_data_files_local_dir, execution_period_mins):
    data_source_file_path = make_data_source_file_path()
    kpi_caf_obj = KPI_SUCCESS(SCRIPT_DIR, execution_period_mins, perf_data_files_local_dir)
    listOfKPIs = kpi_caf_obj.main(SUCCESS_KPI_CONFIG)

    with open(data_source_file_path, "w") as data_source_ref:
        data_source_ref.writelines(line + '\n' for line in listOfKPIs)


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
        CONFIG_FILE_PATH = os.path.join(SCRIPT_DIR, "config/config.json")

        EXECUTION_PERIOD_MINS = parse_args()
        PERF_DATA_FILES_LOCAL_DIR = load_config(CONFIG_FILE_PATH)

        SUCCESS_KPI_CONFIG_PATH = os.path.join(SCRIPT_DIR, "config/Success_Rate_Kpis_Config.json")
        SUCCESS_KPI_CONFIG = read_success_kpi_config(SUCCESS_KPI_CONFIG_PATH)

        ARCHIVE_DIR = os.path.join(SCRIPT_DIR, "archive")

        setup()
        main(PERF_DATA_FILES_LOCAL_DIR, EXECUTION_PERIOD_MINS)
        pc.stop()

        logging.info(banner("End application"))
    except Exception as ex:
        logging.exception(f"Failed execution ::: {str(ex)}")
