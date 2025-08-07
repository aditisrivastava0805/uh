import logging
import subprocess
from typing import Optional, Tuple, Dict, Any
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.Namespace import get_application_namespace

class CommandExecutor:
    def __init__(self, config_file, is_unhealthy_test_mode: bool):
        """
        Assigning the variables and getting logger.

        :param config_file: Application Configuration File
        :return None
        """

        self.config_file = config_file
        self.namespace = get_application_namespace()
        self.air_pod_healthy_status = None
        self.cluster_ip = None
        self.is_unhealthy_test_mode = is_unhealthy_test_mode

    def run(self, json_data) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Passing command and getting parsed data.
        Comparing based on percentage and returning the Dictionary of Air Pod Data.

        :param json_data: Command File Data
        :return: Returning Air Pod health Data Like - Health_Status, Number_of_Air_Pods, Name Of the Air Pods, Cluster IP
        """
        try:
            logging.info(f"Starting the Process..")

            # Checking the Air Pod Count and getting all the values in dictionary
            air_pod_health_dict = self.execute_command(str(json_data["check_healthy_pod"]["command"]).replace("{namespace}", self.namespace),
                                                       "air_pod_quality_check")

            # taking Air Pod Max Count
            air_pod_max_count = self.execute_command(str(json_data["air_pod_max_count"]["command"]).replace("{namespace}", self.namespace),
                                                     "air_pod_max_count")

            # Calculating percentage
            percentage = self.calculate_percentage(int(air_pod_health_dict['Number_of_Healthy_Air_Pods']), air_pod_max_count)
            logging.info(f"After Calculating...threshold is: {json_data['air_pod_threshold']}% and Calculated: {percentage}%")

            # Checking Envoy Pods Status
            envoy_status = self.get_envoy_pods_status(str(json_data["envoy_pod_check"]["command"]).replace("{namespace}", self.namespace))

            if envoy_status is None:
                logging.info(f"Couldn't check envoy pods status")

            if "Unhealthy" in envoy_status:
                self.air_pod_healthy_status = False
                logging.info(f"Envoy Pod Status is Unhealthy.")

                # Getting cluster IP
                self.cluster_ip = self.execute_command(str(json_data["cluster_ip"]["command"]).replace("{namespace}", self.namespace), "cluster_ip")
                logging.info(f"Name of the cluster AIR IP - {self.cluster_ip}")
                air_pod_health_dict.update({"Health_Status": "unhealthy"})
                air_pod_health_dict.update({"Cluster_IP": self.cluster_ip["Cluster_IP"]})
                air_pod_health_dict.update({"Max_Air_Pod_Count": str(air_pod_max_count)})
                logging.info(f"Air Pod Data ::: {str(air_pod_health_dict)}")
                return air_pod_health_dict, None

            # Comparing health count with Threshold
            if percentage < int(json_data["air_pod_threshold"]) or self.is_unhealthy_test_mode:
                # Setting Flag to False
                self.air_pod_healthy_status = False
                logging.info(f"Air Pod Health is below Threshold...Percentage is: {percentage}")

                # Getting cluster IP
                self.cluster_ip = self.execute_command(str(json_data["cluster_ip"]["command"]).replace("{namespace}", self.namespace), "cluster_ip")
                logging.info(f"Name of the cluster AIR IP - {self.cluster_ip}")
                air_pod_health_dict.update({"Health_Status": "unhealthy"})
                air_pod_health_dict.update({"Cluster_IP": self.cluster_ip["Cluster_IP"]})
                air_pod_health_dict.update({"Max_Air_Pod_Count": str(air_pod_max_count)})
                logging.info(f"Air Pod Data ::: {str(air_pod_health_dict)}")
                return air_pod_health_dict, None
            else:
                logging.info(f"Air Pod Health is above Threshold...Percentage is: {percentage}")

                # Getting cluster IP
                self.cluster_ip = self.execute_command(str(json_data["cluster_ip"]["command"]).replace("{namespace}", self.namespace), "cluster_ip")
                logging.info(f"Name of the cluster AIR IP - {self.cluster_ip}")
                air_pod_health_dict.update({"Health_Status": "healthy"})
                air_pod_health_dict.update({"Cluster_IP": self.cluster_ip["Cluster_IP"]})
                logging.info(f"Air Pod Data ::: {str(air_pod_health_dict)}")
                air_pod_health_dict.update({"Max_Air_Pod_Count": str(air_pod_max_count)})
                return air_pod_health_dict, None
        except Exception as err:
            logging.error(f"Exception in run ::: {str(err)}")
            return None, str(err)

    def execute_command(self, command, command_type=""):
        """
        Using the SUBPROCESS Module to run commands and taking output of that command.
        After that calling the respective function to parse the output data.

        :param command: Command for Execution
        :param command_type: Which type of command - two type : air_pod_quality_check and cluster_ip
        :return: Returning Cluster IP or Air Pod Data
        """
        task = None
        try:
            task = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = task.communicate()
            if command_type == "air_pod_quality_check":
                return self.get_healthy_air_pods(out)
            elif command_type == "cluster_ip":
                return self.get_cluster_ip(out)
            elif command_type == "air_pod_max_count":
                return self.get_max_pod_count(out)
            else:
                return out, err
        except Exception as err:
            logging.error(f"Exception in execute_command() ::: {str(err)}")
        finally:
            task.terminate()  # send sigterm, or ...
            task.kill()

    @staticmethod
    def get_healthy_air_pods(terminal_output):
        """
        Parsing the output data and returning the parsed data as dict.

        :param terminal_output: Output of subprocess command.
        :return: Returning a dictionary with Air Pod related data.
        """
        try:
            counter = 0
            air_health_dict = {"Number_of_Healthy_Air_Pods": 0}

            air_health_details = {"Number_Of_Containers": "",
                                  "Air_Pod_Status": "",
                                  "Number_Of_Restart": "",
                                  "Pod_Up_Time": ""
                                  }
            terminal_output = terminal_output.decode('ascii').splitlines()
            for line in terminal_output:
                name, num_of_containers, pod_status, num_of_restart, pod_up = line.split()
                logging.info(f"get_healthy_air_pods() values::: Name: {name}, num_of_containers: {num_of_containers}, pod_status: {pod_status}, num_of_restart: {num_of_restart}, pod_up: {pod_up}")

                air_health_details["Number_Of_Containers"] = num_of_containers
                air_health_details["Air_Pod_Status"] = pod_status
                air_health_details["Number_Of_Restart"] = num_of_restart
                air_health_details["Pod_Up_Time"] = pod_up

                air_health_dict.update({name: air_health_details})
                counter += 1
                air_health_details = {"Number_Of_Containers": "",
                                      "Air_Pod_Status": "",
                                      "Number_Of_Restart": "",
                                      "Pod_Up_Time": ""
                                      }
            air_health_dict["Number_of_Healthy_Air_Pods"] = int(counter)
            logging.info(f"get_healthy_air_pods() air_health_dict ::: {str(air_health_dict)}")
            return air_health_dict
        except Exception as err:
            logging.error(f"Exception in get_healthy_air_pods ::: {str(err)}")

    @staticmethod
    def get_cluster_ip(terminal_output):
        """
        Parsing the output data and returning the Cluster IP.

        :param terminal_output: Output of subprocess command.
        :return: Returning a dictionary with Cluster IP.
        """
        try:
            cluster_ip_dict = {"Cluster_IP": []}
            terminal_output = terminal_output.decode('ascii').splitlines()
            for line in terminal_output:
                try:
                    cluster_ip = line.split()
                    cluster_ip_dict["Cluster_IP"].append(cluster_ip[0])
                except Exception as err:
                    logging.error(err)
            return cluster_ip_dict
        except Exception as err:
            logging.info(f"Exception in get_fqdn_name() ... {str(err)}")

    @staticmethod
    def calculate_percentage(ava_value, max_val):
        """
        Calculating the percentage based on Max_Air_Pod_Data and Active Air Pod Count.

        :param ava_value: Active Air Pod Count.
        :param max_val: Max Air Pod Count.
        :return: Returning the Percentage.
        """
        if float(max_val) > 0:
            percentage = 100 * float(ava_value) / float(max_val)
            return round(percentage)
        return 0.0

    @staticmethod
    def get_max_pod_count(terminal_output):
        """
        Calculating the number of AirPods.

        :param terminal_output:
        :return: int: Number of AirPods.
        """
        counter = 0
        terminal_output = terminal_output.decode('ascii').splitlines()
        for _ in terminal_output:
            counter += 1
        return counter

    def get_envoy_pods_status(self, cmd: str):
        """
        Checking the status on envoj pods

        cmd:
        """
        out, err = self.execute_command(cmd)
        logging.error(f"get_envoy_pods_status()::::: OUT: {str(out)}, ERROR: {str(err)}")
        if str(out) is not None:
            return str(out).strip()

        return None
