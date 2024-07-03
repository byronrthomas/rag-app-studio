import os
import secrets
import shutil


def make_temp_folder():
    temp_folder = f"/tmp/test_{secrets.token_hex(4)}"
    os.makedirs(temp_folder, exist_ok=False)
    return temp_folder


def cleanup_temp_folder(temp_folder):
    shutil.rmtree(temp_folder)
    return
