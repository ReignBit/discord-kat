import discord


def is_author(bot, user_id):
    if user_id == bot.app_info.owner or user_id == 328532230055919616:
        return True
    return False

def has_permission(bot, user: discord.Member, channel: discord.TextChannel, permission: str):
    if user.id == bot.app_info.owner.id:
        return True
    for perm,value in iter(user.permissions_in(channel)):
        if (perm == permission and value is True) or (perm == "administrator" and value is True):
            return True
    return False
