import gzip
import json
import os
import importlib
import random
import sys
import psutil
import hashlib

from discord.ext.commands import errors, Cog

def compress_file(path):
    """Takes a file and compresses it using g-zip, returns bytes"""
    with open(path, "rb") as f:
        compressed = gzip.compress(f.read())
    return compressed


def write_resource(filepath: str, data):
    """Write data to a resource file filepath located in resources/"""
    with open("resources/" + filepath, "w") as f:
        f.write(data)


def read_resource(filepath: str):
    """Read data from a resource file filepath located in resources/"""
    if os.path.exists("resources/" + filepath):
        with open("resources/" + filepath, "r", encoding="utf-8") as f:
            return json.load(f)

# Cog loading and unloading
def load_cog(bot, cog) -> Cog:
    """Attempts to load a cog from 'cogs/'"""
    
    # format the cog name correctly so we can fetch the instance.
    # since bot.load_extension doesn't return the cog...
    # cog_name = ""
    # if "." in cog:
    #     _ = cog.split('.')
    #     for string in _:
    #         cog_name += string.capitalize()
    # else:
    #     cog_name = cog.capitalize()


    cog_name = cog.split('.')[-1].capitalize()

    try:
        bot.load_extension("cogs." + cog) # load the extension


        # loaded the cog.
        bot.log.info("Loaded %s." % cog_name)
        return cog_name,bot.get_cog(cog_name) 

    except errors.ExtensionError as err:
        bot.log.warn("Failed to load Cog: %s" % cog_name)
        bot.log.warn("re-raising exception: %s" % err)
        raise err

def unload_cog(bot, cog):
    """Attempts to unload a cog from 'cogs/'"""
    
    cog_name = cog.split('.')[-1].capitalize()

    bot.log.debug(cog_name)
    try:
        old_cog = bot.get_cog(cog_name)
        name = old_cog.qualified_name
        bot.unload_extension("cogs." + cog)
        
        bot.log.info("Unloaded %s" % cog_name)
        return name, old_cog
    except errors.ExtensionError as err:
        bot.log.crit("Failed to unload Cog: %s" % cog_name)
        bot.log.crit("re-raising exception: %s" % err)
        raise err


# System Metrics
def get_sys_cpu_usage():
    return psutil.cpu_percent() / psutil.cpu_count()


def get_kat_cpu_usage():
    p = psutil.Process(os.getpid())
    return p.cpu_percent() / psutil.cpu_count()


def get_sys_mem_usage():
    return "{}MB ({}%)".format(format(
        psutil.virtual_memory().used / 1048576, '.2f'), psutil.virtual_memory().percent)


def get_mem_usage():
    p = psutil.Process(os.getpid())
    _info = p.memory_info()
    return "{}MB ({}%)".format(
        format(float(_info.rss) / 1048576, '.2f'), format(p.memory_percent(), '.2f'))


def generate_checksum(file):        
        with open(file, 'rb') as f:
             return hashlib.md5(f.read()).hexdigest()


def generate_checksums(files):
    checksums = {}
    for file in files:
        checksums[file] = generate_checksum(file)
    return checksums
