import os
from collections import deque


def tail_logs(log_directory, n):
    # List all log files, sorted by modification time or name if they include a sequence
    log_files = sorted(
        [f for f in os.listdir(log_directory) if f.startswith("application.log")],
        key=lambda x: os.path.getmtime(os.path.join(log_directory, x)),
    )

    # A deque is used to keep the last n lines
    lines = deque(maxlen=n)

    # Iterate over files in reverse order (most recent first)
    for log_file in reversed(log_files):
        with open(os.path.join(log_directory, log_file), "r") as file:
            # Read file lines to a list
            file_lines = file.readlines()

            # If the number of lines needed is less than the file's line count
            if len(file_lines) >= n - len(lines):
                # Calculate how many lines to take from this file
                needed_lines = n - len(lines)
                # Extend the deque with the last needed_lines from the file
                lines.extendleft(reversed(file_lines[-needed_lines:]))
                break  # Stop reading more files, as we have enough lines
            else:
                # If not enough lines, add all lines from this file and continue to the next
                lines.extendleft(reversed(file_lines))

    # Convert deque to list and return
    return list(lines)
