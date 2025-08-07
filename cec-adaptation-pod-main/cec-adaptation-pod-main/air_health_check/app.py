import json
import logging
import logging.config
import os
import threading
from datetime import datetime, timedelta

from flask import Flask, jsonify

from CommandExecutor import CommandExecutor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

global_result = {}
last_result_refresh_time: datetime = datetime.min
result_refresh_interval = timedelta(seconds=10)
result_lock = threading.Lock()


app = Flask(__name__)

@app.route("/air_pod/status")
def http_get_air_pod_health_status():
    logging.info('Received HTTP status request')
    response = fetch_result()
    logging.info(f'HTTP response: {response}')
    return response


def get_air_pod_health_status():
    logging.info('Refreshing result')

    command_executor = CommandExecutor(config_json, config_json.get('is_unhealthy_test_mode', False))
    data, error = command_executor.run(command_json)

    if error:
        data = {error}

    return jsonify(data=data)


def fetch_result():
    with result_lock:
        global global_result
        global last_result_refresh_time

        if datetime.now() > (last_result_refresh_time + result_refresh_interval):
            global_result = get_air_pod_health_status()
            last_result_refresh_time = datetime.now()
        else:
            logging.info(f'Using cached result from {last_result_refresh_time}')

        return global_result


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


def read_json_file(file_path):
    with open(file_path) as f:
        return json.load(f)


if __name__ == '__main__':
    try:
        setup_logging(SCRIPT_DIR, 'logger-config.json')

        config_json = read_json_file(os.path.join(SCRIPT_DIR, 'AirPodConfigurationFile.json'))
        logging.info(f"Configuration file {config_json}")

        command_json = read_json_file(os.path.join(SCRIPT_DIR, 'AirPodCommandFile.json'))
        logging.info(f"command json file {command_json}")

        app.run(host=config_json["host"], port=config_json["port"])
    except Exception as err:
        logging.exception(err)
