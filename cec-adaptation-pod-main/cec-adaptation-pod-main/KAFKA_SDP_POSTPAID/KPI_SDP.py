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


class KPI_SDP:
    def __init__(self, hostname: str, namespace: str, pod: str, script_dir: str, output_dir: str, archive_dir: str,
                 log_dir: str, pod_container: str):
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
            # self._logger.info(f"update_command() ::: Command - {str(command)}")
            if "{" in command or "}" in command:
                command = command.replace("{", "{{")
                command = command.replace("}", "}}")
            if command_type == "bash":
                command = f"""kubectl exec -it -n {self.namespace} {sdp} -c {self.pod_container} -- bash -c '{command}' """
            else:
                command = f"""kubectl exec -it -n {self.namespace} {sdp} -c {self.pod_container} -- {command}"""
            # self._logger.info(f"update_command() ::: Command after conversion - {str(command)}")
            output, error = self.subprocess_obj.execute_cmd(command)
            self._logger.info(f"{sdp}: Command: {str(command)}, Output: {str(output)}, Error: {str(error)}")
            # output = self.execute_cmd(command)
            return output, error
        except Exception as err:
            self._logger.error("Exception in update_command ::: " + str(err))

    def GetCIP_PeerStat(self, sdp, thread_counter, user, passwd, host):
        try:
            # CIP/Member1
            cmd = f"""FDSRequestSender -U {user} -P {passwd} -h {host} << END > {str(thread_counter)}0_log
<?xml version='1.0' encoding='ISO-8859-1' standalone='no'?>
<Request Operation="PeerStatus" SessionId="R9bx5gg8" Origin="GUI" MO="CIP/Member1"></Request>
END"""

            output, error = self.update_command(sdp, cmd, 'bash')
            self._logger.info("Executed : " + str(cmd) + "Output is : " + str(output))

            cmd = f"""cat {str(thread_counter)}0_log | egrep "PeerInformation|Status" | sed -e '/<Peer/,/\/Peer/s/<PeerInformation fqdn="//g' -e 's/">//g' -e "s/<Status>//g" -e "s/<\/Status>//g" -e "s/<\/PeerInformation>//g" """
            output_mem1, error = self.update_command(sdp, cmd)
            self._logger.info("Executed : " + str(cmd) + "Output is : " + str(output_mem1))

            # CIP/Member2
            cmd = f"""FDSRequestSender -U {user} -P {passwd} -h {host} << END > {str(thread_counter)}0_log
<?xml version='1.0' encoding='ISO-8859-1' standalone='no'?>
<Request Operation="PeerStatus" SessionId="R9bx5gg8" Origin="GUI" MO="CIP/Member2"></Request>
END"""
            output, error = self.update_command(sdp, cmd, 'bash')
            self._logger.info("Executed : " + str(cmd) + "Output is : " + str(output))

            cmd = f"""cat {str(thread_counter)}0_log | egrep "PeerInformation|Status" | sed -e '/<Peer/,/\/Peer/s/<PeerInformation fqdn="//g' -e 's/">//g' -e "s/<Status>//g" -e "s/<\/Status>//g" -e "s/<\/PeerInformation>//g" """
            output_mem2, error = self.update_command(sdp, cmd)
            self._logger.info("Executed : " + str(cmd) + "Output is : " + str(output_mem2))

            return output_mem1, output_mem2
        except Exception as err:
            self._logger.error("Error in GetCIP_PeerStat() ::: " + str(err))

    def GetDCIP_PeerStat(self, sdp, thread_counter, user, passwd, host):
        try:
            # DCIP/Member1
            cmd = f"""FDSRequestSender -U {user} -P {passwd} -h {host} << END > {str(thread_counter)}0_log
<?xml version='1.0' encoding='ISO-8859-1' standalone='no'?>
<Request Operation="PeerStatus" SessionId="R9bx5gg8" Origin="GUI" MO="DCIP/Member1"></Request>
END"""

            output, error = self.update_command(sdp, cmd, 'bash')
            self._logger.info("Executed : " + str(cmd) + "Output is : " + str(output))

            cmd = f"""cat {str(thread_counter)}0_log | egrep "PeerInformation|Status" | sed -e '/<Peer/,/\/Peer/s/<PeerInformation fqdn="//g' -e 's/">//g' -e "s/<Status>//g" -e "s/<\/Status>//g" -e "s/<\/PeerInformation>//g" """
            output_mem1, error = self.update_command(sdp, cmd)
            self._logger.info("Executed : " + str(cmd) + "Output is : " + str(output_mem1))

            # DCIP/Member2
            cmd = f"""FDSRequestSender -U {user} -P {passwd} -h {host} << END > {str(thread_counter)}0_log
<?xml version='1.0' encoding='ISO-8859-1' standalone='no'?>
<Request Operation="PeerStatus" SessionId="R9bx5gg8" Origin="GUI" MO="DCIP/Member2"></Request>
END"""
            output, error = self.update_command(sdp, cmd, 'bash')
            self._logger.info("Executed : " + str(cmd) + "Output is : " + str(output))

            cmd = f"""cat {str(thread_counter)}0_log | egrep "PeerInformation|Status" | sed -e '/<Peer/,/\/Peer/s/<PeerInformation fqdn="//g' -e 's/">//g' -e "s/<Status>//g" -e "s/<\/Status>//g" -e "s/<\/PeerInformation>//g" """
            output_mem2, error = self.update_command(sdp, cmd)
            self._logger.info("Executed : " + str(cmd) + "Output is : " + str(output_mem2))

            return output_mem1, output_mem2
        except Exception as err:
            self._logger.error("Error in GetDCIP_PeerStat() ::: " + str(err))

    @staticmethod
    def add_kafka_kpi(kafka_data_source_builder: KafkaDataSourceBuilder, kpi: str, value: str):
        if value and value != " " and value != "None":
            value = value
            kpi_result = "UNDEFINED"
        else:
            value = "0"
            kpi_result = "NO-DATA"

        kafka_data_source_builder.add_data_record([kpi.upper(), value, kpi_result])

    def set_message(self, data_source_hostname, data_source_ip, kafka_data_source_builder: KafkaDataSourceBuilder):
        kafka_data_source_builder.set_message_field("kpi_last_updated_date", self.todayUTC)
        kafka_data_source_builder.set_message_field("kpi_source",
                                                    f'{data_source_hostname} > KPI_SDP.py > {self.utcTimestamp}')
        kafka_data_source_builder.set_message_field("config_item", data_source_hostname)
        kafka_data_source_builder.set_message_field("kpi_info", f'{data_source_hostname} {data_source_ip}')
        kafka_data_source_builder.set_message_field("src_modified_dt", self.todayUTCMilli)
        kafka_data_source_builder.set_message_field("local_modified_dt", self.localNowMilli)

    def main(self, args_val):
        cmd = ""
        sdp = ""
        try:
            sdp = args_val[0]
            thread_counter = args_val[1]
            kafka_data_source_builder = args_val[2]
            self._logger.info(f" {str(args_val)} and {str(thread_counter)}")
            # Get hostname of sdp pod
            try:
                cmd = """env | grep "HOSTNAME=" | awk -F'=' '{print $2}'"""
                hostname, error = self.update_command(sdp, cmd)
                if hostname:
                    data_source_hostname = hostname.strip()
                    cmd = f"""grep {data_source_hostname} /etc/hosts | awk -F' ' '{{print $1}}' """
                    host_by_name, error = self.update_command(sdp, cmd)
                    data_source_ip = host_by_name.strip()
                else:
                    data_source_hostname = str(sdp)
                    data_source_ip = "NOT AVAILABLE"
                self.set_message(str(data_source_hostname).upper(), data_source_ip, kafka_data_source_builder)
                self._logger.info(f"Hostname ::: {str(data_source_hostname)} and {str(data_source_ip)}")
            except Exception as err:
                self._logger.error(f"Exception {str(sdp)} ::: {str(err)}")

            # CIP_LINK_DOWN_COUNT
            count = 0
            member1, member2 = self.GetCIP_PeerStat(sdp, thread_counter, "metrica", "met123", "localhost")
            if member1 is not None:
                for line in member1.splitlines():
                    val = line.strip()
                    self._logger.info(f"CIP_LINK_DOWN_COUNT : Value : {str(val)}")
                    try:
                        if val != "":
                            if "DISCONNECTED" in val:
                                count += 1
                    except IndexError:
                        pass
                self.add_kafka_kpi(kafka_data_source_builder, "CIP_LINK_DOWN_COUNT", str(count))
            else:
                self.add_kafka_kpi(kafka_data_source_builder, "CIP_LINK_DOWN_COUNT", "0")

            # DATABASE_LOCK_ERRORS
            cmd = """grep -i "DATABASE_LOCK_CONTENTION" /var/opt/fds/logs/cPSCTrafficHandler.log.0 | grep "`date +"%Y%m%d"`"|awk -F" " -v y=`date -d '15 min ago' +"%H%M%S"` '{split($2,a,":"); x=a[1]a[2]a[3] ;if(x > y ){print $0}}'| wc -l """
            count, error = self.update_command(sdp, cmd)
            count = str(count).strip() if count else None
            self._logger.info(f'DATABASE_LOCK_ERRORS: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "DATABASE_LOCK_ERRORS", str(count))

            # DATABASE_LOCK_TIMEOUTS
            cmd = """grep -i "timeout event due to account lock" /var/opt/fds/logs/EventLogFile.txt.0 | grep "`date +"%Y%m%d"`"|awk -F" " -v y=`date -d '15 min ago' +"%H%M%S"` '{split($2,a,":"); x=a[1]a[2]a[3] ;if(x > y ){print $0}}' | wc -l """
            count, error = self.update_command(sdp, cmd)
            count = str(count).strip() if count else None
            self._logger.info(f'DATABASE_LOCK_TIMEOUTS: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "DATABASE_LOCK_TIMEOUTS", str(count))

            # DCIP_LINK_DOWN_COUNT
            count = 0
            thread_counter = int(thread_counter) + 100
            member1, member2 = self.GetDCIP_PeerStat(sdp, thread_counter, "metrica", "met123", "localhost")
            if member1 is not None:
                for line in member1.splitlines():
                    val = line.strip()
                    self._logger.info(f"DCIP_LINK_DOWN_COUNT : Value : {str(val)}")
                    try:
                        if val != "":
                            if "DISCONNECTED" in val:
                                count += 1
                    except IndexError:
                        pass
                self.add_kafka_kpi(kafka_data_source_builder, "DCIP_LINK_DOWN_COUNT", str(count))
            else:
                self.add_kafka_kpi(kafka_data_source_builder, "DCIP_LINK_DOWN_COUNT", "0")

            # DIAMETER TRAFFIC FILENAME
            cmd = """ls /tmp/ | grep "PSC-CIPDiameter_8.1_" | grep "_1.stat.0" | grep -v lck """
            filename, error = self.update_command(sdp, cmd)
            filename = str(filename).strip() if filename else None

            if filename is not None:
                # DIAMETER_REJECT_FAIL
                cmd = f"""grep Diameter /tmp/{filename} |tail -90 | awk -F" " '{{fail += $4; rej += $6}} END {{s = fail + rej; print s}}' """
                count, error = self.update_command(sdp, cmd)
                self._logger.info(f"DIAMETER_REJECT_FAIL ::: {str(count)} ::: {str(error)}")
                count = str(count).strip() if count else None
                self.add_kafka_kpi(kafka_data_source_builder, "DIAMETER_REJECT_FAIL", str(count))

                # DIAMETER_TRAFFIC
                cmd = f"""grep Diameter /tmp/{str(filename)} |tail -90 | awk -F" " '{{s += $3}} END {{print s}}' """
                count, error = self.update_command(sdp, cmd)
                count = str(count).strip() if count else None
                self._logger.info(f'DIAMETER_TRAFFIC: {str(count)}')
                self.add_kafka_kpi(kafka_data_source_builder, "DIAMETER_TRAFFIC", str(count))

                # DIRECTDEBIT_REJECT_FAIL
                cmd = f"""grep DirectDebit /tmp/{str(filename)} |tail -90 | awk -F" " '{{fail += $3; rej += $5}} END {{s = fail + rej; print s}}' """
                count, error = self.update_command(sdp, cmd)
                count = str(count).strip() if count else None
                self._logger.info(f'DIRECTDEBIT_REJECT_FAIL: {str(count)}')
                self.add_kafka_kpi(kafka_data_source_builder, "DIRECTDEBIT_REJECT_FAIL", str(count))

                # DIRECT_DEBIT_TRAFFIC
                cmd = f"""grep  DirectDebit /tmp/{str(filename)} |tail -90 | awk -F" " '{{s += $2}} END {{print s}}' """
                count, error = self.update_command(sdp, cmd)
                count = str(count).strip() if count else None
                self._logger.info(f'DIRECT_DEBIT_TRAFFIC: {str(count)}')
                self.add_kafka_kpi(kafka_data_source_builder, "DIRECT_DEBIT_TRAFFIC", str(count))
            else:
                self._logger.info(f'DIAMETER_REJECT_FAIL: No File Found')
                self._logger.info(f'DIAMETER_TRAFFIC: No File Found')
                self._logger.info(f'DIRECTDEBIT_REJECT_FAIL: No File Found')
                self._logger.info(f'DIRECT_DEBIT_TRAFFIC: No File Found')
                self.add_kafka_kpi(kafka_data_source_builder, "DIAMETER_REJECT_FAIL", "None")
                self.add_kafka_kpi(kafka_data_source_builder, "DIAMETER_TRAFFIC", "None")
                self.add_kafka_kpi(kafka_data_source_builder, "DIRECTDEBIT_REJECT_FAIL", "None")
                self.add_kafka_kpi(kafka_data_source_builder, "DIRECT_DEBIT_TRAFFIC", "None")

            # DISK_AWAIT_TIME_SAR
            cmd = """sar -d | grep -v 'Average' | tail -50 | awk -F " " '{if( $9 * 100 > 1000) s += 1} END { print s }' """
            count, error = self.update_command(sdp, cmd)
            count = str(count).strip() if count else None
            self._logger.info(f'DISK_AWAIT_TIME_SAR: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "DISK_AWAIT_TIME_SAR", str(count))

            # DISK_USAGE_PCT
            cmd = """df -kh | egrep 'root|/var' | awk -F " " 'BEGIN {result = 0} {gsub("%", "", $5);if($5*1 <= 70 && result == 0) {result = 0} else if($5*1 > 70 && $5*1 <= 80 && result == 0) {result = 1} else if($5*1 > 80)  result = 2 }  END { print result }' """
            count, error = self.update_command(sdp, cmd)
            count = str(count).strip() if count else None
            self._logger.info(f'DISK_USAGE_PCT: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "DISK_USAGE_PCT", str(count))

            # FAILED_LICENSES_CHECK_STATUS
            cmd = """echo "<Request Operation=Get MO=LicensesInfo></Request>" | FDSRequestSender  | grep -q LICENSE_SERVER_OK && echo "0" || echo "1" """
            count, error = self.update_command(sdp, cmd, "bash")
            count = str(count).strip() if count else None
            self._logger.info(f'FAILED_LICENSES_CHECK_STATUS: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "FAILED_LICENSES_CHECK_STATUS", str(count))

            # FDS_CLUSTER_DOWN_COUNT
            cmd = """/opt/EABfds/bin/FDSCluster info |grep "Status:    Running" | wc -l """
            count, error = self.update_command(sdp, cmd)
            count = str(count).strip() if count else None
            self._logger.info(f"FDS_CLUSTER_DOWN_COUNT ::: {str(count)}")
            if count is None:
                self.add_kafka_kpi(kafka_data_source_builder, "FDS_CLUSTER_DOWN_COUNT", "None")
            elif count == "0":
                self.add_kafka_kpi(kafka_data_source_builder, "FDS_CLUSTER_DOWN_COUNT", "1")
            else:
                self.add_kafka_kpi(kafka_data_source_builder, "FDS_CLUSTER_DOWN_COUNT", "0")

            # PROVISIONED_TRAFFIC CHECK CONDITION
            p = """ifconfig -a | grep :1: | wc -l """
            ifConfig_count, error = self.update_command(sdp, p)
            ifConfig_count = str(ifConfig_count).strip() if ifConfig_count else "0"

            if ifConfig_count == "1":
                cmd = f"""ls /tmp/ | grep PSC-PPASInterface | grep .stat.0 """
                prov_filename, error = self.update_command(sdp, cmd)
                prov_filename = str(prov_filename).strip() if prov_filename else None

                if prov_filename is not None:
                    # INCOMING_PROVISIONED_TRAFFIC
                    cmd = f"""grep Total /tmp/{str(prov_filename)} | tail -90 | awk -F " " '{{ s += $3}} END {{print s}}' """
                    count, error = self.update_command(sdp, cmd)
                    count = str(count).strip() if count else None
                    self._logger.info(f'INCOMING_PROVISIONED_TRAFFIC: {str(count)}')
                    self.add_kafka_kpi(kafka_data_source_builder, "INCOMING_PROVISIONED_TRAFFIC", str(count))

                    # PROVISIONED_TRAFFIC_FAILED
                    cmd = f"""grep Total /tmp/{prov_filename} |tail -90 |awk -F " " '{{ s += $4}} END {{print s}}' """
                    count, error = self.update_command(sdp, cmd)
                    count = str(count).strip() if count else None
                    self._logger.info(f'PROVISIONED_TRAFFIC_FAILED: {str(count)}')
                    self.add_kafka_kpi(kafka_data_source_builder, "PROVISIONED_TRAFFIC_FAILED", str(count))

                    # PROVISIONED_TRAFFIC_REJECT
                    cmd = f"""grep Total /tmp/{prov_filename} |tail -90 |awk -F " " '{{ s += $5}} END {{print s}}' """
                    count, error = self.update_command(sdp, cmd)
                    count = str(count).strip() if count else None
                    self._logger.info(f'PROVISIONED_TRAFFIC_REJECT: {str(count)}')
                    self.add_kafka_kpi(kafka_data_source_builder, "PROVISIONED_TRAFFIC_REJECT", str(count))
                else:
                    self._logger.info(f'INCOMING_PROVISIONED_TRAFFIC: No File Found')
                    self._logger.info(f'PROVISIONED_TRAFFIC_FAILED: No File Found')
                    self._logger.info(f'PROVISIONED_TRAFFIC_REJECT: No File Found')
                    self.add_kafka_kpi(kafka_data_source_builder, "INCOMING_PROVISIONED_TRAFFIC", "None")
                    self.add_kafka_kpi(kafka_data_source_builder, "PROVISIONED_TRAFFIC_FAILED", "None")
                    self.add_kafka_kpi(kafka_data_source_builder, "PROVISIONED_TRAFFIC_REJECT", "None")

            # LICENSE_MANAGER_CHECK_STATUS
            cmd = """grep LicenseStatus /home/resolveSDP/lsmon.log  | grep -v LICENSE_ACTIVE | wc -l """
            count, error = self.update_command(sdp, cmd)
            count = str(count).strip() if count else None
            self._logger.info(f'LICENSE_MANAGER_CHECK_STATUS: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "LICENSE_MANAGER_CHECK_STATUS", str(count))

            # PROCESSES_DOWN_COUNT
            cmd = """/opt/EABfds/bin/FDSpgrep -l -C | wc -l """
            count, error = self.update_command(sdp, cmd)
            count = str(count).strip() if count else None
            self._logger.info(f'PROCESSES_DOWN_COUNT: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "PROCESSES_DOWN_COUNT", str(count))

            # REJECTION_COUNT_FROM_LOGS
            cmd = """grep -i "reject" /var/opt/fds/logs/cPSCCIPDiameter.log.0 | grep "`date +"%Y%m%d"`"|awk -F" " -v y=`date -d '15 min ago' +"%H%M%S"` '{split($2,a,":"); x=a[1]a[2]a[3] ;if(x > y ){print $0}}' | wc -l """
            count, error = self.update_command(sdp, cmd)
            count = str(count).strip() if count else None
            self._logger.info(f'REJECTION_COUNT_FROM_LOGS: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "REJECTION_COUNT_FROM_LOGS", str(count))

            # REPLICATION_LOG_COUNT
            cmd = """ls -lrth /var/opt/fds/TT/db-log/sdp_db/ | grep "sdp.*" |wc -l  """
            count, error = self.update_command(sdp, cmd)
            count = str(count).strip() if count else None
            self._logger.info(f'REPLICATION_LOG_COUNT: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "REPLICATION_LOG_COUNT", str(count))

            # REPLICATION_STATUS
            log_file = str(self.script_dir) + "/" + str(sdp) + "_replication_logfile.log"
            cmd = f"""/opt/sdp/TTMonitor/bin/TTRepCheck > {log_file}"""
            count, error = self.update_command(sdp, cmd)
            exists = os.path.isfile(log_file)
            if exists:
                p = f""" cut -d" " -f1 {log_file} | sort | uniq  """
                log_date, error = self.subprocess_obj.execute_cmd(p)
                if self.todayYMD not in log_date and self.yesterdayYMD not in log_date:
                    self._logger.info('REPLICATION_STATUS: ')
                    self.add_kafka_kpi(kafka_data_source_builder, "REPLICATION_STATUS", "")
                else:
                    p = f""" egrep "ERROR:|WARNING" {log_file} """
                    logfiles_line, error = self.subprocess_obj.execute_cmd(p)
                    if logfiles_line is None:
                        self._logger.info('REPLICATION_STATUS: 0')
                        self.add_kafka_kpi(kafka_data_source_builder, "REPLICATION_STATUS", "0")
                    else:
                        warn_string = 'WARNING'
                        error_string = 'ERROR:'
                        for line in logfiles_line.splitlines():
                            cols = line.split()
                            status = str(cols[2])
                            if status == warn_string:
                                self._logger.info(f'REPLICATION_STATUS: WARNING {str(cols[3])}')
                                self.add_kafka_kpi(kafka_data_source_builder, "REPLICATION_STATUS", str(cols[3]))
                                break
            else:
                self._logger.info(f'REPLICATION_STATUS: NO LOGS - 0')
                self.add_kafka_kpi(kafka_data_source_builder, "REPLICATION_STATUS", "0")
            os.remove(log_file)

            # SCHEDULER_FILE_SENT_FAILED
            cmd = """ls /var/opt/fds/CDR/scheduledJobUnsentCdr | wc -l  """
            count, error = self.update_command(sdp, cmd)
            count = str(count).strip() if count else None
            self._logger.info(f'SCHEDULER_FILE_SENT_FAILED: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "SCHEDULER_FILE_SENT_FAILED", str(count))

            # TNP_FILE_SENT_FAILED
            cmd = """ls /var/opt/fds/FI/BN/failedtosendexternal | wc -l  """
            count, error = self.update_command(sdp, cmd)
            count = str(count).strip() if count else None
            self._logger.info(f'TNP_FILE_SENT_FAILED: {str(count)}')
            self.add_kafka_kpi(kafka_data_source_builder, "TNP_FILE_SENT_FAILED", str(count))

            # VOICE_FI_FR_FILENAME
            cmd = """ls /tmp/ | grep "PSC-CIPDiameter_8.1_" | grep "_1.stat.0" | grep -v lck """
            voice_filename, error = self.update_command(sdp, cmd)
            voice_filename = str(voice_filename).strip() if voice_filename else None

            if voice_filename is not None:
                # VOICE_FI_FR_REJECT_FAIL
                cmd = f"""egrep 'FirstInterrogation|FinalReport' /tmp/{voice_filename} | tail -90 | awk -F" " '{{s += $3 + $5}} END {{print s}}' """
                count, error = self.update_command(sdp, cmd)
                count = str(count).strip() if count else None
                self._logger.info(f'VOICE_FI_FR_REJECT_FAIL: {str(count)}')
                self.add_kafka_kpi(kafka_data_source_builder, "VOICE_FI_FR_REJECT_FAIL", str(count))

                # VOICE_TRAFFIC_FI
                cmd = f"""grep 'FirstInterrogation' /tmp/{str(voice_filename)} | tail -90 | awk -F" " '{{s += $2}} END {{print s}}' """
                count, error = self.update_command(sdp, cmd)
                count = str(count).strip() if count else None
                self._logger.info(f'VOICE_TRAFFIC_FI: {str(count)}')
                self.add_kafka_kpi(kafka_data_source_builder, "VOICE_TRAFFIC_FI", str(count))

                # VOICE_TRAFFIC_FR
                cmd = f"""grep 'FinalReport' /tmp/{str(voice_filename)} |tail -90| awk -F" " '{{s += $2}} END {{print s}}' """
                count, error = self.update_command(sdp, cmd)
                count = str(count).strip() if count else None
                self._logger.info(f'VOICE_TRAFFIC_FR: {str(count)}')
                self.add_kafka_kpi(kafka_data_source_builder, "VOICE_TRAFFIC_FR", str(count))
            else:
                self._logger.info(f'VOICE_FI_FR_REJECT_FAIL: {str(count)}')
                self._logger.info(f'VOICE_TRAFFIC_FI: {str(count)}')
                self._logger.info(f'VOICE_TRAFFIC_FR: {str(count)}')
                self.add_kafka_kpi(kafka_data_source_builder, "VOICE_FI_FR_REJECT_FAIL", "None")
                self.add_kafka_kpi(kafka_data_source_builder, "VOICE_TRAFFIC_FI", "None")
                self.add_kafka_kpi(kafka_data_source_builder, "VOICE_TRAFFIC_FR", "None")

            # TARIFF_UPDATE_FAILED
            try:
                cmd = """date +%Y%m%d """
                val, error = self.update_command(sdp, cmd)
                val = str(val).strip() if val else ""

                cmd = f"""grep {str(val)} /var/opt/fds/logs/cPSCConfigHandler.log.0 | grep "Failed to update" |wc -l """
                count1, error = self.update_command(sdp, cmd)
                count1 = str(count1).strip() if count1 else 0

                cmd = f"""grep {str(val)} /var/opt/fds/logs/cPSCConfigHandler.log.0 | grep "Probably a sync issue" |wc -l """
                count2, error = self.update_command(sdp, cmd)
                count2 = str(count2).strip() if count2 else 0

                count = int(count1) - int(count2)
                self._logger.info('TARIFF_UPDATE_FAILED: ')
                self.add_kafka_kpi(kafka_data_source_builder, "TARIFF_UPDATE_FAILED", str(count))
            except Exception as err:
                self._logger.error(f"Exception in TARIFF_UPDATE_FAILED ::: {str(err)}")
                self.add_kafka_kpi(kafka_data_source_builder, "TARIFF_UPDATE_FAILED", "None")

            # HIGH_SMS_COUNT
            cmd = """ls /tmp/ | grep "FSC-SMSInterface_8.0_" | grep "_.*.stat.0" | grep -v lck """
            filename, error = self.update_command(sdp, cmd)
            filename = str(filename).strip() if filename else None

            if filename is not None:
                cmd = f"""grep -i "Total" /tmp/{str(filename)} | tail | awk -F" " '{{sum+=$3}} END {{print sum+0" "}}' """
                count, error = self.update_command(sdp, cmd)
                count = str(count).strip() if count else None
                self._logger.info(f"HIGH_SMS_COUNT ::: {str(count)}")
                self.add_kafka_kpi(kafka_data_source_builder, "HIGH_SMS_COUNT", str(count))
            else:
                self._logger.info(f"HIGH_SMS_COUNT ::: No File Found")
                self.add_kafka_kpi(kafka_data_source_builder, "HIGH_SMS_COUNT", "None")

            self._logger.info("ALL KPI's Done")
        except Exception as err:
            self._logger.error(f"Exception in main ::: {str(cmd)} ::: {str(err)}")
