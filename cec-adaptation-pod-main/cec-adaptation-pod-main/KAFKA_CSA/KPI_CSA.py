#!/usr/bin/python
# Copyright (c) 2019 Ericsson Inc
# All rights reserved.
# The Copyright to the computer program(s) herein is the property of Ericsson AB, Sweden.
# The program(s) may be used and/or copied with the written permission from Ericsson AB
# or in accordance with the terms and conditions stipulated in the agreement/contract
# under which the program(s) have been supplied.
#
#
# Fetches multiple KPI parameters and formats/outputs to a timestamped CSA_KPI file for kafka input
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
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from KAFKA_SENDER import KafkaDataSourceBuilder
from KPI_Helper import banner, files_newer_that_mins, is_http_ok
from SubprocessClass import SubprocessClass

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.kpi_csv_aggregator.aggregator2 import Aggregator2, KpiAndValue, KpiDef, fs, Oper, CntType

import lxml.etree as ET


class KPI_CSA:
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
        self.pm_csv_file = os.path.join(script_dir, "pm_file.csv")
        self.measCollec_xsl = os.path.join(script_dir, "measCollec.xsl")

    def format_kpi_value(self, value: float) -> str:
        if type(value) == int or value.is_integer():
            return '{0:.0f}'.format(value)
        else:
            return '{0:.2f}'.format(round(value, 2))

    def add_kafka_kpi(self, kpi: KpiAndValue, is_dummy_message: bool = False):
        if kpi.value is not None:
            value = kpi.value
            kpi_result = "UNDEFINED"
        else:
            value = 0
            kpi_result = "NO-DATA"
        if is_dummy_message:
            self.kafka_data_source_builder.add_data_record(
                [kpi.name.upper(), self.format_kpi_value(value), kpi_result, is_dummy_message])
        else:
            self.kafka_data_source_builder.add_data_record([kpi.name.upper(), self.format_kpi_value(value), kpi_result])

    def execute_kubectl(self, csa, command, command_type=None):
        try:
            if "{" in command or "}" in command:
                command = command.replace("{", "{{")
                command = command.replace("}", "}}")
            if command_type == "bash":
                command = f"""kubectl exec -it {csa} -- bash -c '{command}' """
            else:
                command = f"""kubectl exec -it -n {self.namespace} {csa} -- {command} """
            logging.info(f"Command - {str(command)}")
            output, error = self.subprocess_obj.execute_cmd(command)
            return output, error
        except Exception as err:
            logging.error("Exception in update_command ::: " + str(err))

    def write_kpi(self, line):
        try:
            val = ""
            nf_instance = ""
            countername = ""
            envoy_response_code_class = ""
            instance = ""
            pool_name = ""
            nf_type = ""
            for field in line.split(","):
                if "countervalue" in field:
                    key_value = field.split("=")
                    if len(key_value) == 2:
                        val = key_value[1]

                if "nf_instance" in field:
                    nf_instance = field.split("=")
                    nf_instance = nf_instance[1]

                if "countername" in field:
                    countername = field.split("=")
                    countername = countername[1]

                if "envoy_response_code_class" in field:
                    envoy_response_code_class = field.split("=")
                    envoy_response_code_class = envoy_response_code_class[1]

                if ",instance" in field:
                    instance = field.split("=")
                    instance = instance[1]

                if "pool_name" in field:
                    pool_name = field.split("=")
                    pool_name = pool_name[1]

                if "nf_type" in field:
                    nf_type = field.split("=")
                    nf_type = nf_type[1]

            if envoy_response_code_class != "":
                if len(str(envoy_response_code_class)) == 1:
                    envoy_response_code_class = "0" + str(envoy_response_code_class)
                countername = str(countername).replace("xx", envoy_response_code_class)

            kpi_names = [str(nf_instance), str(nf_type), str(countername), str(pool_name), str(instance)]
            final_kpi_name = "_".join(i for i in kpi_names if i != "")
            return final_kpi_name, val
        except Exception as e:
            logging.error("Exception in write_kpi ::: " + str(e))

    def aggregate_pm_files_into_csv_file(self, csa, pm_file_paths: List[str]):
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
            logging.exception(f"Failed aggregating PM file into csv file")
            return None

    def write_pm_kpis(self, interval_mins: int):
        logging.info(banner("Calculating KPIs"))

        with open(self.pm_csv_file, 'r') as f:
            data_lines = f.readlines()

        agg = Aggregator2(interval_mins, data_lines)

        logging.info(f'Interval: {interval_mins} minutes')

        cc_and_iotcc_combined_pool = [".*cc_.*", ".*iotchf_.*"]

        # SCP_LOAD
        self.add_kafka_kpi(
            agg.calc_kpi(KpiDef('SCP_LOAD', fs(['measInfoId=scp_system_metrics', 'countername=scp_load']), Oper.avg)))

        ############# CAF Traffic KPIs #############
        total_accepted_traffic_caf: KpiAndValue = agg.calc_var(KpiDef('TOTAL_ACCEPTED_TRAFFIC_CC',
                                                                      fs(['measInfoId=scp_egress', 'pool_name=.*cc_.*',
                                                                          'countername=envoy_egress_upstream_rq_total,']),
                                                                      Oper.sum))
        # CAF_BY_RESP_CODE
        for code in ["200", "201", "204", "400", "404", "410", "500", "503", "504"]:
            counter = KpiDef(f"TRAFFIC_CAF_BY_RESP_CODE_{code}",
                             fs(['measInfoId=scp_egress', 'pool_name=.*cc_.*', 'countername=envoy_egress_upstream_rq,',
                                 f'envoy_response_code={code}']), Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter), is_dummy_message=True)
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"TRAFFIC_CAF_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_caf), is_dummy_message=True)
        # CAF_CREATE_BY_RESP_CODE
        for code in ["201", "400", "503", "504"]:
            counter = KpiDef(f"CAF_CREATE_BY_RESP_CODE_{code}", fs(['measInfoId=scp_egress', 'pool_name=.*cc_create.*',
                                                                    'countername=envoy_egress_upstream_rq,',
                                                                    f'envoy_response_code={code}']), Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter), is_dummy_message=True)
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"CAF_CREATE_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_caf), is_dummy_message=True)
        # CAF_UPDATE_BY_RESP_CODE
        for code in ["200", "400", "404", "410", "500", "503", "504"]:
            counter = KpiDef(f"CAF_UPDATE_BY_RESP_CODE_{code}", fs(['measInfoId=scp_egress', 'pool_name=.*cc_update.*',
                                                                    'countername=envoy_egress_upstream_rq,',
                                                                    f'envoy_response_code={code}']), Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter), is_dummy_message=True)
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"CAF_UPDATE_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_caf), is_dummy_message=True)
        # CAF_RELEASE_BY_RESP_CODE
        for code in ["204", "400", "404", "410", "500", "503", "504"]:
            counter = KpiDef(f"CAF_RELEASE_BY_RESP_CODE_{code}",
                             fs(['measInfoId=scp_egress', 'pool_name=.*cc_release.*',
                                 'countername=envoy_egress_upstream_rq,',
                                 f'envoy_response_code={code}']), Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter), is_dummy_message=True)
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"CAF_RELEASE_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_caf), is_dummy_message=True)
        # CC_NOTIFY_BY_RESP_CODE
        for code in ["204", "404", "500", "504"]:
            counter = KpiDef(f"CC_NOTIFY_BY_RESP_CODE_{code}", fs(['measInfoId=scp_egress', 'pool_name=.*cc_notify.*',
                                                                    'countername=envoy_egress_upstream_rq,',
                                                                    f'envoy_response_code={code}']), Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter))
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"CC_NOTIFY_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_caf))

        ############# SLC Traffic KPIs #############
        total_accepted_traffic_slc: KpiAndValue = agg.calc_var(KpiDef('TOTAL_ACCEPTED_TRAFFIC_SLC',
                                                                      fs(['measInfoId=scp_egress', 'pool_name=.*slc_.*',
                                                                          'countername=envoy_egress_upstream_rq_total,']),
                                                                      Oper.sum))

        # SLC_BY_RESP_CODE
        for code in ["200", "201", "204", "400", "403", "404", "500"]:
            counter = KpiDef(f"TRAFFIC_SLC_BY_RESP_CODE_{code}",
                             fs(['measInfoId=scp_egress', 'pool_name=.*slc_.*', 'countername=envoy_egress_upstream_rq,',
                                 f'envoy_response_code={code}']), Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter))
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"TRAFFIC_SLC_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_slc))
        # SUBSCRIBE_SLC_BY_RESP_CODE
        for code in ["201", "400", "403", "404", "500"]:
            counter = KpiDef(f"SUBSCRIBE_SLC_BY_RESP_CODE_{code}",
                             fs(['measInfoId=scp_egress', 'pool_name=.*slc_subscribe.*',
                                 'countername=envoy_egress_upstream_rq,', f'envoy_response_code={code}']),
                             Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter))
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"SUBSCRIBE_SLC_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_slc))
        # UNSUBSCRIBE_SLC_BY_RESP_CODE
        for code in ["204", "400", "500"]:
            counter = KpiDef(f"UNSUBSCRIBE_SLC_BY_RESP_CODE_{code}",
                             fs(['measInfoId=scp_egress', 'pool_name=.*slc_unsubscribe.*',
                                 'countername=envoy_egress_upstream_rq,', f'envoy_response_code={code}']), Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter))
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"UNSUBSCRIBE_SLC_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_slc))
        # MODIFY_SLC_BY_RESP_CODE
        for code in ["200", "400"]:
            counter = KpiDef(f"MODIFY_SLC_BY_RESP_CODE_{code}", fs(['measInfoId=scp_egress', 'pool_name=.*slc_modify.*',
                                                                    'countername=envoy_egress_upstream_rq,',
                                                                    f'envoy_response_code={code}']), Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter))
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"MODIFY_SLC_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_slc))
        # NOTIFY_SLC_BY_RESP_CODE
        for code in ["204", "404"]:
            counter = KpiDef(f"NOTIFY_SLC_BY_RESP_CODE_{code}", fs(['measInfoId=scp_egress', 'pool_name=.*slc_notify.*',
                                                                    'countername=envoy_egress_upstream_rq,',
                                                                    f'envoy_response_code={code}']), Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter))
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"NOTIFY_SLC_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_slc))

        ############# IOTCC Traffic KPIs #############
        total_accepted_traffic_iotcc: KpiAndValue = agg.calc_var(KpiDef('TOTAL_ACCEPTED_TRAFFIC_IOTCC',
                                                                        fs(['measInfoId=scp_egress',
                                                                            'pool_name=.*iotchf_.*',
                                                                            'countername=envoy_egress_upstream_rq_total,']),
                                                                        Oper.sum))
        # IOTCC_BY_RESP_CODE
        for code in ["200", "201", "204", "400", "404", "410", "500", "503", "504"]:
            counter = KpiDef(f"TRAFFIC_IOTCC_BY_RESP_CODE_{code}",
                             fs(['measInfoId=scp_egress', 'pool_name=.*iotchf_.*',
                                 'countername=envoy_egress_upstream_rq,',
                                 f'envoy_response_code={code}']), Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter), is_dummy_message=True)
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"TRAFFIC_IOTCC_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_iotcc))
        # IOTCC_CREATE_BY_RESP_CODE
        for code in ["201", "400", "503", "504"]:
            counter = KpiDef(f"IOTCC_CREATE_BY_RESP_CODE_{code}",
                             fs(['measInfoId=scp_egress', 'pool_name=.*iotchf_create.*',
                                 'countername=envoy_egress_upstream_rq,',
                                 f'envoy_response_code={code}']), Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter), is_dummy_message=True)
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"IOTCC_CREATE_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_iotcc), is_dummy_message=True)
        # IOTCC_UPDATE_BY_RESP_CODE
        for code in ["200", "400", "404", "410", "500", "503", "504"]:
            counter = KpiDef(f"IOTCC_UPDATE_BY_RESP_CODE_{code}",
                             fs(['measInfoId=scp_egress', 'pool_name=.*iotchf_update.*',
                                 'countername=envoy_egress_upstream_rq,',
                                 f'envoy_response_code={code}']), Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter), is_dummy_message=True)
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"IOTCC_UPDATE_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_iotcc), is_dummy_message=True)
        # IOTCC_RELEASE_BY_RESP_CODE
        for code in ["204", "400", "404", "410", "500", "503", "504"]:
            counter = KpiDef(f"IOTCC_RELEASE_BY_RESP_CODE_{code}",
                             fs(['measInfoId=scp_egress', 'pool_name=.*iotchf_release.*',
                                 'countername=envoy_egress_upstream_rq,',
                                 f'envoy_response_code={code}']), Oper.sum)
            if is_http_ok(code):
                self.add_kafka_kpi(agg.calc_kpi(counter), is_dummy_message=True)
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"IOTCC_RELEASE_RATE_BY_RESP_CODE_{code}",
                                                agg.calc_var(counter),
                                                total_accepted_traffic_iotcc), is_dummy_message=True)

        ############# IOTCC and CC Combined Traffic #############
        cc_and_iotcc_combined_accepted_traffic = agg.addition_counters("TOTAL_ACCEPTED_TRAFFIC",
                                                                       total_accepted_traffic_caf,
                                                                       total_accepted_traffic_iotcc,
                                                                       CntType.Cnt)

        # COMBINED_IOTCC_AND_CC_BY_RESP_CODE
        for code in ["200", "201", "204", "400", "404", "410", "500", "503", "504"]:
            counter_iotcc = KpiDef(f"TRAFFIC_IOTCC_BY_RESP_CODE_{code}",
                                   fs(['measInfoId=scp_egress', 'pool_name=.*iotchf_.*',
                                       'countername=envoy_egress_upstream_rq,',
                                       f'envoy_response_code={code}']), Oper.sum)

            counter_cc = KpiDef(f"TRAFFIC_CC_BY_RESP_CODE_{code}",
                                fs(['measInfoId=scp_egress', 'pool_name=.*cc_.*',
                                    'countername=envoy_egress_upstream_rq,',
                                    f'envoy_response_code={code}']), Oper.sum)

            counter = agg.addition_counters(f"TRAFFIC_CC_BY_RESP_CODE_{code}",
                                            agg.calc_kpi(counter_iotcc),
                                            agg.calc_kpi(counter_cc), CntType.Cnt)

            if is_http_ok(code):
                self.add_kafka_kpi(counter)
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"TRAFFIC_CC_RATE_BY_RESP_CODE_{code}",
                                                counter,
                                                cc_and_iotcc_combined_accepted_traffic))

        # COMBINED_IOTCC_AND_CC_CREATE_BY_RESP_CODE
        for code in ["201", "400", "503", "504"]:
            counter_iotcc = KpiDef(f"IOTCC_CREATE_BY_RESP_CODE_{code}",
                                   fs(['measInfoId=scp_egress', 'pool_name=.*iotchf_create.*',
                                       'countername=envoy_egress_upstream_rq,',
                                       f'envoy_response_code={code}']), Oper.sum)

            counter_cc = KpiDef(f"CC_CREATE_BY_RESP_CODE_{code}",
                                fs(['measInfoId=scp_egress', 'pool_name=.*cc_create.*',
                                    'countername=envoy_egress_upstream_rq,',
                                    f'envoy_response_code={code}']), Oper.sum)

            counter = agg.addition_counters(f"CC_CREATE_BY_RESP_CODE_{code}",
                                            agg.calc_kpi(counter_iotcc),
                                            agg.calc_kpi(counter_cc), CntType.Cnt)

            if is_http_ok(code):
                self.add_kafka_kpi(counter)
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"CC_CREATE_RATE_BY_RESP_CODE_{code}",
                                                counter,
                                                cc_and_iotcc_combined_accepted_traffic))
        # COMBINED_IOTCC_AND_CC_UPDATE_BY_RESP_CODE
        for code in ["200", "400", "404", "410", "500", "503", "504"]:
            counter_iotcc = KpiDef(f"IOTCC_UPDATE_BY_RESP_CODE_{code}",
                                   fs(['measInfoId=scp_egress', 'pool_name=.*iotchf_update.*',
                                       'countername=envoy_egress_upstream_rq,',
                                       f'envoy_response_code={code}']), Oper.sum)

            counter_cc = KpiDef(f"CC_UPDATE_BY_RESP_CODE_{code}",
                                fs(['measInfoId=scp_egress', 'pool_name=.*cc_update.*',
                                    'countername=envoy_egress_upstream_rq,',
                                    f'envoy_response_code={code}']), Oper.sum)

            counter = agg.addition_counters(f"CC_UPDATE_BY_RESP_CODE_{code}",
                                            agg.calc_kpi(counter_iotcc),
                                            agg.calc_kpi(counter_cc), CntType.Cnt)

            if is_http_ok(code):
                self.add_kafka_kpi(counter)
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"CC_UPDATE_RATE_BY_RESP_CODE_{code}",
                                                counter,
                                                cc_and_iotcc_combined_accepted_traffic))
        # COMBINED_IOTCC_AND_CC_RELEASE_BY_RESP_CODE
        for code in ["204", "400", "404", "410", "500", "503", "504"]:
            counter_iotcc = KpiDef(f"IOTCC_RELEASE_BY_RESP_CODE_{code}",
                                   fs(['measInfoId=scp_egress', 'pool_name=.*iotchf_release.*',
                                       'countername=envoy_egress_upstream_rq,',
                                       f'envoy_response_code={code}']), Oper.sum)

            counter_cc = KpiDef(f"CC_RELEASE_BY_RESP_CODE_{code}",
                                fs(['measInfoId=scp_egress', 'pool_name=.*cc_release.*',
                                    'countername=envoy_egress_upstream_rq,',
                                    f'envoy_response_code={code}']), Oper.sum)

            counter = agg.addition_counters(f"CC_RELEASE_BY_RESP_CODE_{code}",
                                            agg.calc_kpi(counter_iotcc),
                                            agg.calc_kpi(counter_cc), CntType.Cnt)

            if is_http_ok(code):
                self.add_kafka_kpi(counter)
            else:
                self.add_kafka_kpi(agg.rate_kpi(f"CC_RELEASE_RATE_BY_RESP_CODE_{code}",
                                                counter,
                                                cc_and_iotcc_combined_accepted_traffic))

        # TOTAL_ACCEPTED_TRAFFIC
        total_accepted_traffic = agg.addition_counters("TOTAL_ACCEPTED_TRAFFIC", total_accepted_traffic_slc,
                                                       total_accepted_traffic_caf, CntType.Cnt)

        SCP_TRANSACTION_SUCCESS_TPS = agg.calc_var(KpiDef('SCP_transaction_success', fs(['measInfoId=scp_ingress',
                                                                                         'countername=envoy_ingress_downstream_rq_xx,',
                                                                                         'envoy_response_code_class=2']),
                                                          Oper.tps))
        SCP_TRANSACTION_ALL_TPS = agg.calc_var(KpiDef('SCP_transaction_all', fs(['measInfoId=scp_ingress',
                                                                                 'countername=envoy_ingress_downstream_rq_total,']),
                                                      Oper.tps))

        SCP_TRANSACTION_SUCCESS_SLC_TPS = agg.calc_var(KpiDef('SCP_transaction_success_slc',
                                                              fs(['measInfoId=scp_egress', 'pool_name=.*slc_.*',
                                                                  'countername=envoy_egress_upstream_rq_xx,',
                                                                  'envoy_response_code_class=2']), Oper.tps))
        SCP_TRANSACTION_SLC_ALL_TPS = agg.calc_var(KpiDef('SCP_transaction_all_slc',
                                                          fs(['measInfoId=scp_egress', 'pool_name=.*slc_.*',
                                                              'countername=envoy_egress_upstream_rq_total,']),
                                                          Oper.tps))

        SCP_CONVERGED_CHARGING_SUCCESS = agg.calc_var(KpiDef('SCP_converged_charging_success',
                                                             fs(['measInfoId=scp_egress', 'pool_name=.*cc_.*',
                                                                 'countername=envoy_egress_upstream_rq_xx,',
                                                                 'envoy_response_code_class=2']), Oper.tps))
        SCP_CONVERGED_CHARGING_ALL = agg.calc_var(KpiDef('SCP_converged_charging_all',
                                                         fs(['measInfoId=scp_egress', 'pool_name=.*cc_.*',
                                                             'countername=envoy_egress_upstream_rq_total,']), Oper.tps))

        SCP_CONVERGED_CHARGING_SUCCESS_IOTCC = agg.calc_var(KpiDef('SCP_converged_charging_success_iotcc',
                                                                   fs(['measInfoId=scp_egress', 'pool_name=.*iotchf_.*',
                                                                       'countername=envoy_egress_upstream_rq_xx,',
                                                                       'envoy_response_code_class=2']), Oper.tps))
        SCP_CONVERGED_CHARGING_ALL_IOTCC = agg.calc_var(KpiDef('SCP_converged_charging_all_iotcc',
                                                               fs(['measInfoId=scp_egress', 'pool_name=.*iotchf_.*',
                                                                   'countername=envoy_egress_upstream_rq_total,']),
                                                               Oper.tps))

        SCP_CONVERGED_CHARGING_SUCCESS_COMBINED = agg.addition_counters("SCP_converged_charging_success_combined",
                                                                        SCP_CONVERGED_CHARGING_SUCCESS,
                                                                        SCP_CONVERGED_CHARGING_SUCCESS_IOTCC,
                                                                        CntType.Cnt)

        SCP_CONVERGED_CHARGING_ALL_COMBINED = agg.addition_counters("SCP_converged_charging_all_combined",
                                                                    SCP_CONVERGED_CHARGING_ALL,
                                                                    SCP_CONVERGED_CHARGING_ALL_IOTCC,
                                                                    CntType.Cnt)

        self.add_kafka_kpi(
            agg.rate_kpi('SCP_TRANSACTION_SUCCESS_RATE', SCP_TRANSACTION_SUCCESS_TPS, SCP_TRANSACTION_ALL_TPS))
        self.add_kafka_kpi(agg.rate_kpi('SCP_TRANSACTION_SUCCESS_RATE_SLC', SCP_TRANSACTION_SUCCESS_SLC_TPS,
                                        SCP_TRANSACTION_SLC_ALL_TPS))
        self.add_kafka_kpi(
            agg.rate_kpi('SCP_TRANSACTION_SUCCESS_RATE_CAF', SCP_CONVERGED_CHARGING_SUCCESS,
                         SCP_CONVERGED_CHARGING_ALL), is_dummy_message=True)
        self.add_kafka_kpi(
            agg.rate_kpi('SCP_TRANSACTION_SUCCESS_RATE_CC', SCP_CONVERGED_CHARGING_SUCCESS_COMBINED,
                         SCP_CONVERGED_CHARGING_ALL_COMBINED))

        self.add_kafka_kpi(
            agg.rate_kpi('SCP_TRANSACTION_SUCCESS_RATE_IOTCC', SCP_CONVERGED_CHARGING_SUCCESS_IOTCC,
                         SCP_CONVERGED_CHARGING_ALL_IOTCC))

        OUTGOING_REQUESTS_ON_NNRF_NFMANAGEMENT_INTERFACE_GLOBAL_NRF = agg.calc_kpi(
            KpiDef(f"OUTGOING_REQUESTS_ON_NNRF_NFMANAGEMENT_INTERFACE_GLOBAL_NRF",
                   fs(['measInfoId=scp_nrf', 'service=nnrf-disc', 'countername=scp_nrf_out_requests_total,']),
                   Oper.sum))
        SUCC_ANSWERS_FROM_GLOBAL_NRF = agg.calc_var(KpiDef(f"TOTAL_SUCC_ANSWERS_FROM_GLOBAL_NRF",
                                                           fs(['measInfoId=scp_nrf', 'service=nnrf-disc',
                                                               'countername=scp_nrf_in_answers_total,', 'status=2']),
                                                           Oper.sum))
        self.add_kafka_kpi(agg.rate_kpi('GNRF_TRANSACTION_SUCCESS_RATE', SUCC_ANSWERS_FROM_GLOBAL_NRF,
                                        OUTGOING_REQUESTS_ON_NNRF_NFMANAGEMENT_INTERFACE_GLOBAL_NRF))

        OUTGOING_REQUESTS_ON_NNRF_NFMANAGEMENT_INTERFACE_REGIONAL_NRF = agg.calc_kpi(
            KpiDef(f"OUTGOING_REQUESTS_ON_NNRF_NFMANAGEMENT_INTERFACE_REGIONAL_NRF",
                   fs(['measInfoId=scp_nrf', 'service=nnrf-nfm', 'countername=scp_nrf_out_requests_total,']), Oper.sum))
        SUCC_ANSWERS_FROM_REGIONAL_NRF = agg.calc_var(KpiDef(f"TOTAL_SUCC_ANSWERS_FROM_REGIONAL_NRF",
                                                             fs(['measInfoId=scp_nrf', 'service=nnrf-nfm',
                                                                 'countername=scp_nrf_in_answers_total,', 'status=2']),
                                                             Oper.sum))
        self.add_kafka_kpi(agg.rate_kpi('RNRF_TRANSACTION_SUCCESS_RATE', SUCC_ANSWERS_FROM_REGIONAL_NRF,
                                        OUTGOING_REQUESTS_ON_NNRF_NFMANAGEMENT_INTERFACE_REGIONAL_NRF))

    def write_pod_status_kpi(self):
        STATUS_UNDEFINED = "undefined"
        status = STATUS_UNDEFINED
        kpi = 0
        out, error = self.subprocess_obj.execute_cmd(f"""kubectl get pods -n {self.namespace} --no-headers""")
        try:
            if error:
                raise ValueError(f'Failed fetching pods information, error: {error}')
            for line in out.splitlines():
                fields = line.strip().split()
                status = fields[2] if len(fields) > 2 else "undefined"
                if status not in ["Running", "Completed"]:
                    kpi = 1
                    break
            logging.info(f"KPI: CSA_PROCESS_HC = {kpi}, status is: {status}")
            self.add_kafka_kpi(KpiAndValue("CSA_PROCESSS_HC", kpi))

        except Exception as err:
            logging.exception(f"Failed to fetch status of pods")

    def set_message(self, data_source_hostname, data_source_ip, kafka_data_source_builder: KafkaDataSourceBuilder):
        kafka_data_source_builder.set_message_field("kpi_last_updated_date", self.todayUTC)
        kafka_data_source_builder.set_message_field("kpi_source",
                                                    f'{data_source_hostname} > KPI_CSA.py > {self.utcTimestamp}')
        kafka_data_source_builder.set_message_field("config_item", self.host_name)
        kafka_data_source_builder.set_message_field("kpi_info", f'{data_source_hostname} {data_source_ip}')
        kafka_data_source_builder.set_message_field("src_modified_dt", self.todayUTCMilli)
        kafka_data_source_builder.set_message_field("local_modified_dt", self.localNowMilli)

    def main(self, csa):
        cmd: str = ""

        logging.info(f'PM-BULK NAME - {csa}')

        # Get hostname of csa pod
        try:
            cmd = """cat /etc/hosts | awk 'END{print  $1 "," $2}' """
            ip_hostname_csv, error = self.execute_kubectl(csa, cmd)
            ip_hostname = ip_hostname_csv.split(',')
            data_source_ip = ip_hostname[0].strip()
            data_source_hostname = ip_hostname[1].strip() if len(ip_hostname) > 1 else "undefined-hostname"
            logging.info(f"Hostname: {data_source_hostname}, IP: {data_source_ip}")

            self.set_message(data_source_hostname, data_source_ip, self.kafka_data_source_builder)
        except Exception as err:
            logging.error(f"Exception {str(csa)} ::: {str(err)}")

        # Checking
        try:
            cmd = """ip addr show eth1 | grep -w inet | wc -l """
            count, error = self.subprocess_obj.execute_cmd(cmd)
            count = count.strip()
            if int(count) == 1:
                logging.info("Not an active director node, exiting...")
                sys.exit(0)
        except Exception as err:
            logging.error(f"Exception {cmd} ::: {str(err)}")

        # Get the PM-BulK reporter Port
        try:
            cmd = """kubectl get svc -n csa | grep pm-bulk | awk -F' ' '{print $1 "," $5}' """
            count, error = self.subprocess_obj.execute_cmd(cmd)
            name_and_port = count.strip()
            if len(count) > 4:
                self.pm_bulk_name = name_and_port.split(",")[0]
                self.pm_bulk_port = name_and_port.split(",")[1]
                if len(self.pm_bulk_port) > 1 and "TCP" in self.pm_bulk_port:
                    self.pm_bulk_port = self.pm_bulk_port.split(":")[1].split("/")[0]
                    logging.info(f"pm-bulk port : {self.pm_bulk_port}")
            else:
                logging.info(f"Exiting. Cannot get sftp server port. {self.pm_bulk_port}")
                sys.exit(1)
        except Exception as err:
            logging.error(f"Exception {cmd} ::: {str(err)}")

        # Get Internal IP From Worker Nodes
        cmd = """kubectl get nodes -o wide """
        try:
            count, error = self.subprocess_obj.execute_cmd(cmd)
            count = count.splitlines()
            for line in count:
                if "worker" in line:
                    self.internal_ip = line.split()[5]
                    logging.info(f"Internal_IP : {self.internal_ip}")
                    break
            if len(self.internal_ip) == 0:
                sys.exit(1)
        except Exception as err:
            logging.exception(f"Exception {cmd}")

        self.write_pod_status_kpi()

        file_paths = files_newer_that_mins(self.pm_files_local_dir, "*.xml", self.execution_period_mins)
        self.aggregate_pm_files_into_csv_file(csa, file_paths)
        self.write_pm_kpis(self.execution_period_mins)
