import logging
import os.path
from typing import Optional, List


def collect_files(source_folder, number_of_last_updated_files) -> Optional[List[str]]:
    # Get all files in the directory with their modification times
    try:
        all_files = []
        for f in os.listdir(source_folder):
            file_path = os.path.join(source_folder, f)
            if os.path.isfile(file_path):
                all_files.append((file_path, os.path.getmtime(file_path)))

        if not all_files:
            logging.info("No files found in the folder.")
            return []

        # Sort files by modification time (most recent first)
        all_files.sort(key=lambda x: x[1], reverse=True)

        # Get the last `num_files` updated files
        latest_files = [file for file, _ in all_files[:number_of_last_updated_files]]

        logging.info(f"Latest {number_of_last_updated_files} modified files: {latest_files}")
        return latest_files

    except Exception as e:
        logging.error(f"Error processing folder '{source_folder}': {e}")
        return []
