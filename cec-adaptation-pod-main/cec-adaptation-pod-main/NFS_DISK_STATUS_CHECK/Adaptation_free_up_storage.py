# importing the os module
import json
import os

import subprocess
import logging

script_home = os.path.dirname(os.path.realpath(__file__))
max_percentage = 70
logging.basicConfig(filename=f'{str(script_home)}/Adaptation_to_free_up.runlog', filemode='w', format='%(asctime)s - %('
                                                                                                   'levelname)s - %('
                                                                                                   'message)s',
                    level=logging.INFO)

script_dir = os.path.dirname(__file__)
config_file_path = os.path.join(script_dir, 'Configuration_disk_usage.json')

with open(config_file_path, 'r') as json_file_data:
        config_file_data = json.loads(json_file_data.read())


def get_path(dir_path):
    pwd = os.getcwd()
    logging.info("cwd:%s" % os.getcwd())
    if pwd == dir_path:
        pass
    else:
        os.chdir(dir_path)
    dir_path = os.getcwd()
    return dir_path


# function that returns size of a file
def get_disk_size(dirPath):
    command = "df  " + dirPath + " | tail -1 |awk '{print $5}' | tr -d '%'"
    logging.info("cwd:%s" % os.getcwd())
    output = subprocess.check_output(command, shell=True)
    output = output.decode().strip()
    percentage_used_space = int(output)
    logging.info("percentage used: %s" % percentage_used_space)
    return percentage_used_space


# function to delete a file
def remove_file(filePath):
    try:
        # deleting the file
        os.remove(filePath)
        logging.info("file is deleted successfully:%s" % filePath)
    except Exception as err:
        # error
        logging.info("Unable to delete the file%s" % filePath)
        print(err)


def delete_empty_folders(folder_location):
    try:
        if os.path.exists(folder_location):
            for dirpath, dirnames, filenames in os.walk(folder_location, topdown=False):
                if not dirnames and not filenames:
                    os.rmdir(dirpath)
                    # success message
                    logging.info(f"{folder_location} is removed successfully")
                else:
                    # failure message
                    logging.info(f"Unable to delete the {folder_location}")
    except Exception as err:
        # error
        logging.info("Unable to delete the empty directory%s" % folder_location)
        print(err)


def main():

    dir_path = config_file_data["directory"]

    dirPath = get_path(dir_path)
    try:
        if get_disk_size(dirPath) >= config_file_data["max_percentage"]:
            # checking whether the path exists or not
            if os.path.exists(dirPath):
                print("exists:", os.path.exists(dirPath))
                for root_folder, folders, files in os.walk(dirPath):
                    if len(files) > 0:
                        for file in files:
                            remove_file(os.path.join(root_folder, file))
                    if get_disk_size(dirPath) <= config_file_data["check_percentage"]:
                        break

                print("deleting empty directory")

            else:
                logging.info("directory Path doesn't exist:%s" % dirPath)
                print("directory Path doesn't exist:%s" % dirPath)
            delete_empty_folders(dirPath)

        else:
            logging.info("disk size is capable")
            print(f"{dirPath} disk size is capable with {get_disk_size(dirPath)} %")
    except Exception as err:
        print(err)


if __name__ == '__main__':
    main()
