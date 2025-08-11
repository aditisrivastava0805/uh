#!/usr/bin/python

import json
# import requests
from time import sleep
import os, fnmatch
import glob
import sys, getopt
import subprocess
import socket
import random
from datetime import datetime


#from kafka import KafkaProducer
from kafka import SimpleProducer, KafkaClient

#kafka_ip_pol = "10.253.130.118,10.253.130.114,10.253.130.117,10.253.130.116,10.253.130.119"
#kafka_ip_titan = "10.255.129.151,10.255.129.152,10.255.129.147,10.255.129.148,10.255.129.149"
kafka_ip_pol = "5.232.36.216"
kafka_ip_titan = "5.232.36.216"

#kafka_port = "9093"
kafka_port = "9092"

message_topic = "validation.svc_ss_incoming_msgs"
#message_topic = "test-topic"

def publish_message(client, value):
    status = "SUCCESS"
    try:
        client.send_messages(message_topic,value.encode("UTF-8"))
        print("Message published successfully.")

    except Exception as e:
        print("Exception in publishing message")
        print(str(e))
        status = "FAIL"

    return status


def create_kafka_client(in_ip):
    client = None
    try:
        kafka = KafkaClient(in_ip+":"+kafka_port)
        client = SimpleProducer(kafka)
    except Exception as e:
        print("Exception connecting Kafka")
        print(str(e))

    finally:
        return client


def executecmd(cmd):
    result = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result.wait()
    return result



if __name__ == '__main__':

    try:
       opts, args = getopt.getopt(sys.argv[1:],"d:p:")
    except getopt.GetoptError:
       print "usage:  kafka_sdpkpi.py -d -p"
       sys.exit(2)
    for opt, arg in opts:
       if opt == '-h':
          print "usage:  kafka_sdpkpi.py -d -p"
          sys.exit()
       elif opt == "-d":
          kafka_ip = arg
       elif opt == "-p":
          kafka_port = arg

    #print kafka_ip, "  ", kafka_port

    # read all files
    filename_mask = "*.txt"
    files = []
    json_messages = []
    host_name = socket.gethostname()
    ips_pol = kafka_ip_pol.split(',')
    ips_titan = kafka_ip_titan.split(',')

    print(ips_pol)
    print(ips_titan)

    kafka_client_pol = []
    kafka_client_titan = []


    src_file = '/home/resolveSDP/output/%s_KPI.txt' % host_name
    files.append(src_file)

    for file in files:
       with open(file) as fp:
          lines = fp.readlines()

       for line in lines:
          #print line
          fields = line.rstrip().split(",")
          kpi_source = '%s > %s > %s' % (host_name,"KPI_SDP.py", fields[5]) 
          kpi_info = host_name + ' ' + socket.gethostbyname(host_name)

          kpi_result = "UNDEFINED"
          kpi_value = fields[2].strip()
          if len(kpi_value) == 0 or kpi_value == "NODATA":
             kpi_result = "NO-DATA"
             kpi_value = "0"

          message = { 
                "category": "UNDEFINED", 
                "config_item": host_name,
                "kpi_info": kpi_info,
                "kpi_last_updated_date": fields[4],
                "kpi_name": fields[1],
                "kpi_result": kpi_result,
                "kpi_source": kpi_source,
                "kpi_value": kpi_value,
                "platform": "UNDEFINED",
                "source_owner": "Tier2_CC",
                "src_modified_dt": int(fields[6]),
                "local_modified_dt": int(fields[7]),
                "ref_id": str(random.randint(1,10000000))
          }

          json_messages.append(json.dumps(message))

          #message['ref_id'] = str(random.randint(1,10000000))
          #json_messages_titan.append(json.dumps(message))


    #print json_messages
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    archiveFile="/home/resolveSDP/archive/%s_KPI.status.%s" % (host_name,timestamp)
    fileWriter = open(archiveFile, "w")

    if len(json_messages) > 0:
        for ip in ips_pol:
            client_pol = create_kafka_client(ip)
            kafka_client_pol.append(client_pol)

        for ip in ips_titan:
            #kafka_ip = ip
            client_titan = create_kafka_client(ip)
            kafka_client_titan.append(client_titan)

        final_status = 'SUCCESS'
        for message in json_messages:
            final_status = 'SUCCESS'
            print message
            result = ''

            # Polaris
            for client in kafka_client_pol:
               if not client is None:
                   result = publish_message(client, message)
                   if 'FAIL' == result:
                       print("Polaris FAIL")
                       final_status = 'FAIL'
                   else:
                       print("Polaris successful")
               else:
                   print("Polaris FAIL")
                   final_status = 'FAIL'

            # Titan
            for client in kafka_client_titan:
               if not client is None:
                   result = publish_message(client, message)
                   if 'FAIL' == result:
                       print("Titan FAIL")
                       final_status = 'FAIL'
                   else:
                       print("Titan successful")
               else:
                   print("Titan FAIL")
                   final_status = 'FAIL'


            fileWriter.write(str(message) + ".%s\n" % final_status)

        for client in kafka_client_pol:
           if client is not None:
               client.stop()

        for client in kafka_client_titan:
           if client is not None:
               client.stop()

    fileWriter.close()
    subprocess.call("mv %s /home/resolveSDP/archive/%s_KPI.txt.%s" % (src_file,host_name,timestamp), shell=True)
[root@VCCSDPBL04A resolveSDP]#
