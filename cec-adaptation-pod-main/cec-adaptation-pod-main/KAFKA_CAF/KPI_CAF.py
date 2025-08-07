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
#          Created : 2023-03-14
#
#     Version history:
#
# 1.2     2019-07-12 create a 2nd file for Kafka message creation
# 1.2     2019-05-30 CIP/DCIP updates
# 1.1     2019-05-17 path updates
# 1.0     2019-05-07 First version
#
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List
import re
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from KAFKA_SENDER import KafkaDataSourceBuilder
from KPI_Helper import files_newer_that_mins, files_newer_that_mins_latest
from SubprocessClass import SubprocessClass

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import lxml.etree as ET


class KPI_CAF:
    def __init__(self, script_dir, hostname, namespace, execution_period_mins, pm_files_local_dir: str,
                 kafka_data_source_builder: KafkaDataSourceBuilder, is_test_mode: bool):
        self.kafka_data_source_builder = kafka_data_source_builder
        self.is_test_mode = is_test_mode
        self.pm_files_local_dir = pm_files_local_dir
        self.yesterdayYMD = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
        self.yesterdayYYMMDD = datetime.strftime(datetime.now() - timedelta(1), '%y-%m-%d')
        self.host_name = hostname
        self.namespace = namespace
        self.execution_period_mins = execution_period_mins
        self.currentDT = datetime.now()
        self.todayYMD = self.currentDT.strftime("%Y-%m-%d")
        self.todayYYMMDD = self.currentDT.strftime("%y-%m-%d")

        # Creating a object from subprocess class
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

        self.script_dir = script_dir
        self.pm_bulk_port = 22
        self.pm_bulk_name = None
        self.internal_ip = None
        self.pm_csv_file = os.path.join(self.script_dir, "pm_file.csv")
        self.measCollec_xsl = os.path.join(self.script_dir, "measCollec.xsl")

    @staticmethod
    def format_kpi_value(value: float) -> str:
        if type(value) == int or value.is_integer():
            return '{0:.0f}'.format(value)
        else:
            return '{0:.2f}'.format(round(value, 3))

    def aggregate_pm_files_into_csv_file(self, pm_file_paths: List[str]):
        try:
            if os.path.exists(self.pm_csv_file):
                os.remove(self.pm_csv_file)

            logging.info(f"Aggregating {len(pm_file_paths)} PM files into file: {self.pm_csv_file} <- {pm_file_paths}")

            with open(self.pm_csv_file, "a") as fd:
                for pm_file_path in pm_file_paths:
                    dom = ET.parse(pm_file_path)
                    xslt = ET.parse(self.measCollec_xsl)
                    transform = ET.XSLT(xslt)
                    new_dom = transform(dom)
                    print(new_dom, file=fd)
        except Exception as err:
            logging.exception(f"Failed aggregating PM file into csv file ::: {str(err)}")
            return None

    @staticmethod
    def add_kafka_kpi(kafka_data_source_builder: KafkaDataSourceBuilder, kpi: str, value: str, status: bool = True):
        if value and status:
            value = value
            kpi_result = "UNDEFINED"
        else:
            value = "0"
            kpi_result = "NO-DATA"

        kafka_data_source_builder.add_data_record([kpi.upper(), value, kpi_result])

    def get_value_from_csv_file(self, cmd, error_codes_list=[], error_codes_to_consider=[]):
        try:
            kpi_val = 0
            out, error = self.subprocess_obj.execute_cmd(cmd)
            if out is not None:
                for line in out.splitlines():
                    logging.info(f"get_value_from_csv_file Line: {str(line)}")
                    value, stat = self.retrieve_kpi_value(line, error_codes_list=error_codes_list,
                                                          error_codes_to_consider=error_codes_to_consider)
                    kpi_val = float(kpi_val) + float(value)
                    logging.info(f"get_value_from_csv_file value: {str(kpi_val)}")
                return kpi_val, True
            return kpi_val, False
        except Exception as err:
            logging.error(f"Exception in get_value_from_csv_file ::: {str(err)}")

    @staticmethod
    def success_rate(total_req, error_req):
        try:
            return 0.0 if total_req == 0 else ((total_req - error_req) / total_req) * 100
        except Exception as err:
            logging.error(f"Exception in success_rate ::: {str(err)}")

    @staticmethod
    def calculate_rate(total_req, error_req):
        try:
            return 0.0 if total_req == 0 else (error_req / total_req) * 100
        except Exception as err:
            logging.error(f"Exception in success_rate ::: {str(err)}")

    def grep_values_from_file(self, pm_file, counter_name, filters, error_codes_list=[], error_codes_to_consider=[]):
        try:
            stat = False
            locked = False
            request_data = 0
            if filters:
                for req in filters:
                    cmd = f"""grep countername={str(counter_name)} {pm_file} | grep {str(req)} """
                    logging.info(f"cmd ::: {str(cmd)}")
                    val, stat = self.get_value_from_csv_file(cmd, error_codes_list=error_codes_list,
                                                             error_codes_to_consider=error_codes_to_consider)
                    if stat:
                        locked = True
                    request_data = request_data + int(val)
            else:
                cmd = f"""grep countername={str(counter_name)} {pm_file} """
                logging.info(f"cmd ::: {str(cmd)}")
                val, stat = self.get_value_from_csv_file(cmd, error_codes_list=error_codes_list,
                                                         error_codes_to_consider=error_codes_to_consider)
                if stat:
                    locked = True
                request_data = request_data + int(val)
            return request_data, locked
        except Exception as err:
            logging.error(f"Exception in grep_data_from_file ::: {str(err)}")

    @staticmethod
    def retrieve_kpi_value(line, error_codes_list=[], error_codes_to_consider=[]):
        fields = line.split(",")
        if error_codes_list:
            for field in fields:
                if "response-code" in field:
                    res_code_val = field.split("=")
                    if res_code_val[1] in error_codes_list:
                        return 0, True

        if error_codes_to_consider:
            for field in fields:
                if "response-code" in field:
                    res_code_val = field.split("=")
                    if res_code_val[1] not in error_codes_to_consider:
                        return 0, True

        for field in fields:
            if "countervalue" in field:
                key_value = field.split("=")
                kpi = ""
                if len(key_value) == 2:
                    kpi = key_value[1]

                return float(kpi), True
        return 0, False

    @staticmethod
    def retrieve_kpi(line):
        try:
            kpi = ""
            for field in line.split(","):
                if "countervalue" in field:
                    key_value = field.split("=")
                    kpi = ""
                    if len(key_value) == 2:
                        kpi = key_value[1]
                    return kpi, True
            return kpi, False
        except Exception as e:
            logging.error("Exception in write_kpi ::: " + str(e))

    def CAF_CTA_CONNECTION_STATUS(self, ns: str):
        # get all dlbs
        cmd = f"kubectl -n {str(ns)} get pods -l app.kubernetes.io/name=eric-bss-cha-diameter-lb --no-headers | awk -F' ' '{{print $1}}'"
        dlbs, error = self.subprocess_obj.execute_cmd(cmd)

        if error:
            return "Command is having some issue"

        dlbs_list = str(dlbs).split()

        cta_dict = {}
        cta_name = ""
        kpi_count = 0
        for dlb in dlbs_list:
            cmd = f"kubectl -n {str(ns)} exec -it {str(dlb)} -c eric-bss-cha-diameter-lb -- /bin/bash -c 'client'"
            commandResult, error = self.subprocess_obj.get_output_with_child_run(cmd, "peerlist")
            if not commandResult:
                continue
            commandResult = str(commandResult).replace("\t", "")
            peerList = re.findall(r'address:.*|status:.*', commandResult)
            print(peerList)
            # get CTA name from commandResult
            for i, line in enumerate(peerList):
                if line.startswith("address:"):
                    if "CCCTA" in line or "CCTAC" in line:
                        cta_name = re.split(r'[-.]', line.split("://")[-1])
                        cta_name = str(cta_name[0])
                        if cta_name not in cta_dict.keys():
                            cta_dict.update({str(cta_name): {"connected": 0, "disconnected": 0}})
                elif line.startswith("status:"):
                    if "CCCTA" in peerList[i - 1] or "CCTAC" in peerList[i - 1]:
                        if 'status: CONNECTED' in line:
                            conVal = cta_dict[cta_name]["connected"]
                            cta_dict[cta_name]["connected"] = int(conVal) + 1
                        else:
                            disConVal = cta_dict[cta_name]["disconnected"]
                            cta_dict[cta_name]["disconnected"] = int(disConVal) + 1

        print(f"cta_dict: {str(cta_dict)}")
        logging.info(f'cta_dict - {str(cta_dict)}')
        for cta in cta_dict.keys():
            connected = cta_dict[cta]["connected"]
            disconnected = cta_dict[cta]["disconnected"]
            commonRation = (connected + disconnected) / 2

            if disconnected > 0:
                if commonRation > disconnected > 0:
                    kpi_count = 1
                elif disconnected >= commonRation:
                    kpi_count = 2
                    break

        return kpi_count

    def set_message(self, data_source_hostname, data_source_ip, kafka_data_source_builder: KafkaDataSourceBuilder,
                    namespace: str):
        kafka_data_source_builder.set_message_field("kpi_last_updated_date", self.todayUTC)
        kafka_data_source_builder.set_message_field("kpi_source",
                                                    f'{data_source_hostname} > KPI_CAF.py > {self.utcTimestamp}')
        kafka_data_source_builder.set_message_field("config_item", namespace)
        kafka_data_source_builder.set_message_field("kpi_info", f'{data_source_hostname} {data_source_ip}')
        kafka_data_source_builder.set_message_field("src_modified_dt", self.todayUTCMilli)
        kafka_data_source_builder.set_message_field("local_modified_dt", self.localNowMilli)

    def main(self, pm_bulk, namespace, hostname, ip, kafka_data_source_builder, alarm_kpi_config, latency_kpi_config,
             script_kpi_config, success_kpi_config, counter_kpi_config):
        cmd: str = ""

        logging.info(f'PM-BULK NAME - {pm_bulk}')
        self.set_message(str(hostname).upper(), ip, self.kafka_data_source_builder, str(namespace).upper())

        # Taking path for last 3 updated files
        file_paths = files_newer_that_mins_latest(self.pm_files_local_dir, "*.xml", self.execution_period_mins)

        # Reading Files and creating a self.pm_csv_file
        self.aggregate_pm_files_into_csv_file(file_paths)

        # LATENCY KPIs
        cha_pm_counters_group_RequestName_dict = {}
        for key in latency_kpi_config.keys():
            cha_pm_counters_group_RequestName_dict[key] = []

        try:
            cmd = f"""grep measInfoId=cha-pm-counters-group-RequestName {self.pm_csv_file} """
            out, error = self.subprocess_obj.execute_cmd(cmd)
            logging.info(f"{str(out)}")
            if error is None and out is not None:
                for line in out.splitlines():
                    line = line.strip()
                    for key in cha_pm_counters_group_RequestName_dict.keys():
                        if key in line:
                            value, stat = self.retrieve_kpi(line)
                            logging.info(f"KEY: {str(key)} and VALUE: {str(value)}")
                            # print(cha_pm_counters_group_RequestName_dict[key], value)
                            if value not in ["None", "NaN"]:
                                cha_pm_counters_group_RequestName_dict[key].append(value)
        except Exception as err:
            logging.error(f"Exception {cmd} ::: {str(err)}")

        for key, value in cha_pm_counters_group_RequestName_dict.items():
            for k, val in latency_kpi_config.items():
                if key == k:
                    logging.info(f"{str(value)}")
                    logging.info(f"{str(k)}")
                    for counter, thresold in val.items():
                        try:
                            if any(float(x) >= int(thresold) for x in value):
                                self.add_kafka_kpi(kafka_data_source_builder, str(counter).upper(), "1")
                            else:
                                self.add_kafka_kpi(kafka_data_source_builder, str(counter).upper(), "0")
                        except Exception as err:
                            logging.error(f"Exception in LATENCY Counter:: {str(err)}")

        # SUCCESS_KPIs
        update_dns_total_request = 0
        update_dns_error_request = 0
        try:
            total_request = 0
            error_request = 0

            filters = []
            error_codes = []
            config_values = success_kpi_config
            for k, v in config_values.items():
                if "filters" in config_values[k].keys():
                    filters = str(config_values[k]["filters"]).split("|")
                    logging.info(f"Filters ::: {str(filters)}")

                if "code" in config_values[k].keys():
                    error_codes = str(config_values[k]["code"]).split("|")
                    logging.info(f"code ::: {str(error_codes)}")

                # For Total Traffic Request
                total_request, total_status = self.grep_values_from_file(self.pm_csv_file,
                                                                         config_values[k]['kpi_total'], filters)
                logging.info(f"{str(k)}_total: {str(total_request)}")

                # For Error Traffic Request
                error_request, error_status = self.grep_values_from_file(self.pm_csv_file,
                                                                         config_values[k]['kpi_error'], filters,
                                                                         error_codes_list=error_codes)
                logging.info(f"{str(k)}_error: {str(error_request)}")

                # Success Rate
                counter = self.success_rate(total_request, error_request)
                logging.info(f"{str(k)}_success rate: {str(counter)}")

                counter = self.format_kpi_value(float(counter))

                if config_values[k]["kpi"] == "SCAPV2_SESSIONS_SUCCESSFUL_RATE":
                    print(f"total_status: {str(total_status)}   :::: error_status: {str(error_status)}")
                    if total_status or error_status:
                        self.add_kafka_kpi(kafka_data_source_builder, str(config_values[k]['kpi']).upper(),
                                           str(counter))
                else:
                    self.add_kafka_kpi(kafka_data_source_builder, str(config_values[k]['kpi']).upper(), str(counter))
                total_request = 0
                error_request = 0
                filters = []
                error_codes = []
        except Exception as err:
            logging.error(f"Exception in SUCCESS Counter:: {str(err)}")

        # # COUNTER KPIs
        # try:
        #     codes_to_consider_list = []
        #     filters = []
        #     val = 0
        #     max_val = 0
        #     for k, v in counter_kpi_config.items():
        #         if "filters" in counter_kpi_config[k].keys():
        #             filters = str(counter_kpi_config[k]["filters"]).split("|")
        #             logging.info(f"Filters ::: {str(filters)}")
        #
        #         if "codes_to_consider" in counter_kpi_config[k].keys():
        #             codes_to_consider_list = str(counter_kpi_config[k]["codes_to_consider"]).split("|")
        #             logging.info(f"codes_to_consider ::: {str(codes_to_consider_list)}")
        #
        #             for code in codes_to_consider_list:
        #                 # For Total Traffic Request
        #                 total_request, total_status = self.grep_values_from_file(self.pm_csv_file,
        #                                                                          counter_kpi_config[k]['counter'],
        #                                                                          filters,
        #                                                                          error_codes_to_consider=[code])
        #                 if max_val < total_request:
        #                     max_val = total_request
        #                 logging.info(f"{str(k)}_total -> for code {str(code)}: value: {str(total_request)}")
        #             logging.info(f"max_val: {str(max_val)}")
        #             if 0 <= max_val <= 5000:
        #                 val = 0
        #             elif 5000 < max_val <= 10000:
        #                 val = 1
        #             elif max_val > 10000:
        #                 val = 2
        #
        #             self.add_kafka_kpi(kafka_data_source_builder, str(counter_kpi_config[k]['kpi']).upper(), str(val))
        # except Exception as err:
        #     logging.error(f"Exception in Counter Kpis:: {str(err)}")

        # ALARM KPIs
        try:
            list_alarms_cmd = """kubectl -n <namespace> get pods -l app.kubernetes.io/name=eric-fh-alarm-handler -o jsonpath="{.items[0].metadata.name}" | xargs -I{} kubectl -n <namespace> exec -it {} -- ah_alarm_list.sh """.replace(
                "<namespace>", str(namespace))
            alarms, error = self.subprocess_obj.execute_cmd(list_alarms_cmd)
            if alarms is not None:
                alarms = str(alarms).splitlines()
                logging.info(f"Execute command Alarms: {str(alarms)}")
            logging.info(f"{str(len(alarms))}")
            SearchAlarms = alarm_kpi_config

            for i, j in SearchAlarms.items():
                if str(j) == "CAF_CTA_CONNECTION_STATUS":
                    val = self.CAF_CTA_CONNECTION_STATUS(namespace)
                    self.add_kafka_kpi(kafka_data_source_builder, str(j).upper(), str(val))
                    continue

                if str(j) == "CAF_EMM_CDR_TRANSFER":
                    try:
                        partA, partB = str(i).split("|")
                        if partA in str(alarms) and partB in str(alarms):
                            self.add_kafka_kpi(kafka_data_source_builder, str(j).upper(), "1")
                            continue
                        else:
                            self.add_kafka_kpi(kafka_data_source_builder, str(j).upper(), "0")
                            continue
                    except Exception as err1:
                        logging.error(f"Exception in Alarm KPI CAF_EMM_CDR_TRANSFER::: {str(err1)}")
                        self.add_kafka_kpi(kafka_data_source_builder, str(j).upper(), "0")
                        continue

                if str(i) in str(alarms):
                    self.add_kafka_kpi(kafka_data_source_builder, str(j).upper(), "1")
                else:
                    self.add_kafka_kpi(kafka_data_source_builder, str(j).upper(), "0")
        except Exception as err:
            logging.error(f"Exception in Alarm KPIs ::: {str(err)}")

        # CUSTOMER ADAPTATION KPIs
        try:
            customer_adaptation_kpi_dict = script_kpi_config
            for key, value in customer_adaptation_kpi_dict.items():
                cmd = f"""cat {customer_adaptation_kpi_dict[key]["path"]} | grep "ERROR" """
                out, error = self.subprocess_obj.execute_cmd(cmd)
                logging.info(f"{customer_adaptation_kpi_dict[key]['kpi']}::: {str(out)}")
                if out:
                    self.add_kafka_kpi(kafka_data_source_builder, str(customer_adaptation_kpi_dict[key]["kpi"]).upper(),
                                       "1")
                else:
                    self.add_kafka_kpi(kafka_data_source_builder, str(customer_adaptation_kpi_dict[key]["kpi"]).upper(),
                                       "0")
        except Exception as err:
            logging.error(f"Exception Customer Adaptation KPIs ::: {str(err)}")

