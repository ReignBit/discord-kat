import requests

from discord.ext import commands

from bot.utils.extensions import KatCog
from bot.utils import constants


class Dyndns(KatCog):
    """Auto GoDaddy DNS Updater."""
    def __init__(self, bot):
        super().__init__(bot)
        self.hidden = True

        self.url = f"https://api.godaddy.com/v1/domains/{constants.Dyndns.domain}/records/A/@"
        self.session = requests.Session()

        self.session.headers.update(
            {'Authorization': 'sso-key ' + constants.Dyndns.key})

    def update_ips(self):
        ip = requests.get('https://api.ipify.org').text
        dad_ip = self.session.get(self.url).json()[0]['data']

        return ip, dad_ip

    @commands.Cog.listener()
    async def on_kat_hour_event(self):
        self.log.info("Updating IP...")
        self.current_ip, self.daddy_ip = self.update_ips()

        if self.daddy_ip != self.current_ip:
            self.log.info(
                "GoDaddy's DNS A record is not up to date! Attempting to change...")

            # Creates and executes the PUT request for DNS record type A for host @
            data = '[ { "data": "' + str(self.current_ip) + '" }]'
            res = self.session.put(self.url, data, headers={
                                    'Content-Type': 'application/json'})
            self.log.debug(res.status_code)
            if res.status_code == 200:
                self.log.info("Updated DNS Record. Checking if changed...")
                self.log.warn(res.status_code)
                self.log.debug(res)
            else:
                self.log.warn(
                    "Did not receive 200 status code. IP was probably not updated.")
            # Update current ip and godaddys ip
            self.current_ip, self.daddy_ip = self.update_ips()

            # Test to see if the request worked.
            if self.daddy_ip != self.current_ip:
                self.log.warn(
                    "GoDaddy DNS did not update successfully.")


def setup(bot):
    bot.add_cog(Dyndns(bot))
