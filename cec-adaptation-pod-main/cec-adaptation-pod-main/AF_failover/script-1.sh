#!/bin/bash
#this script will check healthy state of AF
#external service taken as variable - 01_08_2023
#Changing main_check function logic,creating new function - backup - 08082023

curr_dir=$(pwd)
script_file=$(readlink -f "$0")
script_dir=$(dirname "$script_file")
date=$(date +%m_%d_%Y_%H%M%S)
logdir="$script_dir/log_AF_failover"
LogFile="$logdir/AF_failover_$date.log"
i_file="$script_dir/af_details.txt"
script_name=$(basename $0)



function countdown() {
    start="$(( $(date '+%s') + $1))"
    while [ $start -ge $(date +%s) ]; do
  time="$(( $start - $(date +%s) ))"
  printf '%s\r' "$(date -u -d "@$time" +%H:%M:%S)"
  sleep 0.1
    done
}

function logit {
  echo "[$(date)] ---- ${*} ----" | tee -a "${LogFile}"
  echo -e "\n" | tee -a "${LogFile}"
}

logit "script running from $script_dir"

#count of script running. should be changed during production test
count_script_running=$(ps -ef | grep "$script_name" | grep -v "grep" | wc -l)
if [ $count_script_running -gt "2" ]; then
  logit "already script is being executed,existing" 
  exit 1
fi

function cmd {
  cmd="$*"
  echo "# ${cmd}" | tee -a "${LogFile}"
  eval "${cmd}" | tee -a "${LogFile}"
  rec=$?
  if [ $rec != 0 ]; then
  echo "$cmd failed with result code $rec" | tee -a "${LogFile}"
  fi
  echo -e "\n" | tee -a "${LogFile}"
}

#create log dir
if [ -d $logdir ];then
  logit "removing temprary files from $logdir"
  cmd "rm -rf $logdir/*.txt $logdir/*.yml $logdir/*.yaml"
  dire=$(ls -lrth $logdir | grep ^d | awk -F " " '{print $9}')
  for dire in $dire
    do
    cmd "rm -rf $logdir/$dire"
  done
else
  logit "creating $logdir"
  cmd "mkdir -p $logdir"
fi
echo -e "\n"

#check if input file present
if [ ! -f $i_file ]; then
  logit "itput file is not present in $script_dir"
  cmd "ls -lrth $i_file"
  exit 1
fi

#function cdd_handler {
#
#logit "checking for available CDD handler"
#CDD_handler_primary=$(cat $i_file | grep CDD_handler_primary | awk '{print $2}')
#CDD_handler_secondary=$(cat $i_file | grep CDD_handler_secondary | awk '{print $2}')
#
#curl -m 2 http://$CDD_handler_primary:8081 1>/dev/null
#if [ "$?" == "0" ]; then
#       logit "$CDD_handler_primary is reachable"
#       CDD_handler_IP=$(echo $CDD_handler_primary)
#else
#       curl -m 2 http://$CDD_handler_secondary:8081 1>/dev/null
#       if [ $? == "0" ]; then
#         CDD_handler_IP=$(echo $CDD_handler_secondary)
#         logit "$CDD_handler_secondary is reachable"
#       else
#         logit "Both primary & secondary CDD handler is not reachable"
#         exit 1
#       fi
#fi
#}

function validate_input {

  logit "Validating input file $i_file"

  #logit "checking externel service"
  ##cmd "curl http://10.194.80.122:8082/af_pod/status"
  #cmd "curl http://10.194.80.122:8082/af_pod/status > $logdir/ext_opt.txt"
  #cat $logdir/ext_opt.txt
  #
  mahcdnf=$(cat $i_file | grep mainAF | awk -F " " '{print $3}')
  pahcdnf=$(cat $i_file | grep passiveAF | awk -F " " '{print $3}')
  maasif=$(cat $i_file | grep mainAF | awk -F " " '{print $6}')
  paasif=$(cat $i_file | grep passiveAF | awk -F " " '{print $6}')
  ext_svc_url=$(cat $i_file | grep ext_svc_url | awk '{for(i=2; i<=NF; i++) print $i}')
  mafu=$(cat $i_file | grep mainAF | awk '{print $7}')
  pafu=$(cat $i_file | grep passiveAF | awk '{print $7}')
  ssh_main_AF () 
  {
    ssh -o StrictHostKeyChecking=no -q ec01afgeored@$maasif "$@"
  }
  ssh_pass_AF () 
  {
    ssh -o StrictHostKeyChecking=no -q ec01afgeored@$paasif "$@"
  }
  namespace=chf-ec-apps

  logit "checking if access servers are reachable"
  ssh_main_AF "hostname 1>/dev/null"
  if [ $? == 0 ]; then
    maasif_reach=$(echo 200)
    logit  "Main AF access server $maasif is reachable"
    k_ab_path_main_AF=$(ssh_main_AF "source .bash_profile && which kubectl")
    helm_ab_path_main_AF=$(ssh_main_AF "source .bash_profile && which helm")
    logit "checking if helm release present in $maasif"
    mahcdnf_actual=$(ssh_main_AF "$helm_ab_path_main_AF ls -a" | awk '{print $1}' |grep -w "^$mahcdnf\$")
    if [ "$mahcdnf_actual" == "$mahcdnf" ]; then
      logit "helm release $mahcdnf is present in $maasif"
      logit "Checking if main AF passive enabled set to no"
      pe_mainaf=$(ssh_main_AF "$helm_ab_path_main_AF get values -a $mahcdnf -o yaml" | grep -A1 "passiveMain:" | tail -1 | awk -F "\"" '{print $(NF -1)}')
      if [ $pe_mainaf == 'no' ]; then
        logit "main AF passive enabled status set to no"
        st_pe_mainaf=$(echo 0)
      elif [ $pe_mainaf == 'yes' ]; then
        logit "main AF passive enabled status set to yes"
        st_pe_mainaf=$(echo 111)
      else
        logit "main AF passive enabled status is undetermined"
        st_pe_mainaf=$(echo 500)
      fi
    else
      logit "helm release $mahcdnf is not present in $maasif"
      exit 1
    fi
    logit "checking OAM & Traffic IP's are correct for main AF in $i_file"
    matif=$(cat $i_file | grep mainAF | awk -F " " '{print $4}')
    maof=$(cat $i_file | grep mainAF | awk -F " " '{print $5}')
    c_maof=$(ssh_main_AF "$k_ab_path_main_AF get svc -n $namespace" | grep $mahcdnf | grep af-tcp-oam-0 | awk -F " " '{print $4}' )
    c_matif=$(ssh_main_AF "$k_ab_path_main_AF get svc -n $namespace" | grep $mahcdnf | grep af-tcp-traffic-0 | awk -F " " '{print $4}')
    if [ ! -z $c_maof ]; then
      if [[ "$c_maof" =~ ^(([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))\.){3}([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))$ ]]; then
        if [ $c_maof == $maof ]; then
          logit "main AF OAM IP $maof correct in $i_file"
        else
          logit "Correcting main AF OAM IP in $i_file"
          cmd "sed -i 's/$maof/$c_maof/g' $i_file"
        fi
      fi
    else
      logit "Unable to get main AF OAM IP in $maasif"
    fi
    if [ ! -z $c_matif ]; then
      if [[ "$c_matif" =~ ^(([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))\.){3}([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))$ ]]; then
        if [ $c_matif == $matif ]; then
          logit "main AF traffic IP $matif correct in $i_file"
        else
          logit "Correcting main AF traffic IP in $i_file"
          cmd "sed -i 's/$matif/$c_matif/g' $i_file"
        fi
      fi
    else
      logit "Unable to get main AF traffic IP in $maasif"
    fi
  else
    logit "Main AF access server $maasif is not reachable"
    logit "checking externel service"
    #external service taken as variable in input file
    cmd "for i in $ext_svc_url; do curl $i; done > $logdir/ext_opt.txt"
    cat $logdir/ext_opt.txt
    s_mahcdnf=$(cat $logdir/ext_opt.txt | awk -F '[][]' '{print $2}' | tr "," "\n" | grep Role | cut -d: -f2- | sed 's/[{,},"]//g'| grep "$mahcdnf:" | awk -F ":" '{print $2}')
    s_pahcdnf=$(cat $logdir/ext_opt.txt | awk -F '[][]' '{print $2}' | tr "," "\n" | grep Role | cut -d: -f2- | sed 's/[{,},"]//g'| grep "$pahcdnf:" | awk -F ":" '{print $2}')


    if [[ $s_mahcdnf == 'active' && $s_pahcdnf == 'standby' ]]; then
      logit "main AF & passive AF entry in $i_file found OK"
    elif [[ $s_mahcdnf == 'standby' && $s_pahcdnf == 'active' ]]; then
      logit "input file found not OK"
      logit "Changing input file"
      cmd "sed -i 's/mainAF/mainAF_old/g' $i_file"
      cmd "sed -i 's/passiveAF/mainAF_new/g' $i_file"
      cmd "sed -i 's/mainAF_old/passiveAF/g' $i_file"
      cmd "sed -i 's/mainAF_new/mainAF/g' $i_file"
      logit "Rerun the script"
      exit 1
    else
      logit "Curl command not working,intervene manually"
      #ccnw=curl command not working
      ccnw=$(echo 200)
      #exit 1
    fi
    maasif_reach=$(echo 500)
    #exit 1
  fi

  ssh_pass_AF "hostname 1>/dev/null"
  if [ $? == 0 ]; then
    paasif_reach=$(echo 200)
    logit "Passive AF access server $paasif is reachable"
    k_ab_path_passive_AF=$(ssh_pass_AF "source .bash_profile && which kubectl")
    helm_ab_path_passive_AF=$(ssh_pass_AF "source .bash_profile && which helm")
    logit "checking if helm release present in $paasif"
    pahcdnf_actual=$(ssh -o StrictHostKeyChecking=no -q ec01afgeored@$paasif "$helm_ab_path_passive_AF ls -a" | awk '{print $1}'| grep -w "^$pahcdnf\$")
    if [ $pahcdnf_actual == $pahcdnf ]; then
      logit "helm release $pahcdnf is present in $paasif"
      logit "Checking if passive AF passive enabled set to yes"
      pe_passiveaf=$(ssh_pass_AF "$helm_ab_path_passive_AF get values -a $pahcdnf -o yaml" | grep -A1 "passiveMain:" | tail -1 | awk -F "\"" '{print $(NF -1)}')
      if [ $pe_passiveaf == 'no' ]; then
        logit "Passive AF passive enabled status set to no"
        st_pe_passiveaf=$(echo 111)
      elif [ $pe_passiveaf == 'yes' ]; then
        logit "Passive AF passive enabled status set to yes"
        st_pe_passiveaf=$(echo 0)
      else
        logit "Passive AF passive enabled status is undetermined"
        st_pe_passiveaf=$(echo 500)
      fi
    else
      logit "helm release $pahcdnf is not present in $paasif"
      exit 1
    fi
    logit "checking OAM & Traffic IP's are correct for passive AF in $i_file"
    patif=$(cat $i_file | grep passiveAF | awk -F " " '{print $4}')
    paof=$(cat $i_file | grep passiveAF | awk -F " " '{print $5}')
    c_paof=$(ssh_pass_AF "$k_ab_path_passive_AF get svc -n $namespace" | grep $pahcdnf | grep af-tcp-oam-0 | awk -F " " '{print $4}')
    c_patif=$(ssh_pass_AF $k_ab_path_passive_AF get svc -n $namespace | grep $pahcdnf | grep af-tcp-traffic-0 | awk -F " " '{print $4}')
    if [ ! -z $c_paof ]; then
      if [[ "$c_paof" =~ ^(([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))\.){3}([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))$ ]]; then
        if [ $c_paof == $paof ]; then
          logit "passive AF OAM IP $paof correct in $i_file"
        else
          logit "Correcting passive AF OAM IP in $i_file"
          cmd "sed -i 's/$paof/$c_paof/g' $i_file"
        fi
      fi
    else
      logit "Unable to get passive AF OAM IP in $paasif"
      exit 1
    fi
    if [ ! -z $c_patif ]; then
      if [[ "$c_patif" =~ ^(([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))\.){3}([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))$ ]]; then
        if [ $c_patif == $patif ]; then
          logit "passive AF traffic IP $patif correct in $i_file"
        else
          logit "Correcting passive AF traffic IP in $i_file"
          cmd "sed -i 's/$patif/$c_patif/g' $i_file"
        fi
      fi
    else
      logit "Unable to get passive AF traffic IP in $paasif"
      exit 1
    fi
  else
    logit "Passive AF access server $paasif is not reachable, can not Continue,please check manually."
    exit 1
  fi

  if [[ "$maasif_reach" == "200" && "$paasif_reach" == "200" ]]; then
    if [[ $st_pe_mainaf == '111' && $st_pe_passiveaf == '111' ]]; then
      logit "Changing input file"
      cmd "sed -i 's/mainAF/mainAF_old/g' $i_file"
      cmd "sed -i 's/passiveAF/mainAF_new/g' $i_file"
      cmd "sed -i 's/mainAF_old/passiveAF/g' $i_file"
      cmd "sed -i 's/mainAF_new/mainAF/g' $i_file"
    elif [[ $st_pe_mainaf == '0' && $st_pe_passiveaf == '0' ]]; then
      logit "main AF & passive AF entry in $i_file found OK"
    else
      logit "main AF & passive AF passive enabled status found not OK"
    fi
  fi

  if [ "$ccnw" == "200" ]; then
    logit "Unable to check main AF POD status as both access server & external service unreachable"
    mainaf_down=$(echo 200)
  fi
#       set +H
#       id=$(curl -X 'POST' 'http://'$CDD_handler_IP':8081/api/authenticate' -H 'accept: */*' -H 'content-type: application/json' -d '{"password": "aF22hD!wS8d6HpVsd","rememberMe": true,"username": "af_user"}' | grep \"id_token\"| awk -F " " '{print $NF}' | sed 's/\"//g')
#       set -H
#       logit "checking helm releases & values.yaml file for main AF"
  ma_chart_value=$(ssh_main_AF "$helm_ab_path_main_AF ls -a" | awk -v mahcdnf="$mahcdnf" '$1 == mahcdnf' | awk '{print $(NF -1)}' | awk -F "-" '{print $NF}')
  logit "download values.yaml for $mahcdnf"
  ssh_main_AF "$helm_ab_path_main_AF get values -a $mahcdnf -o yaml"  > $logdir/$mahcdnf.yaml
  ma_tag_value=$(cat $logdir/$mahcdnf.yaml | grep tag |grep -v "#" | awk -F ":" '{print $NF}' | sed 's/\-/\+/g' | sed 's/\"//g' )

  if [ $ma_chart_value == $ma_tag_value ]; then
    logit "$mahcdnf release value & tag value in rosseta repo values.yaml same"
  else
    logit "$mahcdnf release value & tag value in rosseta repo values.yaml not same"
    logit "$mahcdnf release value $ma_chart_value"
    logit "$mahcdnf tag value in values.yaml $ma_tag_value"
    exit 1
  fi
  logit "checking helm releases & values.yaml file for passive AF"
  pa_chart_value=$(ssh_pass_AF "$helm_ab_path_passive_AF ls -a" | awk -v pahcdnf="$pahcdnf" '$1 == pahcdnf' | awk '{print $(NF -1)}' | awk -F "-" '{print $NF}')
  logit "download values.yaml for $pahcdnf"
  ssh_pass_AF "$helm_ab_path_passive_AF get values -a $pahcdnf -o yaml" > $logdir/$pahcdnf.yaml
  pa_tag_value=$(cat $logdir/$pahcdnf.yaml | grep tag |grep -v "#" | awk -F ":" '{print $NF}' | sed 's/\-/\+/g' | sed 's/\"//g' )

  if [ $pa_chart_value == $pa_tag_value ]; then
    logit "$pahcdnf release value & tag value in rosseta repo values.yaml same"
  else
    logit "$pahcdnf release value & tag value in rosseta repo values.yaml not same"
    logit "$pahcdnf release value $pa_chart_value"
    logit "$pahcdnf tag value in values.yaml $pa_tag_value"
    exit 1
  fi
  logit "checking helm releases & values.yaml file for assistant AFs"
  cat $i_file | grep AssistantAF > $logdir/assistant_AF.txt
  while read line
    do
      ass_acc_server_ip=$(echo $line | awk -F " " '{print $6}')
      logit ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "hostname 1>/dev/null"
      if [ $? == 0 ]; then
        ass_helm_name=$(echo $line | awk -F " " '{print $3}')
        ass_helm_path=$(ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "source .bash_profile && which helm")
        ass_chart_value=$(ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_helm_path ls -a" | awk -v ass_helm_name="$ass_helm_name" '$1 == ass_helm_name' | awk '{print $(NF -1)}' | awk -F "-" '{print $NF}')
        assfu=$(echo $line | awk '{print $7}')
        logit "download values.yaml for $ass_helm_name"
        ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_helm_path get values -a $ass_helm_name" > $logdir/$ass_helm_name_values.yaml
        ass_tag_value=$(cat $logdir/$ass_helm_name_values.yaml | grep tag |grep -v "#" | awk -F ":" '{print $NF}' | sed 's/\-/\+/g' | sed 's/\"//g' )
        if [ $ass_chart_value == $ass_tag_value ]; then
          logit "$ass_helm_name release value & tag value in rosseta repo values.yaml same"
        else
          logit "$ass_helm_name release value & tag value in rosseta repo values.yaml not same"
          logit "$ass_helm_name release value $ass_chart_value"
          logit "$ass_helm_name tag value in values.yaml $ass_tag_value"
          exit 1
        fi
      else
        logit "Unable to ssh to $ass_helm_name access server $ass_acc_server_ip"
        exit 1
      fi
    done < $logdir/assistant_AF.txt
}

function define_variables () {

  #define variables
  #main AF pod name in file $i_file - mapnf
  mapnf=$(cat $i_file | grep mainAF | awk -F " " '{print $2}')
  #main AF helm chart dir name in file $i_file - mahcdnf
  mahcdnf=$(cat $i_file | grep mainAF | awk -F " " '{print $3}')
  #main AF traffic IP in file - matf
  matif=$(cat $i_file | grep mainAF | awk -F " " '{print $4}')
  #main AF OAM ip in file - maof
  maof=$(cat $i_file | grep mainAF | awk -F " " '{print $5}')
  #main AF access server IP in file - maasif
  maasif=$(cat $i_file | grep mainAF | awk -F " " '{print $6}')
  #main AF helm chart dir
  #mahcd=$(cat $i_file | grep mainAF | awk -F " " '{print $8}')

  #passive AF pod name in file $i_file - papnf
  papnf=$(cat $i_file | grep passiveAF | awk -F " " '{print $2}')
  #passive AF helm chart dir name in file $i_file - pahcdnf
  pahcdnf=$(cat $i_file | grep passiveAF | awk -F " " '{print $3}')
  #passive AF traffic IP in file - patf
  patif=$(cat $i_file | grep passiveAF | awk -F " " '{print $4}')
  #passive AF OAM ip in file - paof
  paof=$(cat $i_file | grep passiveAF | awk -F " " '{print $5}')
  #passive AF access server IP in file - paasif
  paasif=$(cat $i_file | grep passiveAF | awk -F " " '{print $6}')
  #passive AF helm chart dir
  #pahcd=$(cat $i_file | grep mainAF | awk -F " " '{print $8}')
  #check no of assistant AF present in $i_file file
  no_assistant=$(cat $i_file | grep AssistantAF | wc -l )
  #namespace should be provided
  namespace=chf-ec-apps
  date=$(date +%d_%m_%Y_%H_%M_%S)
  sleeptime=$(cat $i_file | grep sleeptime | awk -F " " '{print $2}')
  retrytime=$(cat $i_file | grep retrytime | awk -F " " '{print $2}')
  mafu=$(cat $i_file | grep mainAF | awk '{print $7}')
  pafu=$(cat $i_file | grep passiveAF | awk '{print $7}')


  ssh_main_AF () 
  {
    ssh -o StrictHostKeyChecking=no -q ec01afgeored@$maasif "$@"
  }

  ssh_pass_AF () 
  {
    ssh -o StrictHostKeyChecking=no -q ec01afgeored@$paasif "$@"
  }
  ssh_main_AF "hostname 1>/dev/null"
  if [ $? == 0 ]; then
    k_ab_path_main_AF=$(ssh_main_AF "source .bash_profile && which kubectl")
    helm_ab_path_main_AF=$(ssh_main_AF "source .bash_profile && which helm")
  fi
  k_ab_path_passive_AF=$(ssh_pass_AF "source .bash_profile && which kubectl")
  helm_ab_path_passive_AF=$(ssh_pass_AF "source .bash_profile && which helm")
}

function helm_dir_prep {
#       #CDD_handler_IP=10.147.72.206
#       curr_pkg=$(cat $i_file | grep curr_pkg | awk '{print $2}')
#       lat_pkg=$(cat $i_file | grep lat_pkg | awk '{print $2}')
#
#       logit "generating id token"
#       set +H
#       id=$(curl -X 'POST' 'http://'$CDD_handler_IP':8081/api/authenticate' -H 'accept: */*' -H 'content-type: application/json' -d '{"password": "aF22hD!wS8d6HpVsd","rememberMe": true,"username": "af_user"}' | grep \"id_token\"| awk -F " " '{print $NF}' | sed 's/\"//g')
#       set -H
#       logit "generated id"
#       logit "$id"
#
#       logit "download chart dir"
#
#       cmd "curl -X 'GET' 'http://'$CDD_handler_IP':8081$curr_pkg' -H 'accept: */*' -H 'Authorization: Bearer $id' --output $logdir/curr_pkg.tar.gz"
#
  curr_chart_value=$(ssh_pass_AF "cat /home/ec01afgeored/pkgs/EC22.6/eric-ec-af/Chart.yaml | grep '^version' | awk '{print \$NF}'")
#
#       cmd "curl -X 'GET' 'http://'$CDD_handler_IP':8081$lat_pkg' -H 'accept: */*' -H 'Authorization: Bearer $id' --output $logdir/lat_pkg.tar.gz"
#
  lat_chart_value=$(ssh_pass_AF "cat /home/ec01afgeored/pkgs/EC22.9_ODR/eric-ec-af/Chart.yaml | grep '^version' | awk '{print \$NF}'")
#
#       #logit "untar the package"
#       #cmd "tar -zxvf $logdir/curr_pkg.tar.gz --directory $logdir"
#
#
  case $1 in
  pahcdnf)
  logit "preparing helm directory for $pahcdnf"
  logit "Get the release value"
  chart_value=$(ssh_pass_AF "$helm_ab_path_passive_AF ls -a" | awk -v pahcdnf="$pahcdnf" '$1 == pahcdnf' | awk '{print $(NF -1)}' | awk -F "-" '{print $NF}')
  if [ ! -z $chart_value ]; then
    if [ $chart_value == $curr_chart_value ]; then
      logit "Helm release $chart_value for $pahcdnf"
      logit "get the package copied"
      ssh_pass_AF "rsync -a /home/ec01afgeored/pkgs/EC22.6/eric-ec-af/ /home/ec01afgeored/pkgs/EC22.6/eric-ec-af_$pahcdnf"
      cmd scp -r -q -o StrictHostKeyChecking=no ec01afgeored@$paasif:~/pkgs/EC22.6/eric-ec-af_$pahcdnf $logdir/
    elif [ $chart_value == $lat_chart_value ]; then
      logit "Helm release $chart_value for $pahcdnf"
      logit "get the package copied"
      ssh_pass_AF "rsync -a /home/ec01afgeored/pkgs/EC22.9_ODR/eric-ec-af/ /home/ec01afgeored/pkgs/EC22.9_ODR/eric-ec-af_$pahcdnf"
      cmd scp -r -q -o StrictHostKeyChecking=no ec01afgeored@$paasif:~/pkgs/EC22.9_ODR/eric-ec-af_$pahcdnf $logdir/
    else
      "logit Unknown Helm release $chart_value for $pahcdnf"
    fi
  else
    logit "Unable to get Helm release for $pahcdnf"
  fi
  #cmd "mv $logdir/eric-ec-af $logdir/eric-ec-af_$pahcdnf"
  #if [ $? == 0 ]; then
  #       rm -rf $logdir/eric-ec-af
  #fi

  logit "preparing esa secret file in $logdir/eric-ec-af_$pahcdnf"
  cmd "echo -e \"snmpUser-1: snmpuser1\nsnmpAuthPasswd-1: EricssonAuth1\nsnmpPrivPasswd-1: EricssonPriv1\" > $logdir/eric-ec-af_$pahcdnf/esaSecretFile.txt"
  cmd "cat $logdir/eric-ec-af_$pahcdnf/esaSecretFile.txt"
  logit "preparing user secret file in $logdir/eric-ec-af_$pahcdnf"
  cmd "echo -e \"sftpUser: ftpuser\nsftpPasswd: Champing2018#321\" > $logdir/eric-ec-af_$pahcdnf/userSecretFile.txt"
  cmd "cat $logdir/eric-ec-af_$pahcdnf/userSecretFile.txt"

  #logit "Downloading values.yaml file for $pahcdnf"
  #cmd "curl -X 'GET' 'http://'$CDD_handler_IP':8081$pafu=values.yaml' -H 'accept: */*' -H 'Authorization: Bearer $id' > $logdir/eric-ec-af_$pahcdnf/values.yaml"
  #logit "Downloading af-networkpolicy-values.yaml file for $pahcdnf"
  #cmd "curl -X 'GET' 'http://'$CDD_handler_IP':8081$pafu=af-networkpolicy-values.yaml' -H 'accept: */*' -H 'Authorization: Bearer $id' > $logdir/eric-ec-af_$pahcdnf/af-networkpolicy-values.yaml"

  logit "checking template directory for podmon label in $logdir/eric-ec-af_$pahcdnf/"
  if  grep -Fxq "        podmon.dellemc.com/driver: ccd-podmon" $logdir/eric-ec-af_$pahcdnf/templates/af-statefulset.yaml; then
    if [ $(grep -n "        podmon.dellemc.com/driver: ccd-podmon" $logdir/eric-ec-af_$pahcdnf/templates/af-statefulset.yaml | awk -F ":" '{print $1}') == "31" ] ; then
      logit "podmon label present in line 31 $logdir/eric-ec-af_$pahcdnf/templates/af-statefulset.yaml file"
    fi
  else
    logit "inserting podmon label to $logdir/eric-ec-af_$pahcdnf/templates/af-statefulset.yaml"
    cmd "sed -i '31 i \        podmon.dellemc.com/driver: ccd-podmon' $logdir/eric-ec-af_$pahcdnf/templates/af-statefulset.yaml"
  fi
  ;;
  ass_helm_name)
  logit "preparing helm directory for $ass_helm_name"
  logit "Get the release value"
  chart_value=$(ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_helm_path ls -a" | awk -v ass_helm_name="$ass_helm_name" '$1 == ass_helm_name' | awk '{print $(NF -1)}' | awk -F "-" '{print $NF}')
  if [ ! -z $chart_value ]; then
    if [ $chart_value == $curr_chart_value ]; then
      logit "Helm release $chart_value for $ass_helm_name"
      logit "copy the package"
      ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "rsync -a /home/ec01afgeored/pkgs/EC22.6/eric-ec-af/ /home/ec01afgeored/pkgs/EC22.6/eric-ec-af_$ass_helm_name"
      cmd scp -r -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip:~/pkgs/EC22.6/eric-ec-af_$ass_helm_name $logdir/
    elif [ $chart_value == $lat_chart_value ]; then
      logit "Helm release $chart_value for $ass_helm_name"
      logit "copy the package"
      ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "rsync -a /home/ec01afgeored/pkgs/EC22.9_ODR/eric-ec-af/ /home/ec01afgeored/pkgs/EC22.9_ODR/eric-ec-af_$ass_helm_name"
      cmd scp -r -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip:~/pkgs/EC22.9_ODR/eric-ec-af_$ass_helm_name $logdir/
    else
      "logit Unknown Helm release $chart_value for $ass_helm_name"
    fi
  else
    logit "Unable to get Helm release for $ass_helm_name"
  fi
  #cmd "mv $logdir/eric-ec-af $logdir/eric-ec-af_$ass_helm_name"
  #if [ $? == 0 ]; then
  #       rm -rf $logdir/eric-ec-af
  #fi
  logit "preparing esa secret file in $logdir/eric-ec-af_$ass_helm_name"
  cmd "echo -e \"snmpUser-1: snmpuser1\nsnmpAuthPasswd-1: EricssonAuth1\nsnmpPrivPasswd-1: EricssonPriv1\" > $logdir/eric-ec-af_$ass_helm_name/esaSecretFile.txt"
  cmd "cat $logdir/eric-ec-af_$ass_helm_name/esaSecretFile.txt"
  logit "preparing user secret file in $logdir/eric-ec-af_$ass_helm_name"
  cmd "echo -e \"sftpUser: ftpuser\nsftpPasswd: Champing2018#321\" > $logdir/eric-ec-af_$ass_helm_name/userSecretFile.txt"
  cmd "cat $logdir/eric-ec-af_$ass_helm_name/userSecretFile.txt"

  #logit "Downloading values.yaml file for $ass_helm_name"
  #cmd "ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_helm_path get values -a ass_helm_name -o yaml" > $logdir/eric-ec-af_$ass_helm_name/values.yaml"
  #logit "Downloading af-networkpolicy-values.yaml file for $ass_helm_name"
  #cmd "curl -X 'GET' 'http://'$CDD_handler_IP':8081$assfu=af-networkpolicy-values.yaml' -H 'accept: */*' -H 'Authorization: Bearer $id' > $logdir/eric-ec-af_$ass_helm_name/af-networkpolicy-values.yaml"

  logit "checking template directory for podmon label in $logdir/eric-ec-af_$ass_helm_name/"
  if  grep -Fxq "        podmon.dellemc.com/driver: ccd-podmon" $logdir/eric-ec-af_$ass_helm_name/templates/af-statefulset.yaml; then
    if [ $(grep -n "        podmon.dellemc.com/driver: ccd-podmon" $logdir/eric-ec-af_$ass_helm_name/templates/af-statefulset.yaml | awk -F ":" '{print $1}') == "31" ] ; then
      logit "podmon label present in line 31 $logdir/eric-ec-af_$ass_helm_name/templates/af-statefulset.yaml file"
    fi
  else
    logit "inserting podmon label to $logdir/eric-ec-af_$ass_helm_name/templates/af-statefulset.yaml"
    cmd "sed -i '31 i \        podmon.dellemc.com/driver: ccd-podmon' $logdir/eric-ec-af_$ass_helm_name/templates/af-statefulset.yaml"
  fi
  ;;
  esac
}

case $1 in
  helm_dir_prep)
    helm_dir_prep
    exit 1
    ;;
  dir_check)
    dir_check $2
    exit 1
    ;;
  validate)
    validate_input
    exit 1
    ;;
esac


function dir_check {
  #define_variables ## this line to be deleted later
  dir=$1
  chart_name=$(echo $dir | awk -F "_" '{print $NF}')
  echo $chart_name
  # check if the directory exist
  if [ ! -d $dir ]; then
    logit "$dir Directory does not exist, exit"
    exit 1
  fi

  # check the chart file
  dir_chart_value=$(cat $dir/Chart.yaml | grep version | awk -F ":" '{print $NF}' | sed 's/^ //g')
  if [ $chart_name == $pahcdnf ]; then
    chart_value=$(ssh_pass_AF "$helm_ab_path_passive_AF ls -a" | awk -v pahcdnf="$pahcdnf" '$1 == pahcdnf' | awk '{print $(NF -1)}' | awk -F "-" '{print $NF}')
  elif [ $chart_name == $ass_helm_name ]; then
    chart_value=$(ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_helm_path ls -a" | awk -v ass_helm_name="$ass_helm_name" '$1 == ass_helm_name' | awk '{print $(NF -1)}' | awk -F "-" '{print $NF}')
  else
    logit "Unknown directory $dir"
  fi
  tag_value=$(cat $dir/values.yaml | grep tag |grep -v "#" | awk -F ":" '{print $NF}' | sed 's/\-/\+/g' | sed 's/\"//g' )

  echo "dir_chart value $dir_chart_value"
  echo "chart_value $chart_value"
  echo "tag_value $tag_value"

  if [ $dir_chart_value != $chart_value ]; then
    logit "Version mismatch in $dir/Chart.yaml & helm release"
    cmd "cat $dir/Chart.yaml | grep version | awk -F \":\" '{print \$NF}' | sed 's/^ //g'"
    cmd "ssh_pass_AF \"$helm_ab_path_passive_AF ls -a\" | awk -v pahcdnf=\"$pahcdnf\" '\$1 == pahcdnf' | awk '{print \$(NF -1)}' | awk -F \"-\" '{print \$NF}' "
    exit 1
  elif [ $dir_chart_value != $tag_value ]; then
    logit "Version mismatch in $dir/Chart.yaml & $dir/values.yaml file"
    cmd "cat $dir/Chart.yaml | grep version | awk -F \":\" '{print \$NF}' | sed 's/^ //g'"
    cmd "cat $dir/values.yaml | grep tag |grep -v \"#\" | awk -F \":\" '{print \$NF}'"
    exit 1
  elif [ $chart_value != $tag_value ]; then
    logit "Version mismatch in helm release & $dir/values.yaml file"
    cmd "ssh_pass_AF \"$helm_ab_path_passive_AF ls -a\" | awk -v pahcdnf=\"$pahcdnf\" '\$1 == pahcdnf' | awk '{print \$(NF -1)}' | awk -F \"-\" '{print \$NF}'"
    cmd "cat $dir/values.yaml | grep tag |grep -v \"#\" | awk -F \":\" '{print \$NF}'"
    exit 1
  else
    logit "$dir/Chart.yaml $dir/values.yaml & helm release found OK"
    dir_check_rc=200
  fi

  #check values.yaml file
  #if [ $dir_check_rc == 200 ]; then
  #       if [ $(cat $dir/values.yaml | grep ^nameOverride | awk -F " " '{print $NF}' | sed 's/\"//g') == $pahcdnf ]; then
  #         logit "values.yaml file found OK"
  #
  #         dir_check_rc_1=300
  #       else
  #         logit "values.yaml file found not OK"
  #         cmd "cat $dir/values.yaml | grep ^nameOverride | awk -F \" \" '{print \$NF}' | sed 's/\"//g'"
  #         cmd "echo $pahcdnf"
  #         exit 1
  #       fi
  #fi
}


function convert_old_main_AF_to_passive () {

  logit "get the helm values for old main AF"
  cmd ssh_pass_AF "$helm_ab_path_passive_AF get values -a $pahcdnf -o yaml" > $logdir/$pahcdnf.yml

  #take backup of old main AF helm yml
  logit "take backup of old main AF $pahcdnf helm yml"
  cmd cp -p $logdir/$pahcdnf.yml $logdir/"$pahcdnf"_change.yml
  cp -p $logdir/$pahcdnf.yml $logdir/"$pahcdnf"_"$date".yml

  #change values to convert old main af to passive AF
  logit "change values to convert old main af to passive AF"
  cmd "sed -i \"s|mainIp: $patif|mainIp: $matif|g\" $logdir/"$pahcdnf"_change.yml"
  cmd "sed -i \"s|mainOamIp: $paof|mainOamIp: $maof|g\" $logdir/"$pahcdnf"_change.yml"
  cmd "sed -i \"s|passiveMainIp: .*|passiveMainIp: $patif|g\" $logdir/"$pahcdnf"_change.yml"
  cmd "sed -i \"s|passiveMainOamIp: .*|passiveMainOamIp: $paof|g\" $logdir/"$pahcdnf"_change.yml"
  cmd "sed -i \"s|enabled: \\"\"no\\"\"|enabled: \\"\"yes\\"\"|g\" $logdir/"$pahcdnf"_change.yml"

  #copy the new yml file to old main AF access server
  logit "copy the new yml file to old main AF $pahcdnf access server"
  yaml_to_copy_dir=$(ssh_pass_AF "pwd")
  cmd scp -q -o StrictHostKeyChecking=no $logdir/"$pahcdnf"_change.yml ec01afgeored@$paasif:$yaml_to_copy_dir/
  if [ $? != "0" ]; then
    logit "unable to copy $logdir/"$pahcdnf"_change.yml to $paasif server $yaml_to_copy_dir directory"
  else
    logit "$logdir/"$pahcdnf"_change.yml copied to $paasif server $yaml_to_copy_dir directory"
    #perform helm upgrade to make old main AF to passive AF
    helm_dir_prep pahcdnf
    dir_check $logdir/eric-ec-af_$pahcdnf
    cmd scp -r -q -o StrictHostKeyChecking=no $logdir/eric-ec-af_$pahcdnf ec01afgeored@$paasif:~/
    logit "performing helm upgrade to make old main AF $papnf as new passive AF"
    vl_date=$(ssh_pass_AF "date '+%d %b %Y %H:%M:%S'")
    ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -- sh -c \"echo '$vl_date $papnf $script_dir/$script_name:ACTION=\\"\"converting old main AF to passive AF\\"\" return=\\"\"follow log file $LogFile in adaptation pod\\"\"' >> /var/log/messages\""
    logit "checking helm history, last revision should be deployed state"
    h_lst_rev=$(ssh_pass_AF "$helm_ab_path_passive_AF history $pahcdnf" | tail -1 | awk '{print $1}')
    h_lst_rev_status=$(ssh_pass_AF "$helm_ab_path_passive_AF status $pahcdnf --revision $h_lst_rev" | grep "^STATUS:" | awk '{print $NF}' )

    if [ "$h_lst_rev_status" != "deployed" ]; then
      logit "can not run helm upgrade for $pahcdnf as last revision state is $h_lst_rev_status, Please check helm history for $pahcdnf"
      exit 1
    else
      logit "last revision state in helm history for $pahcdnf is $h_lst_rev_status"
    fi
    cmd ssh_pass_AF "$helm_ab_path_passive_AF upgrade $pahcdnf ~/eric-ec-af_$pahcdnf -f $yaml_to_copy_dir/"$pahcdnf"_change.yml -n $namespace --history-max 0"
    rc=$(echo $?)
    cmd "countdown 180"
    #verify if old main AF converted to new passive AF
    logit "verifying if old main AF converted to new passive AF"

    ssh_pass_AF "$helm_ab_path_passive_AF get values -a $pahcdnf -o yaml" > $logdir/after_$pahcdnf.yml
    enabled_status=$(cat $logdir/after_$pahcdnf.yml |  grep -w enabled | awk -F "\"" '{print $2}')
    main_IP_new=$(cat $logdir/after_$pahcdnf.yml |  grep -w mainIp | awk -F " " '{print $NF}' )
    main_oam_IP_new=$(cat $logdir/after_$pahcdnf.yml |  grep -w mainOamIp | awk -F " " '{print $NF}' )

    if [[ ($rc == "0" ) && ($enabled_status == "yes" ) && ( "$main_IP_new" == "$matif" ) && ( "$main_oam_IP_new" == "$maof" ) ]]; then
      logit "old main AF $papnf converted to passive AF"
      vl_date_1=$(ssh_pass_AF "date '+%d %b %Y %H:%M:%S'")
      ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -- sh -c \"echo '$vl_date_1 $papnf $script_dir/$script_name:ACTION=\\"\"old main AF is converted to new passive AF\\"\" return=\\"\"follow log file $LogFile in adaptation pod\\"\"' >> /var/log/messages\""
      # add new passive AF as assitant in new main AF
      logit "adding $papnf as assistant to $mapnf"
      cmd ssh_main_AF "$k_ab_path_main_AF exec -it $mapnf -n $namespace -- /opt/af/bin/AFServerManager -a -as $patif"
      if [ $? == "0" ]; then
        logit "$papnf added as assistant to $mapnf"
        cmd ssh_main_AF "$k_ab_path_main_AF exec -it $mapnf -n $namespace -- /opt/af/bin/AFServerManager -p -as"
        cmd "countdown 60"
        #run configure -ud in main AF
        cmd ssh_main_AF "$k_ab_path_main_AF exec -it $mapnf -n $namespace -- /opt/af/bin/configure -ud"
        cmd "countdown 60"

        logit "checking inside pod $mapnf & $papnf" 
        for i in {1..999}
        do
          patif_b=$(ssh_main_AF "$k_ab_path_main_AF exec -it $mapnf -- /opt/af/bin/AFServerManager -p -as" | grep "af02" | awk -F " " '{print $NF}')
          patif_c=$(ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -- /opt/af/bin/AFServerManager -p -as" | grep "af02" | awk -F " " '{print $NF}')

          if [[ $patif == $patif_b && $patif == $patif_c ]]; then
            logit "Passive AF traffic IP $patif present in main AF & passive AFServerManager command output"
            break
          else
            logit "Passive AF traffic IP $patif not present in main AF AFServerManager command output"
            cmd "countdown 60"
          fi

          named_main=$(ssh_main_AF "$k_ab_path_main_AF exec -it $mapnf -- cat /etc/opt/af/named.conf" | grep -A3 "acl theAssistants" | egrep -v "}|{" | sed 's/;//g' | grep -o '[^[:space:]]\+' | grep $patif )
          named_standby=$(ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -- cat /etc/opt/af/named.conf" | grep -A3 "acl theAssistants" | egrep -v "}|{" | sed 's/;//g' | grep -o '[^[:space:]]\+' | grep "$patif" )
          if [[ $patif == $named_main && $patif == $named_standby ]]; then
            logit "Passive AF traffic IP $patif present in main AF & passive AF named.conf file"
            break
          else
            logit "Passive AF traffic IP $patif not present in main AF & passive AF named.conf file,check "
            cmd "countdown 60"
          fi
        done
        #run configure -ud in assistant AF
        logit "checking assistant AF named.conf file"
        while read line
        do
          ass_po_name=$(echo $line | awk -F " " '{print $2}')
          ass_acc_server_ip=$(echo $line | awk -F " " '{print $6}')
          assfu=$(echo $line | awk '{print $7}')
          ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "hostname"
          if [ $? != "0" ]; then
            logit "Unable to ssh to $ass_po_name access server IP $ass_acc_server_ip"
          else
            ass_k_path=$(ssh -o StrictHostKeyChecking=no -q ec01afgeored@$ass_acc_server_ip "source .bash_profile && which kubectl")
            named_assistant=$(ssh -o StrictHostKeyChecking=no -q ec01afgeored@$ass_acc_server_ip "$ass_k_path exec -it $ass_po_name -- cat /etc/opt/af/named.conf" | grep -A3 "acl theAssistants" | egrep -v "}|{" | sed 's/;//g' | grep -o '[^[:space:]]\+' | grep "$patif")

            if [ "$named_assistant" == "$patif" ]; then
              logit "$patif is present $ass_po_name named.conf file"
            else
              logit "$patif is not present $ass_po_name named.conf file"
              cmd ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_k_path exec -it $ass_po_name -n $namespace -- /opt/af/bin/configure -ud"
              cmd "countdown 60"
              logit "checking assistant AF named.conf file after configure"
              named_assistant=$(ssh -o StrictHostKeyChecking=no -q ec01afgeored@$ass_acc_server_ip "cat /etc/opt/af/named.conf" | grep -A3 "acl theAssistants" | egrep -v "}|{" | sed 's/;//g' | grep -o '[^[:space:]]\+' | grep "$patif")
              if [ "$named_assistant" != "$patif" ]; then
                logit "$patif is not present $ass_po_name named.conf file after running configure -ud command,please check manually"
              fi

            fi
          fi
        done < $logdir/assistant_AF.txt

        logit "checkzone check in new main AF"
        cmd ssh_main_AF "$k_ab_path_main_AF exec -it $mapnf -n $namespace -- /opt/af/bin/checkzones.pl | grep "cs" > $logdir/checkzone_$mapnf.txt"
        if [ ! -z $logdir/checkzone_$mapnf.txt ]; then
          if  grep -qwv "OK" $logdir/checkzone_$mapnf.txt; then
            logit "checkzone status to $mapnf found not OK, Please intervene manually"
            cat $logdir/checkzone_$mapnf.txt
          else
            logit "checkzone status to $mapnf found OK"
            cat $logdir/checkzone_$mapnf.txt
          fi
        else
          logit "checkzone status to $mapnf found not OK, Please intervene manually"
        fi
      else
        logit "$papnf not added as assistant to $mapnf,intervene manually"
        exit 1
      fi
    else
      logit "unable to convert old main AF $papnf to passive AF,please intervene manually"
      exit 1
    fi
  fi
}

function af_switch () {

logit "performing switchover between main & passive AF"

#check if main AF accessible & running

logit "getting passive AF helm value"
#get passive AF helm values
cmd "ssh_pass_AF \"$helm_ab_path_passive_AF get values -a $pahcdnf -o yaml\" > $logdir/$pahcdnf.yml"
#take backup of passive_AF helm yml
logit "take backup of passive_AF helm yml"
cp -p $logdir/$pahcdnf.yml $logdir/"$pahcdnf"_"$date".yml
cmd cp -p $logdir/$pahcdnf.yml $logdir/"$pahcdnf"_change.yml

logit "changing passive AF helm values"
#Replace main AF IP's to passive AF

cmd "sed -i \"s|mainIp: $matif|mainIp: $patif|g\" $logdir/"$pahcdnf"_change.yml"
cmd "sed -i \"s|mainOamIp: $maof|mainOamIp: $paof|g\" $logdir/"$pahcdnf"_change.yml"
cmd "sed -i \"s|passiveMainIp: $patif|passiveMainIp: $matif|g\" $logdir/"$pahcdnf"_change.yml"
cmd "sed -i \"s|passiveMainOamIp: $paof|passiveMainOamIp: $maof|g\" $logdir/"$pahcdnf"_change.yml"
cmd "sed -i \"s|enabled: \\"\"yes\\"\"|enabled: \\"\"no\\"\"|g\" $logdir/"$pahcdnf"_change.yml"

#check the changed values are correct

if [ $(cat $logdir/"$pahcdnf"_change.yml | grep -w mainIp | awk -F " " '{print $NF}') != $patif ]; then
  logit "mainIp not properly configured to change new main AF  file $logdir/$pahcdnf.yml"
  exit 1
elif [ $(cat $logdir/"$pahcdnf"_change.yml | grep -w mainOamIp | awk -F " " '{print $NF}') != $paof ]; then
  logit "mainOamIp not properly configured to change new main AF  file $logdir/$pahcdnf.yml"
  exit 1
elif [ $(cat $logdir/"$pahcdnf"_change.yml | grep -w passiveMainIp | awk -F " " '{print $NF}') != $matif ]; then
  logit "passiveMainIp not properly configured to change new main AF  file $logdir/$pahcdnf.yml"
  exit 1
elif [ $(cat $logdir/"$pahcdnf"_change.yml | grep -w passiveMainOamIp | awk -F " " '{print $NF}') != $maof ]; then
  logit "passiveMainOamIp not properly configured to change new main AF  file $logdir/$pahcdnf.yml"
  exit 1
elif [ $(cat $logdir/"$pahcdnf"_change.yml | grep -w enabled | awk -F "\"" '{print $2}') != "no" ]; then
  logit "enabled value not set to \"no\""
else
  logit "$logdir/"$pahcdnf"_change.yml file configured correctly"
fi

yaml_to_copy_dir=$(ssh_pass_AF "pwd")

#copy new yml file to passive AF access dir
logit "copy new yml file to passive AF access dir"
cmd scp -q -o StrictHostKeyChecking=no $logdir/"$pahcdnf"_change.yml ec01afgeored@$paasif:$yaml_to_copy_dir/
if [ $? != "0" ]; then
  logit "unable to copy new main AF yml file $logdir/"$pahcdnf"_change.yml to $paasif server $yaml_to_copy_dir directory"
  exit 1
else
  logit "$logdir/"$pahcdnf"_change.yml copied to $paasif server $yaml_to_copy_dir directory"
  #perform helm upgrade to change passive AF to main AF
  helm_dir_prep pahcdnf
  dir_check $logdir/eric-ec-af_$pahcdnf
  logit "performing helm upgrade to make passive AF as new main AF"
  cmd scp -r -q -o StrictHostKeyChecking=no $logdir/eric-ec-af_$pahcdnf ec01afgeored@$paasif:~/
  vl_date=$(ssh_pass_AF "date '+%d %b %Y %H:%M:%S'")
  ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -- sh -c \"echo '$vl_date $papnf $script_dir/$script_name:ACTION=\\"\"failover triggered\\"\" return=\\"\"follow log file $LogFile in adaptation pod\\"\"' >> /var/log/messages\""
  logit "checking helm history, last revision should be deployed state"
    h_lst_rev=$(ssh_pass_AF "$helm_ab_path_passive_AF history $pahcdnf " | tail -1 | awk '{print $1}')
    h_lst_rev_status=$(ssh_pass_AF "$helm_ab_path_passive_AF status $pahcdnf --revision $h_lst_rev" | grep "^STATUS:" | awk '{print $NF}')
    if [ "$h_lst_rev_status" != "deployed" ]; then
      logit "can not run helm upgrade for $pahcdnf as last revision state is $h_lst_rev_status, Please check helm history for $pahcdnf"
      exit 1
    else
      logit "last revision state in helm history for $pahcdnf is $h_lst_rev_status"
    fi

  cmd ssh_pass_AF "$helm_ab_path_passive_AF upgrade $pahcdnf ~/eric-ec-af_$pahcdnf -f $yaml_to_copy_dir/"$pahcdnf"_change.yml -n $namespace --history-max 0"
  rc=$(echo $?)

  if [ $rc != 0 ]; then
    logit "helm upgrade not sucessfull, Please check manually"
  fi
  cmd countdown 180

  # verify if passive AF converted to new main AF
  logit "verify if passive AF converted to new main AF $papnf"

  for i in {1..999}
    do
    logit "checking inside new main AF $papnf"
    patif_a=$(ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -- /opt/af/bin/AFServerManager -p -as" | grep "af01" | awk -F " " '{print $NF}')
    patif_named_a=$(ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -- cat /etc/opt/af/named.conf" | grep -A2 "masters theMains port 53 {" | grep -v "masters theMains port 53 {"| sed 's/         //g'|sed 's/[{,\;]//g' | paste - - | awk -F " " '{print $1}')
    patif_named_b=$(ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -- cat /etc/opt/af/named.conf" | grep -A2 "masters theMains port 53 {" | grep -v "masters theMains port 53 {"| sed 's/         //g'|sed 's/[{,\;]//g' | paste - - | awk -F " " '{print $2}')

    logit "main AF IP in $papnf $patif_a"
    logit "main AF IPs in $papnf in named.conf file $patif_named_a & $patif_named_b"

    if [[ $patif_a == $patif && ( $patif_named_a == $patif || $patif_named_b == $patif ) ]]; then
      logit "old passive AF $papnf is new main AF in AFServerManager"
      vl_date_1=$(ssh_pass_AF "date '+%d %b %Y %H:%M:%S'")
      ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -- sh -c \"echo '$vl_date_1 $papnf $script_dir/$script_name:ACTION=\\"\"failover completed\\"\" return=\\"\"follow log file $LogFile in adaptation pod\\"\"' >> /var/log/messages\""
      break
    else
      logit "old passive AF $papnf is not yet converted to new main AF in AFServerManager, please check /opt/af/bin/AFServerManager -p -as & /etc/opt/af/named.conf file"
      cmd "countdown 60"
    fi
  done


  cmd "ssh_pass_AF \"$helm_ab_path_passive_AF get values -a $pahcdnf -o yaml\" > $logdir/new_$pahcdnf.yml"
  enabled_status=$(cat $logdir/new_$pahcdnf.yml |  grep -w enabled | awk -F "\"" '{print $2}')
  main_IP_new=$(cat $logdir/new_$pahcdnf.yml |  grep -w mainIp | awk -F " " '{print $NF}' )
  main_oam_IP_new=$(cat $logdir/new_$pahcdnf.yml |  grep -w mainOamIp | awk -F " " '{print $NF}' )
  if [[ ( $rc == "0" ) && ( $enabled_status == "no" ) && ( "$main_IP_new" == "$patif" ) && ( "$main_oam_IP_new" == "$paof") ]]; then
    logit "old passive AF $papnf converted to new main AF sucessfully"
    #change in all assistant AF
    logit "Updating new main AF IP in all assistant AF"
    cat $i_file | grep AssistantAF > $logdir/assistant_AF.txt
    while read line
    do
      ass_po_name=$(echo $line | awk -F " " '{print $2}')
      ass_helm_name=$(echo $line | awk -F " " '{print $3}')
      ass_acc_server_ip=$(echo $line | awk -F " " '{print $6}')
      assfu=$(echo $line | awk '{print $7}')
      #echo "$ass_po_name $ass_helm_name $ass_acc_server_ip"
      logit ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "hostname 1>/dev/null"
      if [ $? != "0" ]; then
        logit "Unable to ssh to $ass_po_name access server IP $ass_acc_server_ip"
      else
        ass_helm_path=$(ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "source .bash_profile && which helm")
        ass_k_path=$(ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "source .bash_profile && which kubectl")
        helm_dir_prep ass_helm_name
        dir_check $logdir/eric-ec-af_$ass_helm_name
        cmd scp -q -r -o StrictHostKeyChecking=no $logdir/eric-ec-af_$ass_helm_name ec01afgeored@$ass_acc_server_ip:~/
        rec_ass_helm_name=$(echo $?)
        if [ $rec_ass_helm_name != "0" ]; then
          logit "unable to copy $logdir/eric-ec-af_$ass_helm_name to $ass_acc_server_ip home path"
        else
          logit "able to copy $logdir/eric-ec-af_$ass_helm_name to $ass_acc_server_ip home path"
          #ass_helm_chart_dir="/home/ec01admin/container/sw/af/EC22_GA/eric-ec-af-assistant"
          cmd ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_helm_path get values -a $ass_helm_name" > $logdir/$ass_helm_name.yml
          cmd "sed -i \"s|mainIp: $matif|mainIp: $patif|g\" $logdir/$ass_helm_name.yml"
          cmd "sed -i \"s|mainOamIp: $maof|mainOamIp: $paof|g\" $logdir/$ass_helm_name.yml"
          cmd scp -q -o StrictHostKeyChecking=no $logdir/$ass_helm_name.yml ec01afgeored@$ass_acc_server_ip:~/
          if [ $? != "0" ]; then
            logit "unable to copy $logdir/$ass_helm_name.yml to ass_acc_server_ip home path"
          else
            logit "able to copy $logdir/$ass_helm_name.yml to ass_acc_server_ip home path"
            logit "Checking helm status for $ass_helm_name, last revision should be in deployed state"
            h_lst_rev_ass=$(ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_helm_path history $ass_helm_name" | tail -1 | awk '{print $1}')
            h_lst_rev_status_ass=$(ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_helm_path status $ass_helm_name --revision $h_lst_rev_ass" | grep "^STATUS:" | awk '{print $NF}')
            if [ "$h_lst_rev_status_ass" != "deployed" ]; then
              logit "can not run helm upgrade for $ass_helm_name as last revision state is $h_lst_rev_status_ass, Please check helm history for $ass_helm_name, and manually try to upgrade"
              break
            else
              logit "last revision state in helm history for $ass_helm_name is $h_lst_rev_status_ass"
              logit "changing main AF IP in $ass_po_name"
              vl_date=$(ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "date '+%d %b %Y %H:%M:%S'")

              ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_k_path exec $ass_po_name -- sh -c \"echo '$vl_date $ass_po_name $script_dir/$script_name:ACTION=\\"\"passive AF IP to be converted to main AF\\"\" return=\\"\"follow log file $LogFile in adaptation pod\\"\"' >> /var/log/messages\""


              cmd ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_helm_path upgrade $ass_helm_name ~/eric-ec-af_$ass_helm_name -f $ass_helm_name.yml -n $namespace --history-max 0"
              cmd countdown 180
              for i in {1..60}
              do
                logit "checking inside $ass_po_name for main AF IP"
                mainafip_assaf=$(ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_k_path exec -it $ass_po_name -- /opt/af/bin/AFServerManager -p -as" | grep "af01" | awk -F " " '{print $NF}')

                assaf_named_a=$(ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_k_path exec -it $ass_po_name -- cat /etc/opt/af/named.conf" | grep -A2 "masters theMains port 53 {" | grep -v "masters theMains port 53 {"| sed 's/         //g'|sed 's/[{,\;]//g' | paste - - | awk -F " " '{print $1}')

                logit "main AF IP in assistant AF AFServerManager $mainafip_assaf"
                logit "main AF IP in named file in assistant AF $assaf_named_a"
                if [[ $mainafip_assaf == $patif && $assaf_named_a == $patif ]]; then
                  logit "$patif new main AF IP in $ass_po_name"
                  vl_date_1=$(ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "date '+%d %b %Y %H:%M:%S'")
                  ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_k_path exec $ass_po_name -- sh -c \"echo '$vl_date_1 $ass_po_name $script_dir/$script_name:ACTION=\\"\"passive AF IP now converted to main AF\\"\" return=\\"\"follow log file $LogFile in adaptation pod\\"\"' >> /var/log/messages\""
                  break
                else
                  logit "$ass_po_name is not in sync with new main AF $papnf"
                  cmd "countdown 60"
                fi
              done
            fi
            cmd ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_helm_path get values -a $ass_helm_name" > $logdir/"$ass_helm_name"_new.yml
            main_IP_new_ass=$(cat $logdir/"$ass_helm_name"_new.yml | grep "mainIp" | awk -F " " '{print $NF}')
            if [ $main_IP_new_ass == $patif ]; then
              logit "main AF IP changed for $ass_po_name"
            else
              logit "main AF IP not changed for $ass_po_name, please intervene manually"
            fi
            #cmd ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "rm -rf ~/eric-ec-af_$ass_helm_name"
          fi
        fi
      fi
    done < $logdir/assistant_AF.txt
  else
    logit "old passive AF $papnf not converted to new main AF sucessfully,check manually"
    exit 1
  fi
  # remove old main AF from AFServerManager
  cmd ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -n $namespace -- /opt/af/bin/AFServerManager -r -as $matif"

  matif_p=$(ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -n $namespace -- /opt/af/bin/AFServerManager -p -as" | grep "$matif" | awk -F " " '{ print $NF}')

  if [ "$matif_p" == "$matif" ]; then
    logit "Unable to remove old main AF IP from new main AF,intervene manually"
    ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -n $namespace -- /opt/af/bin/AFServerManager -p -as"
  fi


  countdown 2
  # run configure -ud command in new main AF
  cmd ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -n $namespace -- /opt/af/bin/configure -ud"
  if [ $? != "0" ]; then
    logit "Unable to run /opt/af/bin/configure -ud in $papnf, PLease intervene manually"
    exit 1
  fi

  # run configure -ud command in all assistants
  while read line
  do
    ass_po_name=$(echo $line | awk -F " " '{print $2}')
    ass_acc_server_ip=$(echo $line | awk -F " " '{print $6}')
    assfu=$(echo $line | awk '{print $7}')
    ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "hostname"
    if [ $? != "0" ]; then
      logit "Unable to ssh to $ass_po_name access server IP $ass_acc_server_ip"
    else
      ass_k_path=$(ssh -o StrictHostKeyChecking=no -q ec01afgeored@$ass_acc_server_ip "source .bash_profile && which kubectl")
      cmd ssh -q -o StrictHostKeyChecking=no ec01afgeored@$ass_acc_server_ip "$ass_k_path exec -it $ass_po_name -n $namespace -- /opt/af/bin/configure -ud"
    fi
  done < $logdir/assistant_AF.txt

  new_main_AF_IP=$(ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -n $namespace -- /opt/af/bin/AFServerManager -p -as | grep \"af01.cs.\"|awk -F \" \" '{print \$NF}'")
  new_main_AF_IP_named=$(ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -n $namespace -- cat /etc/opt/af/named.conf | grep \"masters theMains\" -A1 | paste - - | awk -F \" \" '{print \$NF}' | sed 's/\;//g'")
  #cat /etc/opt/af/named.conf | grep Main -A1 ;
  if [[ ($new_main_AF_IP == $patif) && ($new_main_AF_IP_named == $patif) ]]; then
    # update the $i_file file
    logit "updating input file with correct AF entries"
    cmd "sed -i 's/mainAF/mainAF_old/g' $i_file"
    cmd "sed -i 's/passiveAF/mainAF_new/g' $i_file"
    cmd "sed -i 's/mainAF_old/passiveAF/g' $i_file"
    cmd "sed -i 's/mainAF_new/mainAF/g' $i_file"
    af_switch_rec=$(echo 1000)
  else
    logit "Input file not changed"
    exit 1
  fi

  #logit "trigger to EO for AF failover"
  for i in 1 2 3
  do
    cmd "curl -k --request POST 'https://ecmha4.vcc.t-mobile.lab/custom_wf-cnf-service-aap/cnf/upgrade/afnodes/start'" > $logdir/EO_trigger.txt
    if [ $(cat $logdir/EO_trigger.txt | awk -F "\"" '{print $4}') == 200 ] && [ $(cat $logdir/EO_trigger.txt | awk -F "\"" '{print $15}' | sed 's/\\//g') == $pahcdnf ] && [ $(cat $logdir/EO_trigger.txt | awk -F "\"" '{print $27}' | sed 's/\\//g') == $mahcdnf ]; then
      logit "trigger to EO for AF failover sucessful"
      cat $logdir/EO_trigger.txt
      #rec=$(echo 1000)
      break
    else
      logit "trigger to EO for AF failover not sucessful, please check manually, please check $logdir/EO_trigger.txt"
      cat $logdir/EO_trigger.txt
    fi
  done
fi
}


function planned {
  case $1 in
 failover)
    logit "running planned failover"
    ssh_main_AF "$k_ab_path_main_AF exec -it $mapnf -- test -f /var/opt/af/.inMaintenance"
    if [ $? == "0" ]; then
      cmd "ssh_main_AF \"$k_ab_path_main_AF exec -it $mapnf -- /opt/af/bin/accountfinder stop\""
      logit "wait for $mapnf pod status to 0/1"
      #cmd "countdown 300"
    else
      cmd "ssh_main_AF \"$k_ab_path_main_AF exec -it $mapnf -- touch /var/opt/af/.inMaintenance\""
      cmd "ssh_main_AF \"$k_ab_path_main_AF exec -it $mapnf -- /opt/af/bin/accountfinder stop\""
      logit "wait for $mapnf pod status to 0/1"
      #cmd "countdown 300"
    fi
    logit "checking main AF PO status"
    for i in 1 2 3 4 5 6 7 8 9 10
    do
      ssh_main_AF $k_ab_path_main_AF get po -n $namespace $mapnf | tail -1 | awk -F " " '{print $2}' > $logdir/tmp.txt
      if [ "$( cat $logdir/tmp.txt )" != "0/1" ]; then
        logit "main AF still Up,wait for next 1 min"
        cmd "countdown 60"
        ps=$(echo 200)
      else
        logit "main AF pod status is `cat $logdir/tmp.txt`"
        ps=$(echo 100)
        break
      fi
    done
    if [ $ps == "200" ]; then
      logit "$mapnf POD status is not 0/1"
      exit 1
    fi
    ;;
  fallback)
    logit "running planned fallback"
    ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -- test -f /var/opt/af/.inMaintenance"
    if [ $? == "0" ]; then
      cmd "ssh_pass_AF \"$k_ab_path_passive_AF exec -it $papnf -- rm -rf /var/opt/af/.inMaintenance\""
      cmd "ssh_pass_AF \"$k_ab_path_passive_AF exec -it $papnf -- /opt/af/bin/accountfinder start\""
      logit "wait for $papnf pod status to 1/1"
      #cmd "countdown 300"
    else
      cmd "ssh_pass_AF \"$k_ab_path_passive_AF exec -it $papnf -- /opt/af/bin/accountfinder start\""
      logit "wait for $papnf pod status to 1/1"
      #cmd "countdown 300"
    fi
    for i in 1 2 3 4 5 6 7 8 9 10
    do
      ssh_pass_AF $k_ab_path_passive_AF get po -n $namespace $papnf | tail -1 | awk -F " " '{print $2}' > $logdir/tmp.txt
      if [ $( cat $logdir/tmp.txt ) != "1/1" ]; then
        logit "passive AF still not Up,wait for next 1 min"
        cmd "countdown 60"
        ps=$(echo 200)
      else
        logit "passive AF pod status is `cat $logdir/tmp.txt`"
        ps=$(echo 100)
        break
      fi
    done
    if [ $ps == "200" ]; then
      logit "$papnf POD status is not 1/1"
      exit 1
    fi
    ;;
  esac
}

function switchover {
  logit "Running planned failover"
  logit "checking main AF $mapnf & $papnf POD status"

  ssh_main_AF $k_ab_path_main_AF get po -n $namespace $mapnf | tail -1 > $logdir/tmp.txt
  if [ $( cat $logdir/tmp.txt | awk -F " " '{print $2}' ) == "1/1" ]; then
    logit "main AF $mapnf POD status OK"
    cat $logdir/tmp.txt
    echo -e "\n"
    logit "checking passive AF $papnf POD status"
    ssh_pass_AF $k_ab_path_passive_AF get po -n $namespace $papnf | tail -1 > $logdir/tmp.txt
    if [ $( cat $logdir/tmp.txt | awk -F " " '{print $2}') == "1/1" ]; then
      logit "passive AF $papnf POD status OK"
      rec=$(echo 500)
    else
      logit "passive AF POD status is not OK"
      cat $logdir/tmp.txt
      echo -e "\n"
      logit "can not run planned failover"
      exit 1
    fi
  else
    logit "main AF POD status is not OK"
    cat $logdir/tmp.txt
    echo -e "\n"
    logit "can not run planned failover"
    exit 1
  fi

  if [ $rec == "500" ]; then
    logit "making main AF $mapnf pod status 0/1"
    ssh_main_AF "$k_ab_path_main_AF exec -it $mapnf -- test -f /var/opt/af/.inMaintenance"
      if [ $? == "0" ]; then
        cmd "ssh_main_AF \"$k_ab_path_main_AF exec -it $mapnf -- /opt/af/bin/accountfinder stop\""
        logit "wait for $mapnf pod status to 0/1"
      else
        cmd "ssh_main_AF \"$k_ab_path_main_AF exec -it $mapnf -- touch /var/opt/af/.inMaintenance\""
        cmd "ssh_main_AF \"$k_ab_path_main_AF exec -it $mapnf -- /opt/af/bin/accountfinder stop\""
        logit "wait for $mapnf pod status to 0/1"
      fi
      logit "checking main AF PO status"
      for i in 1 2 3 4 5 6 7 8 9 10
      do
        ssh_main_AF $k_ab_path_main_AF get po -n $namespace $mapnf | tail -1 | awk -F " " '{print $2}' > $logdir/tmp.txt
        if [ $( cat $logdir/tmp.txt ) != "0/1" ]; then
          logit "main AF still Up,wait for next 1 min"
          cmd "countdown 60"
          ps=$(echo 200)
        elif [ $( cat $logdir/tmp.txt ) == "0/1" ]; then
          logit "main AF pod status is 0/1"
          ps=$(echo 100)
          break
        else
          logit "unknown MAIN AF $mapnf status"
          exit 1
        fi
      done
      if [ $ps == "200" ]; then
        logit "$mapnf POD status is not 0/1"
        logit "unable to run planned failover,intervene manually"
        exit 1
      elif [ $ps == "100" ]; then
        logit "converting passive AF to main AF"
        af_switch
      else
        logit "Unknown error, Please check manually"
      fi
  fi

  if [ $af_switch_rec == "1000" ]; then
    logit "$papnf converted to new main AF"
    #validate_input
    define_variables
    logit "checking main AF $mapnf & passive AF $papnf PO status"
    ssh_main_AF $k_ab_path_main_AF get po -n $namespace $mapnf | tail -1 > $logdir/tmp.txt
    if [ "$( cat $logdir/tmp.txt | awk -F " " '{print $2}' )" == "1/1" ]; then
      logit "main AF $mapnf POD status OK"
      cmd ssh_main_AF $k_ab_path_main_AF get po -n $namespace $mapnf
      echo -e "\n"
      logit "checking passive AF $papnf is not added in main AF $mapnf"
      passive_AF_in_main_AF=$(ssh_main_AF "$k_ab_path_main_AF exec -it $mapnf -- /opt/af/bin/AFServerManager -p -as | grep $patif | awk -F \" \" '{print \$NF}'")
      if [ "$passive_AF_in_main_AF" == "$patif" ]; then
        logit "Passive AF $papnf is added in main AF, intervene manually"
        exit 1
      elif [ -z $passive_AF_in_main_AF ]; then
        logit "passive AF $papnf is not added in main AF"
        logit "checking passive AF $papnf POD status"
        ssh_pass_AF $k_ab_path_passive_AF get po -n $namespace $papnf | tail -1 > $logdir/tmp.txt
        if [ $( cat $logdir/tmp.txt | awk -F " " '{print $2}') == "0/1" ]; then
          logit "passive AF $papnf pod status is 0/1"
          logit "making $papnf POD status 1/1"
          ssh_pass_AF "$k_ab_path_passive_AF exec -it $papnf -- test -f /var/opt/af/.inMaintenance"
          if [ $? == "0" ]; then
            cmd "ssh_pass_AF \"$k_ab_path_passive_AF exec -it $papnf -- rm -rf /var/opt/af/.inMaintenance\""
            cmd "ssh_pass_AF \"$k_ab_path_passive_AF exec -it $papnf -- /opt/af/bin/accountfinder start\""
            logit "wait for $papnf pod status to 1/1"
          else
            cmd "ssh_pass_AF \"$k_ab_path_passive_AF exec -it $papnf -- /opt/af/bin/accountfinder start\""
            logit "wait for $papnf pod status to 1/1"
          fi
          for i in 1 2 3 4 5 6 7 8 9 10
          do
            ssh_pass_AF $k_ab_path_passive_AF get po -n $namespace $papnf | tail -1 | awk -F " " '{print $2}' > $logdir/tmp.txt
            if [ $( cat $logdir/tmp.txt ) != "1/1" ]; then
              logit "passive AF still not Up,wait for next 1 min"
              cmd "countdown 60"
              ps=$(echo 200)
            elif [ $( cat $logdir/tmp.txt ) == "1/1" ]; then
              logit "passive AF pod status is 1/1"
              ps=$(echo 100)
              break
            else
              logit "unknown passive AF $papnf status"
            fi
          done
          if [ $ps == "200" ]; then
            logit "$papnf POD status is not 1/1"
            logit "unable to run planned failover,intervene manually"
            exit 1
          elif [ $ps == "100" ]; then
            logit "converting $papnf to passive AF"
            convert_old_main_AF_to_passive
          else
            logit "Unknown error, Please check manually"
            exit 1
          fi
        elif [ $( cat $logdir/tmp.txt | awk -F " " '{print $2}') == "1/1" ]; then
          logit "passive AF pod status is 1/1"
          logit "converting $papnf to passive AF"
          convert_old_main_AF_to_passive
        else
          logit "Passive AF $papnf is not OK for failover, intervene manually"
        fi
      else
        echo "Please check input file af_deails.txt"
        exit 1
      fi
    else
      logit "main AF $mapnf POD status is not OK,Please intervene manually"
    fi
  fi
}

function main_check {
  for ((i=1; i<=$retrytime; i++))
  do
    logit "checking main AF $mapnf pod status"
    ssh_main_AF "hostname 1>/dev/null"
    if [ $? == 0 ]; then
      logit "main AF access server $maasif is reachable"

      ssh_main_AF "$k_ab_path_main_AF get po -n $namespace $mapnf" > $logdir/main_af_po_query.txt
      main_AF_po_status=$(cat $logdir/main_af_po_query.txt | tail -1 | awk -F " " '{print $2}')
      echo "$main_AF_po_status" >> $logdir/main_af_po_running.txt
      logit "Main AF $mapnf POD is $main_AF_po_status"

      ssh_main_AF "$k_ab_path_main_AF exec -n $namespace $mapnf -c main -- mount | grep scini" > $logdir/main_af_scini_volumes.txt
      [[ `grep '(ro,' $logdir/main_af_scini_volumes.txt` ]] && main_AF_volume_status="read-only" || main_AF_volume_status="read-write"
      logit "Main AF $mapnf Powerflex Volumes are $main_AF_volume_status"

      ssh_main_AF "$k_ab_path_main_AF exec -n $namespace $mapnf -c main -- sh -c 'nslookup 999999999.9.msisdn.sub.cs 127.0.0.1'" > $logdir/main_af_nslookup_output.txt 2>&1
      [[ `grep "server can't find 999999999" $logdir/main_af_nslookup_output.txt` ]] && main_af_nslookup_status="good" || main_af_nslookup_status="bad"
      logit "Main AF $mapnf nslookup functionality is $main_af_nslookup_status"
      
      if [ $main_AF_volume_status == "read-only" ]; then
        # Exit checking loop immediately
        break
      elif [ $main_AF_po_status == "1/1" ] && [ $main_af_nslookup_status == "bad" ]; then
        # Exit checking loop immediately
        break
      elif [ $main_AF_po_status != "1/1" ]; then
        logit "main AF $mapnf POD status is not OK"
        echo "main AF POD status is not OK $i" > $logdir/main_AF_po_status.txt
        if [ $i != $retrytime ]; then
          if [ "$pl" == "555" ]; then
            cmd "countdown 2"
          else
            if [ "$i" -le "3" ]; then
              cmd "countdown $sleeptime"
            else
              cmd "countdown 30"
            fi
          fi
        fi
      else
        logit "main AF $mapnf POD status is OK"
        logit "checking passive AF $papnf POD status"
        ssh_pass_AF "$k_ab_path_passive_AF get po -n $namespace $papnf" > $logdir/passive_af_po_query_aft_main_AF.txt
        pass_AF_po_status=$(cat $logdir/passive_af_po_query_aft_main_AF.txt | tail -1 | awk -F " " '{print $2}')

        if [ $pass_AF_po_status == "1/1" ]; then
          logit "passive AF $papnf POD status is OK"
          echo "Passive AF $papnf OK $i" > $logdir/passive_AF_po_status_aft_main_AF.txt

          if [ $i != $retrytime ]; then
            if [ "$pl" == "555" ]; then
              cmd "countdown 2"
            else
              if [ "$i" -le "3" ]; then
                cmd "countdown $sleeptime"
              else
                cmd "countdown 30"
              fi
            fi
          fi
        else
          logit "passive AF $papnf POD status not OK"
          if [ $i != $retrytime ]; then
            if [ "$pl" == "555" ]; then
              cmd "countdown 2"
            else
              if [ "$i" -le "3" ]; then
                cmd "countdown $sleeptime"
              else
                cmd "countdown 30"
              fi
            fi
          fi
        fi
      fi
    else
      logit "main AF access server $maasif is not reachable"
      logit "checking external service"
      #external service taken as variable
      cmd "for i in $ext_svc_url; do curl $i; done > $logdir/ext_opt.txt"
      main_AF_po_status=$(cat $logdir/ext_opt.txt | awk -F '[][]' '{print $4}' | awk -F '[}{]' -v ORS='\n' '{ for (i = 1; i <= NF; i++) print $i }'| sed 's/^,//g' | grep -v "^$" | grep "$mapnf" | sed 's/\"//g' | awk -F "," '{print $2}' | awk -F ":" '{print $2}' )
      echo "$main_AF_po_status" >> $logdir/main_af_po_running.txt
      if [ $main_AF_po_status != "1/1" ]; then
        logit "main AF $mapnf POD status is not OK"
        echo "main AF POD status is not OK $i" > $logdir/main_AF_po_status.txt
        if [ $i != $retrytime ]; then
          if [ "$pl" == "555" ]; then
            cmd "countdown 2"
          else
            if [ "$i" -le "3" ]; then
              cmd "countdown $sleeptime"
            else
              cmd "countdown 30"
            fi
          fi
        fi
      else
        logit "main AF $mapnf POD status is OK"
        logit "checking passive AF $papnf POD status"
        ssh_pass_AF "$k_ab_path_passive_AF get po -n $namespace $papnf" > $logdir/passive_af_po_query_aft_main_AF.txt
        pass_AF_po_status=$(cat $logdir/passive_af_po_query_aft_main_AF.txt | tail -1 | awk -F " " '{print $2}')

        if [ $pass_AF_po_status == "1/1" ]; then
          logit "passive AF $papnf POD status is OK"
          echo "Passive AF $papnf OK $i" > $logdir/passive_AF_po_status_aft_main_AF.txt

          if [ $i != $retrytime ]; then
            if [ "$pl" == "555" ]; then
              cmd "countdown 2"
            else
              if [ "$i" -le "3" ]; then
                cmd "countdown $sleeptime"
              else
                cmd "countdown 30"
              fi
            fi
          fi
        else
          logit "passive AF $papnf POD status not OK"
          if [ $i != $retrytime ]; then
            if [ "$pl" == "555" ]; then
              cmd "countdown 2"
            else
              if [ "$i" -le "3" ]; then 
                cmd "countdown $sleeptime"
              else
                cmd "countdown 30"
              fi
            fi
          fi
        fi
      fi
    fi
  done

  if [[ ( -f $logdir/passive_AF_po_status_aft_main_AF.txt ) && ( $(cat $logdir/passive_AF_po_status_aft_main_AF.txt | awk -F " " '{print $NF}') == $retrytime ) ]]; then
    ssh_main_AF "$k_ab_path_main_AF exec -it $mapnf -- /opt/af/bin/accountfinder status"
    if [ $? == "0" ]; then
      passive_AF_in_main_AF=$(ssh_main_AF "$k_ab_path_main_AF exec -it $mapnf -- /opt/af/bin/AFServerManager -p -as | grep $patif | awk -F \" \" '{print \$NF}'")
        if [ "$passive_AF_in_main_AF" == "$patif" ]; then
          logit "Passive AF $papnf is added in main AF"
        elif [ -z $passive_AF_in_main_AF ]; then
          logit "passive AF $papnf is not added in main AF, converting old main AF to passive AF"
          convert_old_main_AF_to_passive
        else
          echo "Please check input file af_deails.txt"
        fi
    else
      logit "main AF $mapnf account finder service is not running, can not convert old main AF to new passive AF"
    fi
  fi

  if [ ! -f $logdir/main_AF_po_status.txt ]; then
    exit 1
  else
    main_af_po_stat_aft_600=$(cat $logdir/main_AF_po_status.txt | awk -F " " '{print $NF}')
    if [ $main_af_po_stat_aft_600 != $retrytime  ]; then
      exit 1
    elif [[ $main_af_po_stat_aft_600 == $retrytime && $(cat $logdir/main_af_po_running.txt | grep "0/1" | wc -l) == $retrytime ]]; then
      logit "main AF $mapnf POD status not OK for $retrytime times"
      logit "checking passive AF $papnf POD status"
      for j in 1 2 3
      do
        ssh_pass_AF "$k_ab_path_passive_AF get po -n $namespace $papnf" > $logdir/passive_af_po_query.txt
        pass_AF_po_status=$(cat $logdir/passive_af_po_query.txt | tail -1 | awk -F " " '{print $2}')
        if [ $pass_AF_po_status != "1/1" ]; then
          echo "passive AF is not healthy $j" > $logdir/passive_AF_po_status.txt
          if [ $j != "3" ]; then
            if [ "$pl" == "555" ]; then
              cmd "countdown 1"
            else
              cmd "countdown 60"
            fi
          fi
        elif [ $pass_AF_po_status == "1/1" ]; then
          logit "passive AF $papnf POD status 1/1"
          if [ $j != "3" ]; then
            if [ "$pl" == "555" ]; then
              cmd "countdown 1"
            else
              cmd "countdown 60"
            fi
          fi
        else
          logit "unknown passive AF $papnf POD status"
        fi
      done

      if [ -f $logdir/passive_AF_po_status.txt ]; then
        passive_af_po_stat_aft_60=$(cat $logdir/passive_AF_po_status.txt | awk -F " " '{print $NF}')
      fi

      if [ ! -f $logdir/passive_AF_po_status.txt ]; then
        logit "Passive AF OK for failover"
        logit "converting passive AF to main AF"
        af_switch
        #rc =$(echo $?)
        #echo "af_switch rc is $rc"
      elif [ $passive_af_po_stat_aft_60 != "3" ]; then
        logit "Passive AF OK for failover"
        logit "converting passive AF to main AF"
        af_switch
      else
        logit "passive AF is not OK for failover, existing"
        exit 1
      fi
    else
      echo -e "\n"
    fi
  fi
#       cmd timeout 5 ssh -o StrictHostKeyChecking=no -q ec01afgeored@$paasif "rm -rf ~/eric-ec-af_$pahcdnf"
#       cmd timeout 5 ssh -o StrictHostKeyChecking=no -q ec01afgeored@$maasif "rm -rf ~/eric-ec-af_$pahcdnf"
rm -rf $logdir/main_af_po_running.txt
}

#validate_input
logit "current main AF in $i_file $(cat $i_file | grep mainAF| awk -F " " '{print $2}')"
#cdd_handler
#define_variables

if [ "$1" == "planned" ]; then
  pl=$(echo 555)
  if [ "$2" == "failover" ]; then
    validate_input
    define_variables
    planned failover
    main_check
  elif [ "$2" == "fallback" ]; then
    validate_input
    define_variables
    planned fallback
    main_check
  else
    echo -e "\n"
    define_variables
    main_check
  fi
elif [ "$1" == "switchover" ]; then
  validate_input
  define_variables
  switchover
elif [ -z "$1" ]; then
  define_variables
  main_check
elif [ "$mainaf_down" == "200" ]; then
  pl=$(echo 555)
  validate_input
  define_variables
  planned failover
  main_check
else
  logit "unknown option"
  exit 1
fi

logit "removing older log files than 7 days"
cmd "find '$logdir' -type f -name '*.log' -mtime +'7' -exec rm {} \;"