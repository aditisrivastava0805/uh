#!/usr/bin/python3
# Copyright (c) 2023 Ericsson Inc
# All rights reserved.
# The Copyright to the computer program(s) herein is the property of Ericsson AB, Sweden.
# The program(s) may be used and/or copied with the written permission from Ericsson AB
# or in accordance with the terms and conditions stipulated in the agreement/contract
# under which the program(s) have been supplied.
#
#
# Fetches multiple KPI parameters and formats/outputs to a timestamped AIR_KPI file for kafka input
# No input parameters are needed for this execution
#
#       Author(s) : Ankit Kumar jain
#          Created : 2023-03-06
#
#     Version history:
#
# 1.0     2023-03-06 First version

import sys
import os
import subprocess
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.process_check.ProcessCheck import ProcessCheck
from lib.Namespace import get_adaptation_namespace


def execute(cmd):
    """
    Executing the command with the help of Subprocess Module.
    :param cmd: command
    :return: output, error
    """
    result = None
    try:
        result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = result.communicate()
        out = out.decode("utf-8")
        err = err.decode("utf-8")
        if out == "" and err == "":
            return None, None
        elif out == "":
            return None, err
        return out, None
    except Exception as error:
        print("Exception while executing command : " + str(error))
    finally:
        result.terminate()  # send sigterm, or ...
        result.kill()


def load_config(config_file_path: str):
    """
    Loading the configuration file.
    :param config_file_path: Configuration file path.
    :return: namespace, local_files_retention_days, local_paths_list, splunk_files_retention_days, splunk_paths_list, splunk_container, tpim_files_retention_days, tpim_paths_list
    """
    print(f"Loading config file {config_file_path}")

    with open(config_file_path, 'r') as f:
        j = json.load(f)

    local_files_retention_days = j["local"]["files_retention_days"]
    local_files_retention_days -= 2
    local_paths_list = j["local"]["paths"]
    splunk_files_retention_days = j["splunk"]["files_retention_days"]
    splunk_files_retention_days -= 2
    splunk_paths_list = j["splunk"]["paths"]
    splunk_container = j["splunk"]["container"]
    tpim_files_retention_days = j["tpim"]["files_retention_days"]
    tpim_files_retention_days -= 2
    tpim_paths_list = j["tpim"]["paths"]

    return str(local_files_retention_days), local_paths_list, str(splunk_files_retention_days), splunk_paths_list, splunk_container, str(tpim_files_retention_days), tpim_paths_list


def get_splunk(namespace: str):
    """
    Getting Splunk Forwarder name and creating a list.
    :param namespace: Application Namespace
    :return: List of Splunk Forwarder pods.
    """
    try:
        # Get Splunk Pod- Name
        splunk_name_list = []
        cmd = f"""kubectl get pods -n {namespace} | grep splunk | awk -F' ' '{{print $1}}' """
        out, error = execute(cmd)
        if out is not None:
            out = out.splitlines()
        else:
            print("No Splunk Forwarder Available")
            sys.exit(-1)
        for splunk in out:
            if splunk:
                splunk_name_list.append(str(splunk).strip())
        print(f"splunk_list : {splunk_name_list}")
        return splunk_name_list
    except Exception as err:
        print("Exception in get_splunk ::: " + str(err))


def delete_files_from_local_system(retention_days: str, list_of_path: list):
    """
    Deleting old files from the local directories to maintain space.
    :param retention_days: Days of files which want to maintain in the directories.
    :param list_of_path: List of Directories.
    :return: None
    """
    for path in list_of_path:
        cmd = "sudo find path -maxdepth 1 -type f -mtime +retention_days -print -exec rm -rf {} \;".replace("path",
                                                                                                       path).replace(
            "retention_days", retention_days)
        print(f"Command: {str(cmd)}")
        out, error = execute(cmd)
        # print(f"out: {out}, error: {error}")
        if out is not None:
            print(f"KEPT LAST {retention_days} DAYS FILES AND REST DELETED FROM {path}")

        if error is not None:
            print(f"ERROR WHILE DELETING OLDER THAN {retention_days} DAYS FILES FROM {path}   :::: {str(error)}")


def delete_files_from_splunk(retention_days: str, list_of_path: list, splunk_name: str, splunk_container: str):
    """
    Deleting old files from the Splunk Forwarder directories to maintain space.
    :param retention_days: Days of files which want to maintain in the directories.
    :param list_of_path: List of Directories.
    :param splunk_name: Splunk Forwarder Name
    :param splunk_container: Splunk Container Name
    :return: None
    """
    for path in list_of_path:
        cmd = "kubectl exec -it splunk_name -c splunk_container -- sudo find path -maxdepth 1 -type f -mtime +retention_days -print -exec rm -rf {} \;".replace(
            "splunk_name", splunk_name).replace("splunk_container", splunk_container).replace("path", path).replace(
            "retention_days", retention_days)
        out, error = execute(cmd)
        # print(f"out: {out}, error: {error}")
        if out is not None:
            print(
                f"splunk_name: {splunk_name},splunk_container: {splunk_container}, KEPT LAST {retention_days} DAYS FILES AND REST DELETED FROM {path}")
        if error is not None:
            print(
                f"ERROR WHILE DELETING FILES splunk_name: {splunk_name},splunk_container: {splunk_container}, OLDER THAN {retention_days} DAYS FROM {path}   :::: {str(error)}")


def delete_files_from_tpim(retention_days: str, list_of_path: list):
    """
    Deleting old files from the TPIM directories to maintain space.
    :param retention_days: Days of files which want to maintain in the directories.
    :param list_of_path: List of Directories.
    :return: None
    """
    for path in list_of_path:
        cmd = "sudo find path -maxdepth 1 -type f -mtime +retention_days -print -exec rm -rf {} \;".replace("path",
                                                                                                            path).replace(
            "retention_days", retention_days)
        out, error = execute(cmd)
        print(f"out: {out}, error: {error}")
        if out is not None:
            print(f"KEPT LAST {retention_days} DAYS FILES AND REST DELETED FROM {path}")

        if error is not None:
            print(f"ERROR WHILE DELETING OLDER THAN {retention_days} DAYS FILES FROM {path}   :::: {str(error)}")


def main(local_files_retention_days: str, local_paths_list: list, splunk_files_retention_days: str,
         splunk_paths_list: list, splunk_container: str, tpim_files_retention_days: str, tpim_paths_list: list,
         splunk_name_list: list):
    """
    Calling deletion function to delete files.
    :param local_files_retention_days: Days of files which want to maintain in the local directories.
    :param local_paths_list: List of Directories in Local system.
    :param splunk_files_retention_days: Days of files which want to maintain in the Splunk Forwarder directories.
    :param splunk_paths_list: List of Directories on Splunk.
    :param splunk_container: Splunk Forwarder container name
    :param tpim_files_retention_days: Days of files which want to maintain in the TPIM directories.
    :param tpim_paths_list: List of Directories in TPIM.
    :param splunk_name_list: Splunk Forwarder Name list
    :return: None
    """
    try:
        print("FILE DELETION STARTING...")
        # DELETING FILES FROM LOCAL SYSTEM
        delete_files_from_local_system(local_files_retention_days, local_paths_list)

        # DELETING FILES FROM SPLUNK
        for splunk_name in splunk_name_list:
            delete_files_from_splunk(splunk_files_retention_days, splunk_paths_list, splunk_name, splunk_container)

        # DELETING FILES FROM TPIM
        delete_files_from_tpim(tpim_files_retention_days, tpim_paths_list)

        print("FILE DELETION ENDED...")
    except Exception as err:
        print(f"Exception in main ::: {str(err)}")


if __name__ == '__main__':
    pc = ProcessCheck(os.path.join("/", "tmp", os.path.basename(os.path.dirname(os.path.abspath(__file__))) + ".pid"))
    pc.start()
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE_PATH = os.path.join(SCRIPT_DIR, 'config/config.json')
    LOCAL_FILE_RETENTION, LOCAL_PATH_LIST, SPLUNK_FILE_RETENTION, SPLUNK_PATH_LIST, SPLUNK_CONTAINER, TPIM_FILE_RETENTION, TPIM_PATH_LIST = load_config(
        CONFIG_FILE_PATH)
    ADAPTATION_NAMESPACE = get_adaptation_namespace()
    SPLUNK_LIST = get_splunk(ADAPTATION_NAMESPACE)
    main(LOCAL_FILE_RETENTION, LOCAL_PATH_LIST, SPLUNK_FILE_RETENTION, SPLUNK_PATH_LIST, SPLUNK_CONTAINER,
         TPIM_FILE_RETENTION, TPIM_PATH_LIST, SPLUNK_LIST)
    pc.stop()
