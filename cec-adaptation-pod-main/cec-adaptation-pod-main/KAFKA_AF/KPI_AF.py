#!/usr/bin/python
# Copyright (c) 2019 Ericsson Inc
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
#          Created : 2023-03-23
#
#     Version history:
#
# 1.3     2023-03-23 KAFKA support with python3 and GEO RED separate script
# 1.2     2019-07-12 create a 2nd file for Kafka message creation
# 1.2     2019-05-30 CIP/DCIP updates
# 1.1     2019-05-17 path updates
# 1.0     2019-05-07 First version
#


import os
import traceback
from datetime import datetime, timedelta, date
import time
import sys

from Logger import LoggingHandler
from SubprocessClass import SubprocessClass

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from KAFKA_SENDER.KafkaDataSourceBuilder import KafkaDataSourceBuilder


class KPI_AF:
    def __init__(self, hostname: str, namespace: str, pod: str, script_dir: str, output_dir: str, archive_dir: str,
                 log_dir: str, pod_container: str, af_corenet_ip: str):
        self.yesterdayYMD = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
        self.yesterdayYYMMDD = datetime.strftime(datetime.now() - timedelta(1), '%y-%m-%d')
        self._logger = LoggingHandler.get_logger(self.__class__.__name__)
        self.host_name = hostname
        self.namespace = namespace
        self.pod = pod
        self.pod_container = pod_container
        self.script_dir = script_dir
        self.output_dir = output_dir
        self.archive_dir = archive_dir
        self.af_corenet_ip = af_corenet_ip
        self.log_dir = log_dir
        self.currentDT = datetime.now()
        self.todayYMD = self.currentDT.strftime("%Y-%m-%d")
        self.todayYYMMDD = self.currentDT.strftime("%y-%m-%d")
        self.today_timestamp = self.currentDT.strftime("%Y%m%d%H%M%S")

        # Creating an object from subprocess class
        self.subprocess_obj = SubprocessClass()

        # epoch GMT time
        self.todayUTCMilli = int(time.mktime(self.currentDT.timetuple()) * 1000)

        if time.localtime().tm_isdst:
            self.timeDiff = time.timezone - 3600
        else:
            self.timeDiff = time.timezone

        self.localNowMilli = self.todayUTCMilli - self.timeDiff * 1000

        self.utcNow = datetime.utcnow()
        self.utcTimestamp = self.utcNow.strftime("%Y-%m-%d %H:%M:%S")
        self.todayUTC = self.utcNow.strftime("%Y-%m-%d")
        self.kafkaText = f"{self.todayUTC},{self.utcTimestamp},{self.todayUTCMilli},{self.localNowMilli}"

    def update_command(self, af, command, container, command_type=None, timeout=None):
        try:
            self._logger.info(f"update_command() ::: Command - {str(command)}")
            if "{" in command or "}" in command:
                command = command.replace("{", "{{")
                command = command.replace("}", "}}")
            if command_type == "bash":
                command = f"""kubectl exec -it -n {self.namespace} {af} -c {container} -- bash -c '{command}' """
            else:
                command = f"""kubectl exec -it -n {self.namespace} {af} -c {container} -- {command}"""
            self._logger.info(f"update_command() ::: Command after conversion - {str(command)}")

            if timeout:
                output, error = self.subprocess_obj.execute_cmd_with_timeout(command, timeout)
            else:
                output, error = self.subprocess_obj.execute_cmd(command)
            # output = self.execute_cmd(command)
            return output, error
        except Exception as err:
            self._logger.error("Exception in update_command ::: " + str(err))

    @staticmethod
    def add_kafka_kpi(kafka_data_source_builder: KafkaDataSourceBuilder, kpi: str, value: str, result_status: str):
        if result_status == "NO":
            kpi_result = "NO-DATA"
        else:
            kpi_result = "UNDEFINED"

        kafka_data_source_builder.add_data_record([kpi.upper(), value, kpi_result])

    def set_message(self, data_source_hostname, data_source_ip, kafka_data_source_builder: KafkaDataSourceBuilder):
        kafka_data_source_builder.set_message_field("kpi_last_updated_date", self.todayUTC)
        kafka_data_source_builder.set_message_field("kpi_source",
                                                    f'{data_source_hostname} > KPI_SDP.py > {self.utcTimestamp}')
        kafka_data_source_builder.set_message_field("config_item", data_source_hostname)
        kafka_data_source_builder.set_message_field("kpi_info", f'{data_source_hostname} {data_source_ip}')
        kafka_data_source_builder.set_message_field("src_modified_dt", self.todayUTCMilli)
        kafka_data_source_builder.set_message_field("local_modified_dt", self.localNowMilli)

    def get_main_af(self, main_commands, pod_name, release_name_list):
        release_name = None
        for release_name in release_name_list:
            release_name = str(release_name).split("-")[0]
            if release_name in pod_name:
                break

        if not release_name:
            return False

        out, err = self.subprocess_obj.execute_cmd(
            str(main_commands["af_main_from_helm"]).replace("{releaseName}", release_name))
        if err:
            self._logger.error(
                f'Failed fetching pods, cmd: {main_commands["af_main_from_helm"].replace("{releaseName}", release_name)}')
            return False

        if not out:
            self._logger.error(f'No pods are found pod pattern')
            return False

        enabled, status = str(out).split()

        if 'no' in status:
            return True

        return False

    def get_passive_af(self, main_commands, pod_name, release_name_list):
        self._logger.info(f"{pod_name}, release_name_list: {str(release_name_list)}")
        release_name = None
        for release_name in release_name_list:
            # release_name = str(release_name).split("-")[0]
            if str(release_name).split("-")[0] in pod_name:
                break

        if not release_name:
            return False

        # Running command to get afType
        out, err = self.subprocess_obj.execute_cmd(
            str(main_commands["af_passive_type"]).replace("{releaseName}", release_name).replace("{namespace}", self.namespace))
        if err:
            self._logger.error(
                f'Failed fetching pods, cmd: {str(main_commands["af_passive_type"]).replace("{releaseName}", release_name).replace("{namespace}", self.namespace)}')
            return False

        if not out:
            self._logger.error(f'No pods are found pod pattern')
            return False
        self._logger.info(f"{pod_name}, out: {str(out)}")
        # check_main, status = str(out).split()
        if 'main' not in str(out):
            return False

        # Running command to get passive enabled
        out, err = self.subprocess_obj.execute_cmd(
            str(main_commands["af_passive_enabled"]).replace("{releaseName}", release_name).replace("{namespace}", self.namespace))
        if err:
            self._logger.error(
                f'Failed fetching pods, cmd: {main_commands["af_passive_enabled"].replace("{releaseName}", release_name).replace("{namespace}", self.namespace)}')
            return False

        if not out:
            self._logger.error(f'No pods are found pod pattern')
            return False

        # enabled, status = str(out).split()
        self._logger.info(f"{pod_name}, out: {str(out)}")
        if 'yes' in str(out):
            return True

        return False

    def main(self, args_val):
        cmd = ""
        af = ""
        container = ""
        main_af = False
        passive_af = False
        try:
            af = args_val[0]
            thread_counter = args_val[1]
            kafka_data_source_builder = args_val[2]
            main_af_commands = args_val[3]
            release_pod_list = args_val[4]

            if "assistant" not in af:
                # main_af = self.get_main_af(main_af_commands, af, release_pod_list)
                # self._logger.info(f"THIS IS MAIN AF ::::: {str(af)}")

                status = self.get_passive_af(main_af_commands, af, release_pod_list)
                self._logger.info(f"THIS IS PASSIVE AF ::::: {str(af)}")

                if status:
                    passive_af = True
                else:
                    main_af = True

            self._logger.info(f"{af}, passive_af: {str(passive_af)}, main_af: {str(main_af)}")
            if "-main" in af:
                container = "main"
            elif "-assistant" in af:
                container = "assistant"

            self._logger.info(f" {str(args_val)} and {str(thread_counter)}")
            # Get hostname of af pod
            try:
                cmd = """env | grep "HOSTNAME=" | awk -F'=' '{print $2}'"""
                hostname, error = self.update_command(af, cmd, container)
                if hostname:
                    data_source_hostname = hostname.strip()
                    cmd = f"""grep {data_source_hostname} /etc/hosts | awk -F' ' '{{print $1}}' """
                    host_by_name, error = self.update_command(af, cmd, container)
                    data_source_ip = host_by_name.strip()
                else:
                    data_source_hostname = str(af)
                    data_source_ip = "NOT AVAILABLE"
                self.set_message(str(data_source_hostname).upper(), data_source_ip, kafka_data_source_builder)
                self._logger.info(f"Hostname ::: {str(data_source_hostname)} and {str(data_source_ip)}")
            except Exception as err:
                self._logger.error(f"Exception {str(af)} ::: {str(err)}")

            # 1. AF_ROUTER_ERRORS
            count = 0
            cmd = """ls -l /var/opt/af/named/ | grep -i "AFRouter-.*" | tail -1 | awk '{print $9}' """
            filename, error = self.update_command(af, cmd, container)

            if filename:
                filename = str(filename).strip()
                self._logger.info(f"AF_ROUTER_ERRORS: {str(filename)}")

                cmd = f"""awk 'NR == 1 {{for (i=1; i<=NF; i++) {{ col[$i] = i }}}} NR > 1 {{print $col["UDP:Query:Timeout"], $col["UDP:Iquery:Timeout"], $col["UDP:Status:Timeout"], $col["UDP:Notify:Timeout"], $col["UDP:Update:Timeout"], $col["TCP:Query:Timeout"], $col["TCP:Iquery:Timeout"], $col["TCP:Status:Timeout"], $col["TCP:Notify:Timeout"], $col["TCP:Update:Timeout"]}}' /var/opt/af/named/{str(filename)} | tail -15 """
                self._logger.info(f"AF_ROUTER_ERRORS: command - {str(cmd)}")
                data, error = self.update_command(af, cmd, container)
                self._logger.info(f"AF_ROUTER_ERRORS: data - {str(data)}")
                if data:
                    for line in str(data).splitlines():
                        self._logger.info(f"AF_ROUTER_ERRORS: line - {str(line)}")
                        line = str(line).strip()
                        self._logger.info(f"AF_ROUTER_ERRORS: line after strip - {str(line)}")
                        uQuery, uIquery, uStatus, uNotify, uUpdate, tQuery, tIquery, tStatus, tNotify, tUpdate = str(
                            line).split()
                        count += int(uQuery) + int(uIquery) + int(uNotify) + int(uUpdate) + int(uStatus) + int(
                            tNotify) + int(tUpdate) + int(tIquery) + int(tQuery) + int(tStatus)
                        self._logger.info(f"AF_ROUTER_ERRORS: count - {str(count)}")
                    self._logger.info(f'AF_ROUTER_ERRORS: {str(count)}')
                    self.add_kafka_kpi(kafka_data_source_builder, "AF_ROUTER_ERRORS", str(count), "OK")
                else:
                    self._logger.info(f'AF_ROUTER_ERRORS: {str(count)}')
                    self.add_kafka_kpi(kafka_data_source_builder, "AF_ROUTER_ERRORS", str(count), "NO")
            else:
                self._logger.info('AF_ROUTER_ERRORS: No File Found!')
                self.add_kafka_kpi(kafka_data_source_builder, "AF_ROUTER_ERRORS", "0", "NO")

            # 2. AF_ZONE_SYNC_ERRORS
            # cmd = """/opt/af/bin/checkzones.pl | awk -F' ' '{print $2}' """
            cmd = """opt/af/bin/checkzones.pl 2>/dev/null | awk {'print $2'} | sed "s/^ \+//g" | egrep -i 'main|no' | wc -l """
            col_val, error = self.update_command(af, cmd, container)
            col_val = str(col_val).strip() if col_val else None
            # valid_val = ["OK", "Status", ""]
            # val = tuple(1 for x in str(col_val).splitlines() if x not in valid_val)
            self._logger.info(f'AF_ZONE_SYNC_ERRORS: {str(col_val)}')
            if col_val is not None:
                self.add_kafka_kpi(kafka_data_source_builder, "AF_ZONE_SYNC_ERRORS", str(col_val), "OK")
            else:
                self.add_kafka_kpi(kafka_data_source_builder, "AF_ZONE_SYNC_ERRORS", str(col_val), "NO")

            # 3. AF_PROCESS_HC
            count = 1
            cmd = """/opt/af/bin/accountfinder status """
            output, error = self.update_command(af, cmd, container, timeout=5)
            if "Account Finder is running" in output:
                count = 0
            self._logger.info(f'AF_PROCESS_HC: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "AF_PROCESS_HC", str(count), "OK")

            # 4. AF_MAIN_CPM_SYNC_ERROR_STATUS
            if main_af or passive_af:
                cmd = """find /var/opt/af/errorRecords/SYNC_SERVER_01/ -type f -name 'SyncErrorData_*' ! -name '*.tmp' -mmin -15 | wc -l """
                count, error = self.update_command(af, cmd, container)
                count = str(count).strip() if count else "0"
                self._logger.info(f'AF_MAIN_CPM_SYNC_ERROR_STATUS: {str(count)}')
                self.add_kafka_kpi(kafka_data_source_builder, "AF_MAIN_CPM_SYNC_ERROR_STATUS", str(count), "OK")

            # 5. POLARIS_CPM_REACHABILITY
            if main_af or passive_af:
                cmd = """cat /var/log/warn | grep "No answer received from 10.201.186.253" | grep "$(date '+%Y-%m-%dT%H:%M' -d '15 minutes ago')" | wc -l """
                count, error = self.update_command(af, cmd, container)
                count = str(count).strip() if count else "0"
                self._logger.info(f'POLARIS_CPM_REACHABILITY: {str(count)}')
                self.add_kafka_kpi(kafka_data_source_builder, "POLARIS_CPM_REACHABILITY", str(count), "OK")

            # 6. RIVERSIDE_CPM_REACHABILITY
            if main_af or passive_af:
                cmd = """cat /var/log/warn | grep "No answer received from 10.163.80.253" | grep "$(date '+%Y-%m-%dT%H:%M' -d '15 minutes ago')" | wc -l """
                count, error = self.update_command(af, cmd, container)
                count = str(count).strip() if count else "0"
                self._logger.info(f'RIVERSIDE_CPM_REACHABILITY: {str(count)}')
                self.add_kafka_kpi(kafka_data_source_builder, "RIVERSIDE_CPM_REACHABILITY", str(count), "OK")

            # 7. TITAN_CPM_REACHABILITY
            if main_af or passive_af:
                cmd = """cat /var/log/warn | grep "No answer received from 10.201.38.253" | grep "$(date '+%Y-%m-%dT%H:%M' -d '15 minutes ago')" | wc -l """
                count, error = self.update_command(af, cmd, container)
                count = str(count).strip() if count else "0"
                self._logger.info(f'TITAN_CPM_REACHABILITY: {str(count)}')
                self.add_kafka_kpi(kafka_data_source_builder, "TITAN_CPM_REACHABILITY", str(count), "OK")

            # 8. AF_POD_RUNNING_STATUS
            cmd = f"""kubectl get pod -n {self.namespace}| grep caf | egrep -v "1/1|Running" | wc -l """
            count, error = self.subprocess_obj.execute_cmd(cmd)
            self._logger.info(f'AF_POD_RUNNING_STATUS: {str(count)}')
            if error is None:
                if str(count).strip() == "0":
                    self.add_kafka_kpi(kafka_data_source_builder, "AF_POD_RUNNING_STATUS", "100", "OK")
                else:
                    self.add_kafka_kpi(kafka_data_source_builder, "AF_POD_RUNNING_STATUS", "0", "OK")
            else:
                self._logger.info(f'AF_POD_RUNNING_STATUS ERROR: {str(error)}')
                self.add_kafka_kpi(kafka_data_source_builder, "AF_POD_RUNNING_STATUS", "1", "NO")

            # 9. THREAD_COUNT
            if main_af or passive_af:
                cmd = """ps -ef | grep AFRouter"""
                count, error = self.update_command(af, cmd, container, "bash")
                if error is None:
                    if "/opt/af/bin/AFRouter -f" in count:
                        self.add_kafka_kpi(kafka_data_source_builder, "THREAD_COUNT", "1", "OK")
                    elif "/opt/af/bin/AFRouter -t 64 -f" in count:
                        self.add_kafka_kpi(kafka_data_source_builder, "THREAD_COUNT", "0", "OK")
                else:
                    self.add_kafka_kpi(kafka_data_source_builder, "THREAD_COUNT", "0", "NO")
                self._logger.info(f'THREAD_COUNT: {str(count)}')

            # 10. MAIN_AF_HEALTH_CHECK_URL
            kpi_val = 0
            result_status = "NO"
            if main_af or passive_af:
                cmd = f"""curl http://{self.af_corenet_ip}:8082/af_pod/status --connect-timeout 30 """
                response, error = self.subprocess_obj.execute_cmd(cmd)
                self._logger.info(f"MAIN_AF_HEALTH_CHECK_URL: POD: {str(af)} Response - {str(response)}, Error - {str(error)}")
                if error is None:
                    import json
                    response = json.loads(str(response))
                    for roles in response["data"]["helm_data"]:
                        for key, role in roles["Role"].items():
                            if key not in af:
                                continue

                            if role == "error":
                                kpi_val = 1
                                result_status = "OK"

                            if passive_af and role == "standby":
                                kpi_val = 0
                                result_status = "OK"

                            if main_af and role == "active":
                                kpi_val = 0
                                result_status = "OK"

                            if main_af and role == "standby":
                                kpi_val = 2
                                result_status = "OK"

                if error is not None:
                    if "Connection timeout" in error:
                        kpi_val = 3
                        result_status = "OK"
                    else:
                        kpi_val = 0
                        result_status = "NO"
                self._logger.info(f'MAIN_AF_HEALTH_CHECK_URL: {str(kpi_val)}')
                self.add_kafka_kpi(kafka_data_source_builder, "MAIN_AF_HEALTH_CHECK_URL", str(kpi_val), result_status)
            self._logger.info("ALL KPI's Done")
        except Exception as err:
            self._logger.error(f"Exception in main ::: {str(cmd)} ::: {str(err)} ::: {traceback.format_exc()}")
