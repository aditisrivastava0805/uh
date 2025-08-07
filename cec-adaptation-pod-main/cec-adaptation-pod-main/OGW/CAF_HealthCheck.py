#!/usr/bin/python3

import sys
import time
import re
import os

import subprocess
from datetime import datetime, timedelta
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.process_check.ProcessCheck import ProcessCheck

pc = ProcessCheck(os.path.join("/", "tmp", os.path.basename(os.path.dirname(os.path.abspath(__file__))) + ".pid"))
pc.start()

currentDate = os.popen('TZ=":US/Central" date "+%Y%m%d_%H00"').read().rstrip()

yesterdayDate = datetime.now() - timedelta(days=1)
yesterdayDate = datetime.strftime(yesterdayDate, '%Y%m%d_%H00')
hostName = ''
nameSpace = ''
f = open("/home/ericuser/monitor/config", "r")
for line in f.readlines():
    x = re.match("hostName=(.+?)$", line)
    if x:
        hostName = x.group(1)
    y = re.match("alarmNameSpace=(.+?)$", line)
    if y:
        nameSpace = y.group(1)

logName = '/mount/volumes/script/OGW/' + str(hostName) + "_" + str(currentDate) + '.log'
deletedLog = '/mount/volumes/script/OGW/' + str(hostName) + "_" + str(yesterdayDate) + '.log'

print('\nRemoving Old Log File: ' + deletedLog + '\n')
currentCommand = 'rm ' + deletedLog;
os.system(currentCommand)
print('New Log Name: ' + logName + '\n')

# Open log file
logFile = open(logName, "w")

currentCommand = 'kubectl version';
commandResult = os.popen(currentCommand).read()
logFile.write("COMMAND: " + currentCommand + "\n")
logFile.write(commandResult)
currentCommand = 'kubectl get nodes';
commandResult = os.popen(currentCommand).read()
logFile.write("COMMAND: " + currentCommand + "\n")
logFile.write(commandResult)
currentCommand = 'kubectl top nodes';
commandResult = os.popen(currentCommand).read()
logFile.write("COMMAND: " + currentCommand + "\n")
logFile.write(commandResult)
currentCommand = 'kubectl get pods -n ' + str(nameSpace) + ' | grep -i evicted';
commandResult = os.popen(currentCommand).read()
logFile.write("COMMAND: " + currentCommand + "\n")
logFile.write(commandResult)
currentCommand = 'kubectl get pods -n ' + str(nameSpace) + ' | grep -i \'0/\' | grep -iv \'completed\'';
commandResult = os.popen(currentCommand).read()
logFile.write("COMMAND: " + currentCommand + "\n")
logFile.write(commandResult)
currentCommand = 'kubectl get pvc -n ' + str(nameSpace);
commandResult = os.popen(currentCommand).read()
logFile.write("COMMAND: " + currentCommand + "\n")
logFile.write(commandResult)
currentCommand = 'kubectl -n ' + str(
    nameSpace) + ' get pods -l app.kubernetes.io/name=eric-fh-alarm-handler -o jsonpath="{.items[0].metadata.name}" |  xargs -I{} kubectl -n ' + str(
    nameSpace) + ' exec -it {} -- ah_alarm_list.sh';
commandResult = os.popen(currentCommand).read()
logFile.write("COMMAND: " + currentCommand + "\n")
logFile.write(commandResult)
diameterLbPodNames = f"kubectl -n {str(nameSpace)} get pods -l app.kubernetes.io/name=eric-bss-cha-diameter-lb --no-headers | awk -F' ' '{{print $1}}'"
diameterLbPodNamesResult = os.popen(diameterLbPodNames).readlines()
for diameterLbPodName in diameterLbPodNamesResult:
    diameterLbPodName = str(diameterLbPodName).strip() if diameterLbPodName else ""
    currentCommand = f"""kubectl -n {str(nameSpace)} exec -it {str(diameterLbPodName)} -- /bin/bash -c "client" """
    commandResult = subprocess.Popen(currentCommand, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
    time.sleep(3)
    commandResult.stdin.write(b'peerlist\n')
    time.sleep(2)
    peerlist, err = commandResult.communicate()
    peerlist = peerlist.decode('utf-8')
    logFile.write("COMMAND: " + currentCommand + "\n")
    logFile.write(peerlist)
for diameterLbPodName in diameterLbPodNamesResult:
    diameterLbPodName = str(diameterLbPodName).strip() if diameterLbPodName else ""
    currentCommand = f"""kubectl -n {str(nameSpace)} exec -it {str(diameterLbPodName)} -- /bin/bash -c "client" """
    commandResult = subprocess.Popen(currentCommand, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
    time.sleep(3)
    commandResult.stdin.write(b'externalratingpeerlist\n')
    time.sleep(2)
    peerlist, err = commandResult.communicate()
    peerlist = peerlist.decode('utf-8')
    logFile.write("COMMAND: " + currentCommand + "\n")
    logFile.write(peerlist)
logFile.write("CAF Data Collection Completed\n")

# Close log file
logFile.close()

pc.stop()
