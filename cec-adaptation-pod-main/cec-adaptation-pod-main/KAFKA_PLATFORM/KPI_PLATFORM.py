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
from datetime import datetime, timedelta
import time
import sys

from Logger import LoggingHandler
from SubprocessClass import SubprocessClass
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from KAFKA_SENDER.KafkaDataSourceBuilder import KafkaDataSourceBuilder


class KPI_PLATFORM:
    def __init__(self, hostname: str, script_dir: str, output_dir: str, archive_dir: str, log_dir: str):
        self.yesterdayYMD = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
        self.yesterdayYYMMDD = datetime.strftime(datetime.now() - timedelta(1), '%y-%m-%d')
        self._logger = LoggingHandler.get_logger(self.__class__.__name__)
        self.host_name = hostname
        self.script_dir = script_dir
        self.output_dir = output_dir
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

    @staticmethod
    def add_kafka_kpi(kafka_data_source_builder: KafkaDataSourceBuilder, kpi: str, value: str):
        if value:
            value = value
            kpi_result = "UNDEFINED"
        else:
            value = "0"
            kpi_result = "NO-DATA"

        kafka_data_source_builder.add_data_record([kpi.upper(), value, kpi_result])

    def set_message(self, data_source_hostname, data_source_ip, kafka_data_source_builder: KafkaDataSourceBuilder) :
        kafka_data_source_builder.set_message_field("kpi_last_updated_date", self.todayUTC)
        kafka_data_source_builder.set_message_field("kpi_source", f'{data_source_hostname} > KPI_PLATFORM.py > {self.utcTimestamp}')
        kafka_data_source_builder.set_message_field("config_item", data_source_hostname)
        kafka_data_source_builder.set_message_field("kpi_info", f'{data_source_hostname} {data_source_ip}')
        kafka_data_source_builder.set_message_field("src_modified_dt", self.todayUTCMilli)
        kafka_data_source_builder.set_message_field("local_modified_dt", self.localNowMilli)

    def main(self, args_val):
        cmd = ""
        wn_cpu_usage_counter = 0
        wn_mem_usage_counter = 0
        mn_cpu_usage_counter = 0
        mn_mem_usage_counter = 0
        try:
            cem_dict = args_val[0]
            kafka_data_source_builder = args_val[1]
            max_threshold_value = args_val[2]
            self._logger.info(f" {str(args_val)}")

            for key in cem_dict.keys():
                try:
                    if cem_dict[key]["node_type"] == "master_node":
                        if cem_dict[key]["cpu_usage_percentage"] >= max_threshold_value:
                            mn_cpu_usage_counter += 1
                        if cem_dict[key]["mem_usage_percentage"] >= max_threshold_value:
                            mn_mem_usage_counter += 1

                    if cem_dict[key]["node_type"] == "worker_node":
                        if cem_dict[key]["cpu_usage_percentage"] >= max_threshold_value:
                            wn_cpu_usage_counter += 1
                        if cem_dict[key]["mem_usage_percentage"] >= max_threshold_value:
                            wn_mem_usage_counter += 1
                except Exception as err:
                    self._logger.error(f"Exception while reading CEM_DICT ::: {str(err)}")

            cluster_name = str(cem_dict["cluster_name"]).upper()

            # Get hostname of sdp pod
            try:
                if self.host_name is not None:
                    data_source_hostname = self.host_name.strip()
                    cmd = f"""python3 -c "import socket;print(socket.gethostbyname('{str(data_source_hostname)}'))" """
                    host_by_name, error = self.subprocess_obj.execute_cmd(cmd)
                    data_source_ip = host_by_name.strip()
                else:
                    data_source_hostname = "NOT AVAILABLE"
                    data_source_ip = "NOT AVAILABLE"
                self.set_message(str(data_source_hostname).upper(), data_source_ip, kafka_data_source_builder)
                self._logger.info(f"Hostname ::: {str(data_source_hostname)} and {str(data_source_ip)}")
            except Exception as err:
                self._logger.error(f"Exception While getting HOSTNAME ::: {str(err)}")


            # Platform_MASTER_FREE_CPU
            kpi_name = "PLATFORM_MASTER_FREE_CPU_" + cluster_name
            self._logger.info(f'{kpi_name}: {str(mn_cpu_usage_counter)}')
            self.add_kafka_kpi(kafka_data_source_builder, kpi_name, str(mn_cpu_usage_counter))

            # Platform_MASTER_FREE_MEMORY
            kpi_name = "PLATFORM_MASTER_FREE_MEMORY_" + cluster_name
            self._logger.info(f'{kpi_name}: {str(mn_mem_usage_counter)}')
            self.add_kafka_kpi(kafka_data_source_builder, kpi_name, str(mn_mem_usage_counter))

            # Platform_NODE_FREE_CPUk
            kpi_name = "PLATFORM_NODE_FREE_CPU_" + cluster_name
            self._logger.info(f'{kpi_name}: {str(wn_cpu_usage_counter)}')
            self.add_kafka_kpi(kafka_data_source_builder, kpi_name, str(wn_cpu_usage_counter))

            # Platform_NODE_FREE_MEMORY
            kpi_name = "PLATFORM_NODE_FREE_MEMORY_" + cluster_name
            self._logger.info(f'{kpi_name}: {str(wn_mem_usage_counter)}')
            self.add_kafka_kpi(kafka_data_source_builder, kpi_name, str(wn_mem_usage_counter))

            self._logger.info("ALL KPI's Done")
        except Exception as err:
            self._logger.error(f"Exception in main ::: {str(cmd)} ::: {str(err)}")
