"""metrics.py

Retrieve information about system.
    - CPU Usage (System wide & Process specific)
    - RAM Usage (System wide & Process specific)
    - MD5 Checksums
"""
import psutil
import hashlib
import os

def get_sys_cpu_usage():
    """Return total system CPU usage."""
    return psutil.cpu_percent() / psutil.cpu_count()


def get_proc_cpu_usage():
    """Return process CPU usage."""
    p = psutil.Process(os.getpid())
    return p.cpu_percent() / psutil.cpu_count()


def get_sys_mem_usage():
    """Return system RAM usage as a string."""
    return "{}MB ({}%)".format(format(
        psutil.virtual_memory().used / 1048576, '.2f'), psutil.virtual_memory().percent)


def get_proc_mem_usage():
    """Return process RAM usage as a string."""
    p = psutil.Process(os.getpid())
    _info = p.memory_info()
    return "{}MB ({}%)".format(
        format(float(_info.rss) / 1048576, '.2f'), format(p.memory_percent(), '.2f'))


def generate_checksum(file):
    """Return a MD5 checksum of filepath `file: str`."""
    with open(file, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def generate_checksums(files):
    """Return a list of MD5 checksums of filepaths `files: list`."""
    checksums = {}
    for file in files:
        checksums[file] = generate_checksum(file)
    return checksums
