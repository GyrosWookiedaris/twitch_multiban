# Start Import ---------------------------------------------------------------------------------- Start Import
from sys import exit
import socket
import ssl
import os
from time import sleep
from datetime import datetime
import configparser

# End Import -------------------------------------------------------------------------------------- End Import

config = configparser.ConfigParser()

try:
    with open("config.ini", "r") as configfile:
        print("Config found! Skipping config creation!")
    config.read('config.ini')
    print("Reading config values.....")
    twitchhost = config['TWITCH']['host']
    twitchport = config['TWITCH']['port']
    streamer = config['CHANNEL']['streamer']
    user = config['CHANNEL']['user']
    token = config['CHANNEL']['token']
    action = config['ACTION']['action']
    reason = config['ACTION']['reason']
    max_action_in_row = config['ACTION']['max_action_in_row']
    action_per_minute = config['ACTION']['action_per_minute']
    action_pause = config['ACTION']['action_pause']
    print("Following values were read, press Enter to confirm, press CTRL+C to abort.")
    print("----------------------------------------------------------")
    print(f"Target channel: {streamer}")
    print(f"User which executes ban: {user}")
    print(f"Token for the executing user: oauth:{token}")
    print("----------------------------------------------------------")
    print(f"Action (allowed: ban, unban): {action}")
    print(f"Reason: {reason}")
    print(f"Max actions in row: {max_action_in_row}")
    print(
        f"Actions per minute (as moderator the cap before getting yourself banned is 200 per minute): {action_per_minute}")
    print(f"Pause between max actions in row: {action_pause}")
    try:
        input("Press enter to accept. ")
        print(1 * "\n")
    except KeyboardInterrupt:
        print(3 * "\n")
        print("Stopping kinda gracefully, have a nice day!")
        sleep(2)
        exit()

except IOError:
    default_twitch_host = "irc.chat.twitch.tv"
    default_twitch_port = 6697
    default_action = "ban"
    default_reason = "followbot"
    default_action_per_minute = 100
    default_max_action_in_row = 100
    default_action_pause = 30
    default_streamer = "ENTERSTREAMERNAMEHERE"
    default_user = "ENTERUSERHERE"
    default_token = "oauth:ENTERCHATTOKENHERE"

    print("No config present, creating new config!")
    streamer = input("Enter streamer name/target channel (lowercase): ") or default_streamer
    user = input("Enter the user that executes the action (lowercase): ") or default_user
    token = input(
        "Enter the twitch chat token (You may generate the token here: https://twitchapps.com/tmi/): ") or default_token
    action = input(
        "Enter action to perform. Tested actions are ban and unban. Defaults to 'ban' (leave blank for default): ") or default_action
    reason = input("Enter reason. Defaults to 'followbot' (leave blank for default): ") or default_reason
    action_per_minute = int(input(
        "Enter actions per minute (as moderator the cap before getting yourself banned is 200 per minute). Defaults to 100 (leave blank for default): ") or default_action_per_minute)
    max_action_in_row = int(input(
        "Enter max actions performed in row. Defaults to 100 (leave blank for default): ") or default_max_action_in_row)
    action_pause = int(input(
        "Enter pause after max action threshold is reached. Defaults to 100 (leave blank for default): ") or default_action_pause)

    if token.startswith("oauth:"):
        token = token.split(":")
        token = token[1]

    twitchhost = default_twitch_host
    twitchport = default_twitch_port

    with open("config.ini", "w") as configfile:
        config['TWITCH'] = {
            "host": default_twitch_host,
            "port": default_twitch_port,
        }
        config['CHANNEL'] = {
            "streamer": streamer,
            "user": user,
            "token": token,
        }
        config['ACTION'] = {
            "action": action,
            "reason": reason,
            "action_per_minute": action_per_minute,
            "max_action_in_row": max_action_in_row,
            "action_pause": action_pause
        }
        config.write(configfile)
finally:
    configfile.close()

try:
    with open('banlist.txt', 'r') as file:
        print("Banlist found")
        print(3 * "\n")
        file.close()
except IOError:
    print("No banlist found. Creating empty banlist. Enter one user per line.")
    with open('banlist.txt', 'w') as file:
        print("Created list. Fill the list and restart the program.")
        sleep(3)
        file.close()
    exit()


# Start IRC Class ---------------------------------------------------------------------------- Start IRC Class
class IRCSendOnly:
    host = twitchhost
    port = twitchport
    botname = user
    auth = f"oauth:{token}"
    channel = f"#{streamer}"

    def __init__(self):
        with socket.create_connection((self.host, self.port), timeout=360) as socket_con:
            self.con = ssl.create_default_context().wrap_socket(socket_con, server_hostname=self.host)
        self.send_pass()
        self.send_bot_user()
        self.send_cap()
        self.join_channel()

    def close(self):
        self.con.close()

    def send(self, data):
        self.con.send(bytes(data, "utf-8"))

    def receive(self):
        return self.con.recv(1024).decode(encoding="utf-8", errors="ignore")

    def send_bot_user(self):
        self.send("NICK {}\r\n".format(self.botname))

    def send_pass(self):
        self.send("PASS {}\r\n".format(self.auth))

    def send_cap(self):
        self.send("CAP REQ :twitch.tv/membership\r\n")
        self.send("CAP REQ :twitch.tv/commands\r\n")
        self.send("CAP REQ :twitch.tv/tags\r\n")

    def join_channel(self):
        self.send("JOIN {}\r\n".format(self.channel))

    def part_channel(self):
        self.send("PART {}\r\n".format(self.channel))

    def send_message(self, message):
        self.send("PRIVMSG {} :{}\r\n".format(self.channel, message))


# End IRC Class -------------------------------------------------------------------------------- End IRC Class

irc = IRCSendOnly()
file = open('banlist.txt', 'r')
users = file.readlines()
bancount = 0
allcount = 0
sleepmod = 60 / int(action_per_minute)


def do_things(action, user):
    if action == "ban":
        irc.send_message(f"/{action} {user} {reason}")
        print(f"Banned {user}")
    elif action == "unban":
        irc.send_message(f"/{action} {user}")
        print(f"Unbanned {user}")


for user in users:
    if bancount < int(max_action_in_row):
        user = user.rstrip()
        do_things(action, user)
        bancount += 1
        allcount += 1
        sleep(sleepmod)
    else:
        user = user.rstrip()
        do_things(action, user)
        bancount = 0
        allcount += 1
        sleep(int(action_pause))

print(3 * "\n")
print(f"Successfully done things to {allcount} users")
file.close()
irc.close()
sleep(5)
print("Renaming banlist and creating new empty list")
dt_string = datetime.now().strftime("%Y%m%d_%H%M%S")
new_name = f"banlist_{dt_string}.txt"
os.rename('banlist.txt', new_name)
with open('banlist.txt', 'w') as file:
    file.close()
end = input("Press enter to exit.")
exit()