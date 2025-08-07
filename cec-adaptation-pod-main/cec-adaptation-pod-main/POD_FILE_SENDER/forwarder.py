import logging
import os.path

import paramiko as paramiko

from proc2 import eval_value, convert_xml_gz_to_xml


def forward_files(src_file_paths: [], forward_structs: [], output_path: str, application_name_pattern: str):
    for fwd_struct in forward_structs:
        hostname = eval_value(fwd_struct["HOSTNAME"])
        username = fwd_struct["USERNAME"]
        password = fwd_struct["PASSWORD"]
        dest_folder = fwd_struct["DESTINATION_FOLDER"][application_name_pattern]
        logging.info(f"Forwarding files to host: {hostname}")

        forward(src_file_paths, dest_folder, hostname, username, password, output_path)


def forward(src_file_paths: [], dest_folder: str, hostname, username, password, output_path: str):
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

                    logging.info(
                        f"Transferring file: {src_file_path}  and New xml path : {xml_file_with_path} --> {dest_file_path_tmp}")
                    try:
                        sftp.mkdir(dest_folder)
                        logging.info(f"Directory created: {dest_folder}")
                    except IOError:
                        pass

                    sftp.put(xml_file_with_path, dest_file_path_tmp)

                    logging.info(f"Renaming file: {dest_file_path_tmp} --> {filename}")
                    try:
                        sftp.rename(dest_file_path_tmp, dest_file_path)
                    except Exception as ex:
                        logging.info(f"File already exists on destination, file: {os.path.basename(src_file_path)}")
                        sftp.remove(dest_file_path_tmp)

                    logging.info(f"File {filename} uploaded to: {hostname}:/{dest_folder}")

                    # os.remove(xml_file_with_path)
                except Exception as ex:
                    logging.exception(f"Failed transferring file {os.path.basename(src_file_path)}")
