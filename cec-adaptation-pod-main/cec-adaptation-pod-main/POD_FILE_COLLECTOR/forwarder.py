import logging
import os.path
from typing import Tuple

import paramiko as paramiko

from kubernetes import Container, exec_kube, cont_str, select_containers
from proc2 import eval_value, convert_xml_gz_to_xml

def forward_files(src_file_paths: [], forward_structs: [], output_path: str):
    for fwd_struct in forward_structs:
        type = fwd_struct["TYPE"]

        if type == 'POD':
            container_pattern = fwd_struct["CONTAINER_PATTERN"]
            pod_pattern = fwd_struct["POD_PATTERN"]
            namespace_pattern = fwd_struct["NAMESPACE_PATTERN"]
            hostname = eval_value(fwd_struct["HOSTNAME"])
            username = fwd_struct["USERNAME"]
            password = fwd_struct["PASSWORD"]
            dest_folder = fwd_struct["DESTINATION_FOLDER"]
            file_retention_days = fwd_struct['FILE_RETENTION_DAYS']
            logging.info(f"Forwarding files to host: {hostname}, type: {type}, cont: {container_pattern}, pos: {pod_pattern}, ns: {namespace_pattern}")

            for cont in select_containers(container_pattern, pod_pattern, namespace_pattern):
                forward(src_file_paths, dest_folder, file_retention_days, cont, hostname, username, password, output_path)

        else:
            logging.error(f"Unexpected forwarder type {type}")

def user_and_group_id(username: str, cont: Container) -> Tuple[int, int]:
    logging.info(f"Fetching UID and GID from container: {cont_str(cont)}")

    cmd = f"""getent passwd {username} | awk -F':' '{{print $3 "," $4}}'"""
    out, err, exit_code = exec_kube(cmd, cont)

    if err:
        logging.error(f"Failed to fetch user and group ID from cont: {cont_str(cont)}, error: {err}")
        return 0, 0

    uid_and_gid = out.split(",")

    if len(uid_and_gid) != 2:
        logging.error(f"Failed to fetch user and group ID from cont: {cont_str(cont)}, result: {uid_and_gid}")
        return 0, 0

    return int(uid_and_gid[0]), int(uid_and_gid[1])


def delete_old_files(cont: Container, folder: str, file_retention_days: int):
    logging.info(f"Deleting files older than {file_retention_days} days in folder: {folder}, cont: {cont_str(cont)}")

    cmd = f"sudo find {folder} -maxdepth 1 -type f -mtime +{file_retention_days} -exec rm -rf {{}} \;"
    out, err, exit_code = exec_kube(cmd, cont)

    if err:
        logging.error(f"Failed deleting old files in folder: {folder}, cont: {cont_str(cont)}, error: {err}")


def forward(src_file_paths: [], dest_folder: str, file_retention_days, cont: Container, hostname, username, password, output_path: str):
    uid, gid = user_and_group_id(username, cont)

    delete_old_files(cont, dest_folder, file_retention_days)

    with paramiko.SSHClient() as ssh:
        logging.info(f"SFTP: {username}@{hostname}")
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password)
        with ssh.open_sftp() as sftp:
            for src_file_path in src_file_paths:
                try:
                    # Covert XML.GZ to .XML
                    xml_file_with_path = convert_xml_gz_to_xml(src_file_path, output_path)
                    filename = os.path.basename(xml_file_with_path)

                    dest_file_path = os.path.join(dest_folder, filename)
                    dest_file_path_tmp = os.path.join(dest_file_path + '.tmp')

                    logging.info(f"Transferring file: {src_file_path}  and New xml path : {xml_file_with_path} --> {dest_file_path_tmp}")
                    try:
                        sftp.mkdir(dest_folder)
                        logging.info(f"Directory created: {dest_folder}")
                    except IOError:
                        pass

                    sftp.put(xml_file_with_path, dest_file_path_tmp)

                    logging.info(f"Setting file owner: {dest_file_path_tmp}, UID: {uid}, GID: {gid}")
                    sftp.chown(dest_file_path_tmp, uid, gid)

                    logging.info(f"Renaming file: {dest_file_path_tmp} --> {filename}")
                    try:
                        sftp.rename(dest_file_path_tmp, dest_file_path)
                    except Exception as ex:
                        logging.info(f"File already exists on destination, file: {os.path.basename(src_file_path)}")
                        sftp.remove(dest_file_path_tmp)

                    logging.info(f"File {filename} uploaded to: {hostname}:/{dest_folder}, file UID: {uid}, GID: {gid}")

                    # os.remove(xml_file_with_path)
                except Exception as ex:
                    logging.exception(f"Failed transferring file {os.path.basename(src_file_path)}")

