import os
import time

from utils.Utilities import get_today_date, get_current_hour


class BufferedFileWriter:
    def __init__(self, master_dir_path, file_name_prefix, daily_only=False, flush_interval=1.0):
        self.master_dir_path = master_dir_path
        self.file_name_prefix = file_name_prefix
        self.flush_interval = flush_interval
        self.buffer = []
        self.daily_only = daily_only
        self.last_flush_time = time.monotonic()

    def append(self, data):
        self.buffer.append(data)

        # Flush the buffer if the flush interval has elapsed
        current_time = time.monotonic()
        if current_time - self.last_flush_time >= self.flush_interval:
            self.flush()

    def flush(self):
        # aggregate data houly into one file
        date_dir_name = get_today_date()
        if not self.daily_only:
            current_file_index = get_current_hour()
            file_path = os.path.join(
                self.master_dir_path, date_dir_name, f"{self.file_name_prefix}{current_file_index}")
        else:
            file_path = os.path.join(
                self.master_dir_path, f"{self.file_name_prefix}{date_dir_name}")
        # Create the directory if it doesn't exist
        dir_path = os.path.dirname(file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # Append the buffer to the file
        with open(file_path, "a") as f:
            f.write("\n".join(self.buffer))
            f.write("\n")
        self.buffer = []
        self.last_flush_time = time.monotonic()
