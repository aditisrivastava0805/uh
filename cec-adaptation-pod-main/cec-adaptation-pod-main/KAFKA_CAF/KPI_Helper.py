import glob
import logging
import os
import time
import re
from datetime import datetime, timedelta
from typing import List


def banner(text: str):
    return f"""{'-' * 20}  {text}  {'-' * 20}"""


def files_newer_that_mins(dir: str, file_pattern: str, newer_than_mins: int) -> List[str]:
    logging.info(banner(f"Selecting files {file_pattern} in {dir} newer than {newer_than_mins} minutes"))
    file_paths = []
    current_time = time.time()

    for file_path in glob.glob(os.path.join(dir, file_pattern)):
        time_delta = current_time - os.path.getmtime(file_path)
        if (time_delta / 60) < newer_than_mins:
            file_paths.append(file_path)

    return file_paths

def files_newer_that_mins_latest(dir: str, file_pattern: str, newer_than_mins: int) -> List[str]:
    logging.info(banner(f"Selecting files {file_pattern} in {dir} newer than {newer_than_mins} minutes"))
    file_paths = []

    now = datetime.now()
    fifteen_minutes_ago = now - timedelta(minutes=newer_than_mins)

    logging.info(f"Current Time: {now.strftime('%Y-%m-%d %H:%M')}")
    logging.info(f"15 Minutes Ago: {fifteen_minutes_ago.strftime('%Y-%m-%d %H:%M')}")

    # Match XML files
    file_pattern = os.path.join(dir, file_pattern)
    for file_path in sorted(glob.glob(file_pattern)):  # Ensure correct order
        filename = os.path.basename(file_path)

        # Extract timestamps using regex
        match = re.search(r'A(\d{8})\.(\d{4})-.*-(\d{4})-', filename)
        if not match:
            logging.info(f"Skipping invalid file: {filename}")
            continue

        date_part = match.group(1)  # YYYYMMDD
        start_time = match.group(2)  # HHMM (start)
        end_time = match.group(3)  # HHMM (end)

        # Convert extracted times to datetime objects
        file_start_datetime = datetime.strptime(date_part + start_time, "%Y%m%d%H%M")
        file_end_datetime = datetime.strptime(date_part + end_time, "%Y%m%d%H%M")

        logging.info(f"Checking file: {filename} | Start: {file_start_datetime} | End: {file_end_datetime}")

        # Check if the file falls within the last 15 minutes
        if file_end_datetime >= fifteen_minutes_ago:
            logging.info(f"Including: {filename}")
            file_paths.append(file_path)
        else:
            logging.info(f"Excluding: {filename} (Older than 15 min)")

    return file_paths

def delete_files_older_than_days(dir: str, days: int):
    logging.info(f'Deleting old files, dir: {dir}, days old: {days}')
    for f in os.listdir(dir):
        file_path = os.path.join(dir, f)
        file_time = datetime.fromtimestamp(os.stat(file_path).st_mtime)
        if os.path.isfile(file_path):
            if file_time < datetime.now() - timedelta(days=days):
                os.remove(file_path)

def is_http_ok(code: str):
    return True if code[0].isdigit() and int(code[0]) < 4 else False

def is_http_error(code: str):
    return True if code[0].isdigit() and int(code[0]) >= 4 else False
