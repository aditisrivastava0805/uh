import subprocess
import logging
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.Namespace import get_application_namespace


class CommandExecutor:
    def __init__(self, command_json, configuration, is_unhealthy_test_mode: bool):
        """
        Assigning the variables and getting logger.

        :param config_file: Application Configuration File
        :return None
        """
        # Getting the logger
        self.task = None
        self.counter = 0
        self.air_pod_healthy_status = None
        self.cluster_ip = None
        self.command_json = command_json
        self.data_dict = {}
        self.configuration = configuration
        self.namespace = get_application_namespace()
        self.is_unhealthy_test_mode = is_unhealthy_test_mode

    def run(self):
        """
        Passing command and getting parsed data.
        Comparing based on percentage and returning the Dictionary of Air Pod Data.

        :param json_data: Command File Data
        :return: Returning Air Pod health Data Like - Health_Status, Number_of_Air_Pods, Name Of the Air Pods, Cluster IP
        """

        try:
            logging.info(f"Starting the Process..")

            self.data_dict['pod_status'] = self.get_pod_struct(self.command_json)
            self.data_dict['helm_data'] = self.get_helm_struct(self.command_json)

            logging.info(f"self.data_list :::: {str(self.data_dict)}")

        except Exception as err:
            logging.exception(f"Exception in run ::: {str(err)}")
            return "Error", str(err)

    def get_helm_struct(self, json_data):
        helm_role_struct = []

        release_names_command: str = str(json_data["get_release_names"]["command"]).replace("{namespace}",
                                                                                            self.namespace)

        out, err = self.execute_command(command=release_names_command,
                                        request_timeout=self.configuration['request_timeout_seconds'])

        if not out:
            helm_role_struct.append(err)
            return helm_role_struct

        for release_name_row in out.splitlines():
            release_name = release_name_row.split()[0]

            logging.info(f'Release name: {release_name}')
            af_pod_health_dict = self.get_healthy_af_pods(release_name_row)

            # Checking the Air Pod Count and getting all the values in dictionary
            command: str = str(json_data["af_main"]["command"]).replace("{releaseName}", release_name).replace(
                "{namespace}", self.namespace)
            af_pod_main, _ = self.execute_command(command=command, command_type="af_pod_main",
                                                  release_name=release_name)
            af_pod_health_dict["Role"] = af_pod_main

            helm_role_struct.append(af_pod_health_dict)

        return helm_role_struct

    def get_pod_struct(self, json_data):
        pod_status = []
        command: str = str(json_data["pod_status"]["command"]).replace("{namespace}", self.namespace)

        out, err = self.execute_command(command=command, request_timeout=self.configuration['request_timeout_seconds'])

        if not out:
            pod_status.append(err)
            return pod_status

        for pods in out.splitlines():
            pod_components = pods.split()
            pod = {'name': pod_components[0], 'ready': pod_components[1], 'status': pod_components[2]}

            pod_status.append(pod)

        return pod_status

    def execute_command(self, command, release_name=None, command_type=None, request_timeout=None):
        """
        Using the SUBPROCESS Module to run commands and taking output of that command.
        After that calling the respective function to parse the output data.

        :param command: Command for Execution
        :param command_type: Which type of command - two type : air_pod_quality_check and cluster_ip
        :param release_name: release name.
        :return: Returning Cluster IP or Air Pod Data
        """
        try:
            self.task = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = self.task.communicate(timeout=request_timeout)

            out = out.decode("utf-8")

            if err:
                err = err.decode("utf-8")
            else:
                err = ''

            if not command_type:
                return out, err

            if command_type == "af_pod_quality_check":
                return self.get_healthy_af_pods(out), "Success"
            elif command_type == "af_pod_main":
                return self.get_af_main_active(out, release_name), "Success"

        except TimeoutError:
            logging.exception(f"Timeout error")
            return None, "TimeoutException triggered while hitting the command."

        except Exception as err:
            logging.exception(f"Exception in execute_command  {str(err)}")
            return None, f"Exception in execute_command  {str(err)}"

    def get_healthy_af_pods(self, terminal_output):
        """
        Parsing the output data and returning the parsed data as dict.

        :param terminal_output: Output of subprocess command.
        :return: Returning a dictionary with Air Pod related data.
        """
        try:
            self.counter = 0
            af_health_dict = {"Role": ""}

            af_health_details = {"App_Namespace": "",
                                 "Revision": "",
                                 "Deployment_Date": "",
                                 "Status": "",
                                 "Chart": "",
                                 "App_Version": ""
                                 }

            name, app_namespace, revision, date, time, offset, timezone, status, chart, app_version = terminal_output.split()
            logging.info(
                f"get_healthy_af_pods() values::: Name: {name}, app_namespace: {app_namespace}, revision: {revision}, date: {date} {time} {offset} {timezone}, status: {status}, chart: {chart}, app_version: {app_version}")

            af_health_details["App_Namespace"] = app_namespace
            af_health_details["Revision"] = revision
            af_health_details["Deployment_Date"] = date + " " + time + " " + offset + " " + timezone
            af_health_details["Status"] = status
            af_health_details["Chart"] = chart
            af_health_details["App_Version"] = app_version

            af_health_dict.update({name: af_health_details})

            logging.info(f"get_healthy_af_pods() af_health_dict ::: {str(af_health_dict)}")
            return af_health_dict
        except Exception as err:
            logging.exception(f"Exception in get_healthy_af_pods ::: {str(err)}")

    def dns_check(self, pod_name):
        try:
            cmd = f"""kubectl exec -it {pod_name} -n {self.namespace} -- {str(self.command_json["dns_port_check"]["command"])} """
            output, error = self.execute_command(cmd)

            if error:
                return False

            if "53" in output:
                return True

            return False
        except Exception as err:
            logging.exception(f"Exception in dns_check ::: {str(err)}")

    def nslookup_check(self, pod_name: str):
        try:
            cmd = str(self.command_json["nslookup"]["command"]).replace("{pod_name}", pod_name).replace("{namespace}", self.namespace)
            output, error = self.execute_command(cmd)

            if output is not None:
                if str(self.command_json["nslookup"]["pass_case"]) in output:
                    return True

            return False
        except Exception as err:
            logging.exception(f"Exception in nslookup_check ::: {str(err)}")

    def read_only_check(self, pod_name: str):
        try:
            cmd = f"""kubectl exec -it {pod_name} -n {self.namespace} -- mount 2>/dev/null | tail -n +2 | grep scini | grep -i 'ro' """
            output, error = self.execute_command(cmd)
            logging.info(f"read_only_check: output: {output}, error: {error}")

            if output == '' or output is None:
                return True

            return False

        except Exception as err:
            logging.exception(f"Exception in read_only_check ::: {str(err)}")

    def get_af_main_active(self, terminal_output, release_name: str):
        """
        Parsing the output data and returning the parsed data as dict.

        :param release_name:
        :param terminal_output: Output of subprocess command.
        :return: Returning a dictionary with Air Pod related data.
        """

        try:
            af_main_status = {}
            enabled, status = terminal_output.split()
            logging.info(f"get_af_main_active() values::: Status: {status}")

            matched = False
            pod = None
            for pod in self.data_dict['pod_status']:
                release_ini = str(release_name).split("-")[0]
                if release_ini in pod["name"]:
                    matched = True
                    break

            if self.is_unhealthy_test_mode:
                af_main_status[release_name] = "error"
                return af_main_status

            if not matched:
                af_main_status[release_name] = "error"
                return af_main_status

            if not self.nslookup_check(pod["name"]):
                af_main_status[release_name] = "error"
                return af_main_status

            if not self.dns_check(pod["name"]):
                af_main_status[release_name] = "error"
                return af_main_status

            if not self.read_only_check(pod["name"]):
                af_main_status[release_name] = "error"
                logging.info(f"get_af_main_active(): read only check False: {af_main_status}")
                return af_main_status

            if 'no' in status:
                if pod['ready'] != "1/1" or pod['status'] != "Running":
                    af_main_status[release_name] = "error"
                    return af_main_status
                af_main_status[release_name] = 'active'
                return af_main_status
            elif 'yes' in status:
                if pod['ready'] != "1/1" or pod['status'] != "Running":
                    af_main_status[release_name] = "error"
                    return af_main_status
                af_main_status[release_name] = 'standby'
                return af_main_status
            else:
                af_main_status[release_name] = 'error'
                return af_main_status

        except Exception as err:
            logging.exception(f"Exception in get_af_main_active ::: {str(err)}")

    def get_data(self):
        return self.data_dict
