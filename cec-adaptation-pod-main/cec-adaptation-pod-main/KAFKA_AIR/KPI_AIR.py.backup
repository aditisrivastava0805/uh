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
#          Created : 2022-04-19
#
#     Version history:
#
# 1.2     2019-07-12 create a 2nd file for Kafka message creation
# 1.2     2019-05-30 CIP/DCIP updates
# 1.1     2019-05-17 path updates
# 1.0     2019-05-07 First version
#


import os
from datetime import datetime, timedelta, date
import time
import sys

from Logger import LoggingHandler
from SubprocessClass import SubprocessClass
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from KAFKA_SENDER.KafkaDataSourceBuilder import KafkaDataSourceBuilder


class KPI_AIR:
    def __init__(self, hostname: str, namespace: str, pod: str, script_dir: str, output_dir: str, archive_dir: str, log_dir: str, pod_container: str):
        self.yesterdayYMD = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
        self.yesterdayYYMMDD = datetime.strftime(datetime.now() - timedelta(1), '%y-%m-%d')
        self._logger = LoggingHandler.get_logger(self.__class__.__name__)
        self.host_name = hostname
        self.namespace = namespace
        self.pod = pod
        self.pod_container = pod_container
        self.script_dir = script_dir
        self.output_dir = output_dir
        if not str(self.output_dir).endswith("/"):
            self.output_dir = self.output_dir + "/"
        self.archive_dir = archive_dir
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

    def update_command(self, sdp, command, command_type=None):
        try:
            self._logger.info(f"update_command() ::: Command - {str(command)}")
            if "{" in command or "}" in command:
                command = command.replace("{", "{{")
                command = command.replace("}", "}}")
            if command_type == "bash":
                command = f"""kubectl exec -it -n {self.namespace} {sdp} -c {self.pod_container} -- bash -c '{command}' """
            else:
                command = f"""kubectl exec -it -n {self.namespace} {sdp} -c {self.pod_container} -- {command}"""
            self._logger.info(f"update_command() ::: Command after conversion - {str(command)}")
            output, error = self.subprocess_obj.execute_cmd(command)
            # output = self.execute_cmd(command)
            return output, error
        except Exception as err:
            self._logger.error("Exception in update_command ::: " + str(err))

    def air_check_master_af(self, air):
        try:
            # Getting 1 hour back datetime from current datetime in given format.
            from_cmd = """date +%Y%m%d" "%H:%M -d "-1 hour" """
            from_output, error = self.update_command(air, from_cmd)
            # from_output = from_output.decode("utf-8")

            # Getting current datetime in given format.
            now_cmd = """date +%Y%m%d" "%H:%M """
            now_output, error = self.update_command(air, now_cmd)
            # now_output = now_output.decode("utf-8")

            # Looking in log file for "DomainNameNotExist" count from current time to 1 hour back.
            dn_cmd = f"""sed -n "/{from_output}/,/{now_output}/p" /var/opt/fds/logs/event.log.0 | grep "DomainNameNotExist" | wc -l """
            dn_output, error = self.update_command(air, dn_cmd)
            # dn_output = dn_output.decode("utf-8")

            # Looking in log file for "AfNotReachable" count from current time to 1 hour back.
            af_cmd = f"""sed -n "/{from_output}/,/{now_output}/p" /var/opt/fds/logs/event.log.0 | grep "AfNotReachable" | wc -l """
            af_output, error = self.update_command(air, af_cmd)
            # af_output = af_output.decode("utf-8")

            # Calculating the sum of "DomainNameNotExist" count and "AfNotReachable" count.
            cmd = f"echo {dn_output} echo {af_output}"
            tdnaf_cmd = """%s | awk '{print $1+$2}' """ % cmd
            tdnaf_output, error = self.update_command(air, tdnaf_cmd)
            # tdnaf_output = tdnaf_output.decode("utf-8")

            # Returning the sum.
            return tdnaf_output.replace("\n", "")
        except Exception as err:
            self._logger.error("Error in air_check_master_af() ::: " + str(err))

    @staticmethod
    def add_kafka_kpi(kafka_data_source_builder: KafkaDataSourceBuilder, kpi: str, value: str):
        if value and value != "None" and value != " ":
            value = value
            kpi_result = "UNDEFINED"
        else:
            value = "0"
            kpi_result = "NO-DATA"

        kafka_data_source_builder.add_data_record([kpi.upper(), value, kpi_result])

    def set_message(self, data_source_hostname, data_source_ip, kafka_data_source_builder: KafkaDataSourceBuilder) :
        kafka_data_source_builder.set_message_field("kpi_last_updated_date", self.todayUTC)
        kafka_data_source_builder.set_message_field("kpi_source", f'{data_source_hostname} > KPI_AIR.py > {self.utcTimestamp}')
        kafka_data_source_builder.set_message_field("config_item", data_source_hostname)
        kafka_data_source_builder.set_message_field("kpi_info", f'{data_source_hostname} {data_source_ip}')
        kafka_data_source_builder.set_message_field("src_modified_dt", self.todayUTCMilli)
        kafka_data_source_builder.set_message_field("local_modified_dt", self.localNowMilli)

    def main(self, args_val):
        cmd = ""
        sdp = ""
        try:
            air = args_val[0]
            kafka_data_source_builder = args_val[1]
            percentage = args_val[2]
            self._logger.info(f" {str(args_val)}")
            # Get hostname of air pod
            try:
                cmd = """env | grep "HOSTNAME=" | awk -F'=' '{print $2}'"""
                hostname, error = self.update_command(air, cmd)
                if hostname is not None:
                    data_source_hostname = hostname.strip()
                    cmd = f"""grep {data_source_hostname} /etc/hosts | awk -F' ' '{{print $1}}' """
                    #cmd = f"""python -c "import socket;print(socket.gethostbyname('{str(data_source_hostname)}'))" """
                    host_by_name, error = self.update_command(air, cmd)
                    data_source_ip = host_by_name.strip()
                else:
                    data_source_hostname = str(air)
                    data_source_ip = "NOT AVAILABLE"
                self.set_message(str(data_source_hostname).upper(), data_source_ip, kafka_data_source_builder)
                self._logger.info(f"Hostname ::: {str(data_source_hostname)} and {str(data_source_ip)}")
            except Exception as err:
                self._logger.error(f"Exception {str(air)} ::: {str(err)}")

            # AIR_CDRS_FILE_SENT_FAILED
            p = """ls -lrt /var/opt/air/datarecords/trackcdr/outputcdr/ /var/opt/air/datarecords/primary/ | grep `date +%Y%m%d` | grep -v .tmp | wc -l """
            count, error = self.update_command(air, p)
            count = str(count).strip() if count else None
            self._logger.info(f'AIR_CDRS_FILE_SENT_FAILED: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "AIR_CDRS_FILE_SENT_FAILED", str(count))

            # # AIR_CHECK_DOMAIN_NAME_NOT_EXIST_COUNT
            # try:
            #     p = """grep "$(date +'%Y%m%d %H:' -d '60 min ago')" /var/opt/fds/logs/event.log.0 |grep -i "DomainNameNotExist" | wc -l """
            #     count, error = self.update_command(air, p)
            #     count = str(count).strip() if count else None
            #     self._logger.info('AIR_CHECK_DOMAIN_NAME_NOT_EXIST_COUNT: ' + str(count))
            #     self.add_kafka_kpi(kafka_data_source_builder, "AIR_CHECK_DOMAIN_NAME_NOT_EXIST_COUNT", str(count))
            # except Exception as err:
            #     self._logger.error(f'AIR_CHECK_DOMAIN_NAME_NOT_EXIST_COUNT: {str(err)}')
            #     self.add_kafka_kpi(kafka_data_source_builder, "AIR_CHECK_DOMAIN_NAME_NOT_EXIST_COUNT", "None")

            # AIR_CHECK_AF_NOT_REACHABLE_COUNT
            try:
                p = """grep "$(date +'%Y%m%d %H:' -d '60 min ago')" /var/opt/fds/logs/event.log.0 |grep -i "AfNotReachable" | wc -l """
                count, error = self.update_command(air, p)
                count = str(count).strip() if count else None
                self._logger.info('AIR_CHECK_AF_NOT_REACHABLE_COUNT: ' + str(count))
                self.add_kafka_kpi(kafka_data_source_builder, "AIR_CHECK_AF_NOT_REACHABLE_COUNT", str(count))
            except Exception as err:
                self._logger.error(f'AIR_CHECK_AF_NOT_REACHABLE_COUNT: {str(err)}')
                self.add_kafka_kpi(kafka_data_source_builder, "AIR_CHECK_AF_NOT_REACHABLE_COUNT", "None")

            # CHECK_PROCESS
            p = """FDSpgrep -l -C | wc -l """
            count, error = self.update_command(air, p)
            count = str(count).strip() if count else None
            self._logger.info(f'CHECK_PROCESS: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "CHECK_PROCESS", str(count))

            # SDP_RPC_ERROR_COUNT
            p = """grep -i "SDP Error"  /var/opt/fds/logs/event.log.0 | fgrep "`date "+%Y%m%d %H"`" | wc -l """
            count, error = self.update_command(air, p)
            count = str(count).strip() if count else None
            self._logger.info(f'SDP_RPC_ERROR_COUNT: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "SDP_RPC_ERROR_COUNT", str(count))

            # SUBSCRIBER_NOT_FOUND_COUNT
            p = """grep "`date -d -15min +'%Y%m%d %H:%M'`" /var/opt/fds/logs/event.log.0 |grep -i "subscriber not found" | wc -l """
            count, error = self.update_command(air, p)
            count = str(count).strip() if count else None
            self._logger.info(f'SUBSCRIBER_NOT_FOUND_COUNT: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "SUBSCRIBER_NOT_FOUND_COUNT", str(count))

            # FDS_CLUSTER_DOWN_COUNT
            p = """FDSClusterMgr processstat | grep On | wc -l """
            count, error = self.update_command(air, p)
            count = str(count).strip() if count else None
            self._logger.info(f'FDS_CLUSTER_DOWN_COUNT: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "FDS_CLUSTER_DOWN_COUNT", str(count))

            # PROCESSES_DOWN_COUNT
            p = """cat /proc/cpuinfo | grep processor | wc -l """
            count, error = self.update_command(air, p)
            count = str(count).strip() if count else None
            self._logger.info(f'PROCESSES_DOWN_COUNT: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "PROCESSES_DOWN_COUNT", str(count))

            # AIR_POD_RUNNING_PERCENTAGE
            self._logger.info(f'AIR_POD_RUNNING_PERCENTAGE: {str(percentage)}')
            self.add_kafka_kpi(kafka_data_source_builder, "AIR_POD_RUNNING_PERCENTAGE", str(percentage))

            self._logger.info("ALL KPI's Done")
        except Exception as err:
            self._logger.error(f"Exception in main ::: {str(cmd)} ::: {str(err)}")