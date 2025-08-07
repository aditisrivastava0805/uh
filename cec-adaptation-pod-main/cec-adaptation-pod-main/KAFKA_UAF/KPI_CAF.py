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
            return '{0:.3f}'.format(round(value, 3))

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

    @staticmethod
    def read_json_file(file_path):
        with open(file_path, 'r') as f:
            j = json.load(f)
        return j

    @staticmethod
    def write_to_json_file(file_path, data):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def check_pod_restart_data(self, data):
        file_path = os.path.join(self.script_dir, "restart_values.json")
        # Read Json
        if not os.path.exists(file_path):
            old_data = self.read_json_file(file_path)
        else:
            old_data = {}
        merged_dict = {}
        # Update Latest data in old
        for key, val in old_data.items():
            merged_dict.update({key: val})

        for key, val in data.items():
            if key in merged_dict.keys():
                merged_dict[key] = val
            else:
                merged_dict.update({key: val})

        # Write to json
        self.write_to_json_file(file_path, merged_dict)

        return old_data

    def get_max_from_dict(self, val_dict):
        max_cpu_percentage = 0
        max_memory_percentage = 0

        for k, v in val_dict.items():
            cpu_pct = (v["occupied_cpu"] / v["max_cpu"]) * 100 if v["max_cpu"] else 0
            mem_pct = (v["occupied_memory"] / v["max_memory"]) * 100 if v["max_memory"] else 0

            max_cpu_percentage = max(max_cpu_percentage, cpu_pct)
            max_memory_percentage = max(max_memory_percentage, mem_pct)

        logging.info(f"Max CPU Usage %: {round(max_cpu_percentage, 2)}" )
        logging.info(f"Max Memory Usage %: {round(max_memory_percentage, 2)}")

        return round(max_cpu_percentage, 2), round(max_memory_percentage, 2)

    def set_message(self, data_source_hostname, data_source_ip, kafka_data_source_builder: KafkaDataSourceBuilder,
                    namespace: str):
        kafka_data_source_builder.set_message_field("kpi_last_updated_date", self.todayUTC)
        kafka_data_source_builder.set_message_field("kpi_source",
                                                    f'{data_source_hostname} > KPI_UAF.py > {self.utcTimestamp}')
        kafka_data_source_builder.set_message_field("config_item", namespace)
        kafka_data_source_builder.set_message_field("kpi_info", f'{data_source_hostname} {data_source_ip}')
        kafka_data_source_builder.set_message_field("src_modified_dt", self.todayUTCMilli)
        kafka_data_source_builder.set_message_field("local_modified_dt", self.localNowMilli)

    def main(self, pm_bulk, namespace, hostname, ip, kafka_data_source_builder, success_kpi_config):
        cmd: str = ""

        logging.info(f'PM-BULK NAME - {pm_bulk}')
        self.set_message(str(hostname).upper(), ip, self.kafka_data_source_builder, str(namespace).upper())

        # Taking path for last 3 updated files
        file_paths = files_newer_that_mins_latest(self.pm_files_local_dir, "*.xml", self.execution_period_mins)

        # Reading Files and creating a self.pm_csv_file
        self.aggregate_pm_files_into_csv_file(file_paths)

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

                if config_values[k]["kpi"] == "CPM_UPDATE_DNS_REQUEST_SUCCESSFUL_RATE":
                    update_dns_success_rate = counter
                    update_dns_total_request = total_request
                    update_dns_error_request = error_request

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

        # CPM Availability
        try:
            # Get CPM IP
            cmd = f"kubectl get svc -n {self.namespace} | grep -i eric-bss-cpm-app-dnstcp | awk '{{ print $4}}'"
            cpm_ip, error = self.subprocess_obj.execute_cmd(cmd)
            logging.info(f"Get CPM IP ::: cmd: {str(cmd)}, output: {str(cpm_ip)}, error: {str(error)}")
            if cpm_ip is not None:
                cmd = f"""nslookup 9999999999.9.msisdn.sub.cs {str(cpm_ip).strip()} 2>&1 | egrep -q "connection timed out; no servers could be reached|SERVFAIL" && echo "IP not reachable (DNS timeout) or | SERVFAIL" || echo "Lookup successful" """
                msg, error = self.subprocess_obj.execute_cmd(cmd)
                logging.info(
                    f"nslookup ::: cmd: {str(cmd)}, output: {str(msg)}, error: {str(error)}")
                if msg is not None:
                    if "Lookup successful" in msg:
                        self.add_kafka_kpi(kafka_data_source_builder, "UAF_NSLOOKUP_AVAILABILITY", "0")
                    else:
                        self.add_kafka_kpi(kafka_data_source_builder, "UAF_NSLOOKUP_AVAILABILITY", "1")
                else:
                    self.add_kafka_kpi(kafka_data_source_builder, "UAF_NSLOOKUP_AVAILABILITY", "0", False)

            # Check at least 1 cpm pod is up/running
            # cmd = f"""kubectl get pods -n {self.namespace} | grep 'cpm-app' | grep -v proxy | grep -q '1/1 *Running' && echo "At least one pod is healthy" || echo "No healthy pods found" """
            cmd = f"""kubectl get pods -n {self.namespace} | grep 'cpm-app' | grep -v proxy | grep -vE '([13]/[13].*Running)' | wc -l """
            msg, error = self.subprocess_obj.execute_cmd(cmd)
            logging.info(f"Check at cpm pod is up/running ::: cmd: {str(cmd)}, output: {str(msg)}, error: {str(error)}")
            if msg is not None:
                msg = str(msg).strip()
                self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_POD_AVAILABILITY", msg)
            else:
                self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_POD_AVAILABILITY", "0", False)

            # Check at least 3 cil pods healthy
            # cmd = f"""[ "$(kubectl get pods -n {self.namespace} | grep -i 'eric-bss-cil-database-cd-cil0[1-6]' | awk '$2 ~ /^[13]\/[13]$/ && $3 == "Running"' | wc -l)" -ge 3 ] && echo "At least 3 CIL pods are healthy" || echo "Less than 3 healthy CIL pods found" """
            cmd = f"""kubectl get pods -n {self.namespace} | grep -i 'eric-bss-cil-database-cd-cil0[1-6]' | grep -vE '([13]/[13].*Running)' | wc -l """
            msg, error = self.subprocess_obj.execute_cmd(cmd)
            logging.info(f"Check cil pods healthy ::: cmd: {str(cmd)}, output: {str(msg)}, error: {str(error)}")
            if msg is not None:
                msg = str(msg).strip()
                self.add_kafka_kpi(kafka_data_source_builder, "UAF_GLOBAL_CIL_AVAILABILITY", msg)
            else:
                self.add_kafka_kpi(kafka_data_source_builder, "UAF_GLOBAL_CIL_AVAILABILITY", "0", False)

        except Exception as err:
            logging.error(f"Exception in Availability KPIs ::: {str(err)}")

        # Get the timestamps from the csv
        cmd = f"grep -oP 'tl_timestamp=\K[^,]+' {self.pm_csv_file} | sort | uniq"
        timestamps, error = self.subprocess_obj.execute_cmd(cmd)
        logging.info(f"Latency ::: cmd: {str(cmd)}, output: {str(timestamps)}, error: {str(error)}")
        if timestamps is None:
            logging.error(f"THERE IS ISSUE WHILE FETCHING TIMESTAMPS")

        # Latency
        try:
            ## cpm_lookup_msisdn_dns_response_duration_seconds_max
            val_holder = []
            if timestamps is not None:
                for timestamp in str(timestamps).splitlines():
                    timestamp = str(timestamp).strip()
                    cmd = f"""grep {timestamp} {self.pm_csv_file} | grep "cpm_lookup_msisdn_dns_response_duration_seconds_max" """
                    val, status = self.get_value_from_csv_file(cmd)
                    if status:
                        val_holder.append(val)

                logging.info(f"Latency ::: VALUES FROM ALL THREE FILES: {str(val_holder)}")
                max_val = 0 if len(val_holder) == 0 else max(val_holder)
                max_val = self.format_kpi_value(float(max_val))
                self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_LOOKUP_LATENCY", str(max_val))
            else:
                self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_LOOKUP_LATENCY", "0", False)

            ## cpm_provision_msisdn_dns_response_duration_seconds_max
            val_holder = []
            if timestamps is not None:
                for timestamp in str(timestamps).splitlines():
                    timestamp = str(timestamp).strip()
                    cmd = f"""grep {timestamp} {self.pm_csv_file} | grep "cpm_provision_msisdn_dns_response_duration_seconds_max" """
                    val, status = self.get_value_from_csv_file(cmd)
                    if status:
                        val_holder.append(val)

                logging.info(f"Latency ::: VALUES FROM ALL THREE FILES: {str(val_holder)}")
                max_val = 0 if len(val_holder) == 0 else max(val_holder)
                max_val = self.format_kpi_value(float(max_val))
                self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_PROVISION_LATENCY", str(max_val))
            else:
                self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_PROVISION_LATENCY", "0", False)

            ## cpm_update_msisdn_dns_response_duration_seconds_max
            val_holder = []
            if timestamps is not None:
                for timestamp in str(timestamps).splitlines():
                    timestamp = str(timestamp).strip()
                    cmd = f"""grep {timestamp} {self.pm_csv_file} | grep "cpm_update_msisdn_dns_response_duration_seconds_max" """
                    val, status = self.get_value_from_csv_file(cmd)
                    if status:
                        val_holder.append(val)

                logging.info(f"Latency ::: VALUES FROM ALL THREE FILES: {str(val_holder)}")
                max_val = 0 if len(val_holder) == 0 else max(val_holder)
                max_val = self.format_kpi_value(float(max_val))
                self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_UPDATE_LATENCY", str(max_val))
            else:
                self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_UPDATE_LATENCY", "0", False)

            ### cpm_delete_msisdn_dns_response_duration_seconds_max
            val_holder = []
            if timestamps is not None:
                for timestamp in str(timestamps).splitlines():
                    timestamp = str(timestamp).strip()
                    cmd = f"""grep {timestamp} {self.pm_csv_file} | grep "cpm_delete_msisdn_dns_response_duration_seconds_max" """
                    val, status = self.get_value_from_csv_file(cmd)
                    if status:
                        val_holder.append(val)

                logging.info(f"Latency ::: VALUES FROM ALL THREE FILES: {str(val_holder)}")
                max_val = 0 if len(val_holder) == 0 else max(val_holder)
                max_val = self.format_kpi_value(float(max_val))
                self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_DELETE_LATENCY", str(max_val))
            else:
                self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_DELETE_LATENCY", "0", False)
        except Exception as err:
            logging.error(f"Exception in Latency KPIs ::: {str(err)}")

        # SERV
        try:
            # Get CPM IP
            cmd = f"kubectl get svc -n {self.namespace} | grep -i eric-bss-cpm-app-dnstcp | awk '{{ print $4}}'"
            cpm_ip, error = self.subprocess_obj.execute_cmd(cmd)
            logging.info(f"Get CPM IP ::: cmd: {str(cmd)}, output: {str(cpm_ip)}, error: {str(error)}")
            if cpm_ip is not None:
                cmd = f"""nslookup 9999999999.9.msisdn.sub.cs {str(cpm_ip).strip()} 2>&1 | grep -q "connection timed out; no servers could be reached" && echo "IP not reachable (DNS timeout)" || echo "Lookup successful" """
                msg, error = self.subprocess_obj.execute_cmd(cmd)
                logging.info(
                    f"nslookup ::: cmd: {str(cmd)}, output: {str(msg)}, error: {str(error)}")
                if msg is not None:
                    if "Lookup successful" in msg:
                        self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_AVAILABILITY_TIMEOUT", "0")
                    else:
                        self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_AVAILABILITY_TIMEOUT", "1")
                else:
                    self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_AVAILABILITY_TIMEOUT", "0", False)

                cmd = f"""nslookup 9999999999.9.msisdn.sub.cs {str(cpm_ip).strip()} 2>&1 | grep -q "SERVFAIL" && echo "SERVFAIL" || echo "Lookup successful" """
                msg, error = self.subprocess_obj.execute_cmd(cmd)
                logging.info(
                    f"nslookup ::: cmd: {str(cmd)}, output: {str(msg)}, error: {str(error)}")
                if msg is not None:
                    if "Lookup successful" in msg:
                        self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_AVAILABILITY_SERVFAIL", "0")
                    else:
                        self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_AVAILABILITY_SERVFAIL", "1")
                else:
                    self.add_kafka_kpi(kafka_data_source_builder, "UAF_CPM_AVAILABILITY_SERVFAIL", "0", False)
        except Exception as err:
            logging.error(f"Exception in SERVFAIL KPIs ::: {str(err)}")

        # SUBSCRIBER NOT FOUND
        cpm_pods = None
        try:
            cmd = f"""kubectl get pod -n {self.namespace} | grep "cpm-app" | grep -v "proxy" | awk '{{ print $1 }}' """
            cpm_pods, error = self.subprocess_obj.execute_cmd(cmd)
            logging.info(
                f"Subscriber Not Found ::: cpm_pods :::: cmd: {str(cmd)}, output: {str(cpm_pods)}, error: {str(error)}")
            if cpm_pods is not None:
                subscriber_error_count = 0
                for pod in str(cpm_pods).splitlines():
                    pod = str(pod).strip()
                    # cmd = """kubectl logs {pod} -n {self.namespace} | egrep -o "The MSISDN with id=\[[a-zA-Z0-9_]+\][0-9]+\[/[a-zA-Z0-9_]+\] does not exist|The Subscriber Account Location with \[id *= *[^]]+\] does not exist\.|The mapping of Subscriber Account Location with \[\{\*\}id *= *[^}]+\}\{\*\}\] does not exist\." | sort | uniq -c | sort -nr | wc -l  """.replace(
                    #     "{pod}", pod).replace("{self.namespace}", self.namespace)
                    # The MSISDN with id
                    cmd = """kubectl logs {pod} -n {self.namespace} --since=15m | egrep -o "The MSISDN with id=\[[a-zA-Z0-9_]+\][0-9]+\[/[a-zA-Z0-9_]+\] does not exist" | sort | uniq -c | sort -nr | wc -l  """.replace("{pod}", pod).replace("{self.namespace}", self.namespace)
                    subscriber_count, error = self.subprocess_obj.execute_cmd(cmd)
                    logging.info(f"Subscriber Not Found ::: The MSISDN with id count from logs :::: cmd: {str(cmd)}, output: {str(subscriber_count)}, error: {str(error)}")

                    if subscriber_count is not None:
                        subscriber_count = str(subscriber_count).strip()
                        subscriber_error_count = subscriber_error_count + int(subscriber_count)
                        logging.info(f"Subscriber Not Found ::: subscriber_error_count: {subscriber_error_count}")

                    # The Subscriber Account Location with
                    cmd = """kubectl logs {pod} -n {self.namespace} --since=15m | egrep -o "The Subscriber Account Location with \[id *= *[^]]+\] does not exist\." | sort | uniq -c | sort -nr | wc -l  """.replace("{pod}", pod).replace("{self.namespace}", self.namespace)
                    subscriber_count, error = self.subprocess_obj.execute_cmd(cmd)
                    logging.info(f"Subscriber Not Found ::: The Subscriber Account Location with count from logs :::: cmd: {str(cmd)}, output: {str(subscriber_count)}, error: {str(error)}")

                    if subscriber_count is not None:
                        subscriber_count = str(subscriber_count).strip()
                        subscriber_error_count = subscriber_error_count + int(subscriber_count)
                        logging.info(f"Subscriber Not Found ::: subscriber_error_count: {subscriber_error_count}")

                    # The mapping of Subscriber Account Location with
                    cmd = """kubectl logs {pod} -n {self.namespace} --since=15m | egrep -o "The mapping of Subscriber Account Location with \[\{\*\}id *= *[^}]+\}\{\*\}\] does not exist\." | sort | uniq -c | sort -nr | wc -l  """.replace("{pod}", pod).replace("{self.namespace}", self.namespace)
                    subscriber_count, error = self.subprocess_obj.execute_cmd(cmd)
                    logging.info(
                        f"Subscriber Not Found ::: The mapping of Subscriber Account Location with count from logs :::: cmd: {str(cmd)}, output: {str(subscriber_count)}, error: {str(error)}")

                    if subscriber_count is not None:
                        subscriber_count = str(subscriber_count).strip()
                        subscriber_error_count = subscriber_error_count + int(subscriber_count)
                        logging.info(f"Subscriber Not Found ::: subscriber_error_count: {subscriber_error_count}")

                self.add_kafka_kpi(kafka_data_source_builder, "UAF_SUBSCRIBER_NOT_FOUND_COUNT", str(subscriber_error_count))
            else:
                self.add_kafka_kpi(kafka_data_source_builder, "UAF_SUBSCRIBER_NOT_FOUND_COUNT", "0", False)
        except Exception as err:
            logging.error(f"Exception in SUBSCRIBER NOT FOUND KPIs ::: {str(err)}")


        # POD RESTART
        try:
            cmd = f"""kubectl get pods -n {self.namespace} -o custom-columns="NAME:.metadata.name,RESTARTS:.status.containerStatuses[*].restartCount" | grep -i eric-bss-cpm-app | grep -v "proxy" """
            restart_output, error = self.subprocess_obj.execute_cmd(cmd)
            logging.info(f"POD RESTART ::: cmd: {str(cmd)}, output: {str(restart_output)}, error: {str(error)}")
            val_dict = {}
            if restart_output is not None:
                for line in str(restart_output).splitlines():
                    pod_name, restart_count = str(line).strip().split()
                    val_dict.update({str(pod_name): int(restart_count)})

                # Get old values and update latest one to file
                # old_data = self.check_pod_restart_data(val_dict)
                # pod_count = 0
                vals = list(val_dict.values())
                if vals:
                    self.add_kafka_kpi(kafka_data_source_builder, f"UAF_POD_MAX_RESTART_COUNT", str(max(vals)))
                else:
                    self.add_kafka_kpi(kafka_data_source_builder, f"UAF_POD_MAX_RESTART_COUNT", "0", False)

            else:
                self.add_kafka_kpi(kafka_data_source_builder, f"UAF_POD_MAX_RESTART_COUNT", "0", False)
        except Exception as err:
            logging.error(f"Exception in POD RESTART KPIs ::: {str(err)}")

        # CPU Utilization
        try:
            max_cpu = 0
            max_memory = 0
            occupied_cpu = 0
            occupied_memory = 0
            cpu_and_memory_dict = {}
            if cpm_pods is not None:
                for pod in str(cpm_pods).splitlines():
                    pod = str(pod).strip()
                    cpu_and_memory_dict.update({pod: {}})
                    cmd = """kubectl describe pod -n <self.namespace> <pod> | awk '/Containers:/ {c=1} /Init Containers:/ {c=0} c && /^  eric-bss-cpm-app:/ {f=1} f && /Limits:/ {l=1; print; next} f && l && /^[ ]{6}/ {print; next} l && !/^[ ]{6}/ {exit}' """.replace(
                        "<self.namespace>", self.namespace).replace("<pod>", pod)
                    limit_from_describe_pod, error = self.subprocess_obj.execute_cmd(cmd)
                    logging.info(
                        f"MAX CPU AND MEMORY FROM DESCRIBE POD ::: cmd: {str(cmd)}, output: {str(limit_from_describe_pod)}, error: {str(error)}")
                    if limit_from_describe_pod is not None:
                        for line in str(limit_from_describe_pod).splitlines():
                            line = str(line).strip()
                            if "cpu:" in line:
                                name, val = str(line).split()
                                max_cpu = int(str(val).replace("m", ""))
                                cpu_and_memory_dict[pod].update({"max_cpu": max_cpu})
                            elif "memory:" in line:
                                name, val = str(line).split()
                                if "Gi" in val:
                                    val = str(val).replace("Gi", "")
                                    max_memory = int(val) * 1024
                                    # cpu_and_memory_dict.update({"max_memory": max_memory})

                                if "Mi" in val:
                                    val = str(val).replace("Mi", "")
                                    max_memory = int(val)

                                cpu_and_memory_dict[pod].update({"max_memory": max_memory})

                    cmd = f"""kubectl top pod -n {self.namespace} {pod} 2>/dev/null | awk 'NR>1 {{print $2, $3}}' """
                    limit_from_top_pod, error = self.subprocess_obj.execute_cmd(cmd)
                    logging.info(
                        f"OCCUPIED CPU AND MEMORY FROM TOP COMMAND ::: cmd: {str(cmd)}, output: {str(limit_from_top_pod)}, error: {str(error)}")
                    if limit_from_top_pod is not None:
                        occupied_cpu, occupied_memory = str(limit_from_top_pod).strip().split()
                        occupied_cpu = int(str(occupied_cpu).replace("m", ""))
                        cpu_and_memory_dict[pod].update({"occupied_cpu": occupied_cpu})

                        if "Gi" in str(occupied_memory):
                            occupied_memory = str(occupied_memory).replace("Gi", "")
                            occupied_memory = int(occupied_memory) * 1024

                        if "Mi" in str(occupied_memory):
                            occupied_memory = str(occupied_memory).replace("Mi", "")
                            occupied_memory = int(occupied_memory)

                        cpu_and_memory_dict[pod].update({"occupied_memory": occupied_memory})


                max_cpu, max_memory = self.get_max_from_dict(cpu_and_memory_dict)
                self.add_kafka_kpi(kafka_data_source_builder, f"UAF_MAX_CPU_USAGE", str(float(max_cpu)))
                self.add_kafka_kpi(kafka_data_source_builder, f"UAF_MAX_MEMORY_USAGE", str(float(max_memory)))
            else:
                self.add_kafka_kpi(kafka_data_source_builder, f"UAF_MAX_CPU_USAGE", "0", False)
                self.add_kafka_kpi(kafka_data_source_builder, f"UAF_MAX_MEMORY_USAGE", "0", False)
        except Exception as err:
            logging.error(f"Exception in CPU Utilization KPIs ::: {str(err)}")
