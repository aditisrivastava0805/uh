import os
import json
import logging
import logging.config
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from JsonReaderClass import JsonReader
from CommandExecutor import CommandExecutor


# Taking the current directory path
script_dir = os.path.dirname(__file__)
command_file_path = os.path.join(script_dir, 'AFPodCommandFile.json')
config_file_path = os.path.join(script_dir, 'AFPodConfigurationFile.json')

# Loading JsonReader class and getting configuration file data
config_json_obj = JsonReader()
config_json = config_json_obj.read_json_file(config_file_path)
logging.info(f"Configuration file {config_json}")

# Getting Command file data
command_json = config_json_obj.read_json_file(command_file_path)
logging.info(f"command_json file {command_json}")

CommandExecutor_obj = CommandExecutor(command_json, config_json, config_json.get('is_unhealthy_test_mode', False))
CommandExecutor_obj.run()
sched = BackgroundScheduler(daemon=True, job_defaults={'max_instances': 2})
sched.add_job(CommandExecutor_obj.run, 'interval', seconds=config_json["schedule_time_seconds"])
sched.start()

# Creating the app
app = Flask(__name__)


@app.route("/af_pod/status")
def get_air_pod_health_status():
    """
    Running the Command Executor Class and getting Data.

    :return: Returning the Data as a Json.
    """
    data = CommandExecutor_obj.get_data()
    logging.info(f"data is {str(data)}")
    return jsonify(data=data)


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
        setup_logging(script_dir, 'logger-config.json')
        app.run(host=config_json["host"], port=config_json["port"])
    except Exception as err:
        logging.error(f"Exception in __main__ ::: {str(err)}")