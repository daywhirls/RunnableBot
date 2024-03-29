import discord
import asyncio
import logging

from datetime import datetime
import pytz # Force datetime into EST since my server is UTC

from group_helpers import (
    balanceGroups,
    howManyGroups,
    calculateWeeklySchedule,
    swapGroups,
)
from ttr_helpers import verifyRole

from mongo_helpers import (
    addToQueue,
    removeFromQueue,
    toonExistsInDB,
    wipeDB,
    isDatabaseEmpty,
    getQueueAsList,
    logWeeklySchedule,
    getRunTimes
)

OFFICIAL_SCHEDULE_CHANNEL = 553493689880543242 # Cheese server's #weekly-schedule
OFFICIAL_ANNOUNCEMENTS_CHANNEL = 481295173113085973 # Cheese server's #announcements
TEST_CHANNEL = 553420403033505792 # Local test server's #run-queue

# TTRClient eats the arg it requires (token), then passes the rest
# onto discord.Client's __init__ (*args, **kwargs). in my case nothing
class TTRClient(discord.Client):
    def __init__(self, token, db, *args, **kwargs):
        self._token = token
        self._db = db
        self._logger = logging.getLogger(__name__)
        self.splits = []
        self.fireNums = []
        super(TTRClient, self).__init__(*args, **kwargs)
        #self.loop.create_task(self.schedulePoll())
        #self.loop.create_task(self.pingServerForRun())
        self.function_map = {
            "!add": self.add_message,
            "!queue": self.queue_message,
            "!split": self.split_message,
            "!wipe": self.wipe_message,
            "!remove": self.remove_message,
            "!swap": self.swap_message,
            "!help": self.help_message,
        }

    # calls discord.Client's run() function using _token
    def run(self, *args, **kwargs):
        super(TTRClient, self).run(self._token)

    async def on_read(self):
        self._logger.info(f"Logged in as {self.user.name}:{self.user.id}")
        self._logger.info("-------")

    def add_loop(self, loop):
        self._logger.info(f"Adding Loop {loop}")
        self.loop.create_task(loop)

    def wipeSplits(self):
        self.splits.clear()
        self.fireNums.clear()

    async def schedulePoll(self):
        await self.wait_until_ready()
        message_channel = self.get_channel(OFFICIAL_SCHEDULE_CHANNEL)
        while not self.is_closed():
            now = datetime.today().astimezone(pytz.timezone("US/Eastern")).strftime("%A %H")
            if now == 'Sunday 00':
                self._logger.info("It's time to post this week's poll!")
                time = 82800  # sleep 23 hours and then check every minute

                today = datetime.today().strftime("%B %d, %Y")
                msg = "@everyone\n__**Week of " + today + "**__\n\n"

                msg += "**Choose __Weekday__ Schedule**:\n"
                msg += "🇦  Monday\n"
                msg += "🇧  Tuesday\n"
                msg += "🇨  Wednesday\n"
                msg += "🇩  Thursday\n"

                reactions = ["🇦", "🇧", "🇨", "🇩"]

                weekday = await message_channel.send(msg)
                for choice in reactions:
                    await weekday.add_reaction(choice)

                msg = "`What Week Day Time? (P.M. EST)`"
                reactions = ["6⃣", "7⃣", "8⃣", "9⃣"]
                weekdayTime = await message_channel.send(msg)
                for choice in reactions:
                    await weekdayTime.add_reaction(choice)

                msg = "**Choose __Weekend__ Schedule**:\n"
                msg += "🇦  Friday\n"
                msg += "🇧  Saturday\n"

                reactions = ["🇦", "🇧"]

                weekend = await message_channel.send(msg)
                for choice in reactions:
                    await weekend.add_reaction(choice)

                msg = "`What Weekend Time? (P.M. EST)`"
                reactions = ["2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"]
                weekendTime = await message_channel.send(msg)
                for choice in reactions:
                    await weekendTime.add_reaction(choice)

            elif now == "Monday 00":  # Calculate results and post in #weekly-schedule
                # grab last 4 messages from #weekly-schedule and calculate results
                self._logger.info("It's time to post this week's schedule!")
                results = await message_channel.history(limit=4).flatten()
                announcement, raw = calculateWeeklySchedule(results)
                await message_channel.send(announcement)

                # Record this week's schedule in the database
                weekdayRun = {'_id': 'weekday', 'time': raw[0]}
                weekendRun = {'_id': 'weekend', 'time': raw[1]}
                schedule = [weekdayRun, weekendRun]

                # Store these bad boys in the database to check constantly and avoid Discord rate limiting
                logWeeklySchedule(self._db, schedule)

                time = 60  # check every minute

            else:
                self._logger.info("Not time for Poll or Results yet..")
                time = 60  # check every minute

            await asyncio.sleep(time)

    """
    Checks every hour to see if the next hour is a CEO run!
    If so, ping #announcements saying the run is in an hour.
    """
    async def pingServerForRun(self):
        await self.wait_until_ready()
        announcements_channel = self.get_channel(OFFICIAL_ANNOUNCEMENTS_CHANNEL)
        while not self.is_closed():
            time = 30 # Default to 30 second checks unless specified otherwise
            # If today is Sunday, no runs. Just voting on this week's schedule.
            if not datetime.today().astimezone(pytz.timezone("US/Eastern")).strftime("%A") == 'Sunday':
                runTimes = getRunTimes(self._db)

                est = pytz.timezone("US/Eastern") # Convert from UTC to EST
                now = datetime.today().astimezone(est).strftime("%A %H") # Format ex: Friday 21 (9PM)
                if now in runTimes:
                    msg = "CEO in one hour! @everyone"

                    """
                    Verify we haven't already pinged today (in case Heroku resets the bot during the hour
                    before the run)
                    """
                    lastAnnouncement = await announcements_channel.history(limit=1).flatten()
                    announcement = lastAnnouncement[0].content
                    # We only care if the last ping in announcements was actually today
                    lastPingDate = lastAnnouncement[0].created_at.astimezone(est).strftime("%B %d %Y")
                    today = datetime.today().astimezone(est).strftime("%B %d %Y")  # Format: May 23 2020
                    if announcement == msg and lastPingDate == today:
                        self._logger.error("ALREADY PINGED SERVER. YIKES")
                        time = 3600
                    else:
                        self._logger.info("IT'S CEO TIME. Pinging!")
                        # Alert announcements we have a CEO in one hour!
                        await announcements_channel.send(msg)
                        time = 3600 # Wait an hour so we don't ping every minute this hour
                        self._logger.info("Timer sleeping to 3600ms")
                else:
                    self._logger.info("It's currently " + str(now) + ". Gonna ping at " + str(runTimes[0]) + " and " + str(runTimes[1]) + ".")
                    time = 30 # Check every 30 seconds because yolo, rate limiting is not a concern at this point.
            else:
                self._logger.info("It's Sunday. No schedule for this week yet..")
                time = 3600 # Wait one hour at a time until Sunday is over

            await asyncio.sleep(time) # Sleep for a bit and then recheck everything.

    async def on_message(self, message):
        # await client.change_presence(game=discord.Game(name="I'm being updated!"))
        await self.change_presence(activity=discord.Game(name="5 Fire C.E.O."))
        # we do not want the bot to reply to itself
        if message.author == self.user or message.guild is None:
            return
        command = message.content.split(" ")[0]
        message_fn = self.function_map.get(command)
        if message_fn is not None:
            await message_fn(message)

    # iterate through JSON mongoDB data and ensure entry DNE
    # package entry into JSON and send to DB
    async def add_message(self, message):
        cmd = message.content.split()  # split by spaces
        msg = ""
        toonName = ' '.join(cmd[1:-1]).upper()

        if not cmd[len(cmd) - 1].isdigit() or len(cmd) < 3:
            msg = "**Failed**: Idk what you mean fam. Type `!add [Name] [Suit Level]`.\n__Example__:  `!add Static Void 50`"

        elif int(cmd[(len(cmd) - 1)]) < 8 or int(cmd[(len(cmd) - 1)]) > 50:
            msg = "**Failed**: Your suit level must be between 8 and 50. Get rekt."

        elif toonExistsInDB(self._db, toonName):
            msg = "**Failed**: This person already exists in the queue.\nIf you added them, you can update the entry by using !remove and re-adding them."

        else:  # we gucci fam
            entry = {}
            entry['_id'] = toonName
            entry['level'] = level = int(cmd[len(cmd) - 1])
            entry['sender'] = "{0.author.mention}".format(message)
            addToQueue(self._db, entry)

            msg += (
                "{0.author.mention}".format(message)
                + " added `"
                + str(toonName)
                + " [BC "
                + str(level)
                + "]` to the queue.\nTo edit the entry, type **!remove "
                + str(toonName)
                + "** and then re-add it.\n\n"
            )
            msg += "Current queue:\n```"
            queue = getQueueAsList(self._db)
            # Format list to msg string for printing in discord channel
            for entry in queue:
                level = str(entry[1]) if entry[1] >= 10 else ' ' + str(entry[1])
                msg += "[BC " + level + "]\t" + entry[0] + "\n"
            msg += "```"
        await message.channel.send(msg)

    async def queue_message(self, message):
        if isDatabaseEmpty(self._db):
            msg = "List is empty! use `!add [Name] [8-50]` to add someone!"
        else:
            queue = getQueueAsList(self._db)
            # Format list to msg string for printing in discord channel
            msg = "```"
            for entry in queue:
                level = str(entry[1]) if entry[1] >= 10 else ' ' + str(entry[1])
                msg += "[BC " + level + "]\t" + entry[0] + "\n"
            msg += "```"
        await message.channel.send(msg)

    async def split_message(self, message):
        if isDatabaseEmpty(self._db):
            msg = "**Failed**: There's nobody in the queue fam.\n```U cAnT dO tHaT```"
            await message.channel.send(msg)
            return

        queue = getQueueAsList(self._db)

        numGroups = howManyGroups(queue)
        self.wipeSplits()
        msg = balanceGroups(numGroups, queue, self.splits, self.fireNums)
        await message.channel.send(msg)

    async def wipe_message(self, message):
        msg = ""
        if verifyRole(message.author):  # User has permission to wipe queue
            wipeDB(self._db)
            msg = "Emptied queue!"
        else:
            msg = "**Failed**: You do not have permission to wipe the queue."

        await message.channel.send(msg)

    async def remove_message(self, message):
        msg = ""
        cmd = message.content.split()  # split by spaces

        name = ' '.join(cmd[1:]).upper()

        """ Code to only let the author remove their user """
        #requestor = "{0.author.mention}".format(message)
        # Verify the person removing the entry actually added it in the first place
        # elif queue[index][2] != requestor:
        #    msg = "**Failed**: You cannot remove someone that you didn't add to the queue.\n```Get rekt.```"

        # Check collection to verify the entry exists before trying to remove
        if not toonExistsInDB(self._db, name):
            msg = "This person does not exist.\nTry again or type **!queue** to view the queue."
        else:
            removeFromQueue(self._db, name)
            msg = "**Success**. `" + name + "` has been removed from the queue.\n\n"

            if isDatabaseEmpty(self._db):
                msg += "List is now empty! use `!add [Name] [8-50]` to add someone!"
            else:
                msg += "Current queue:\n```"
                queue = getQueueAsList(self._db)
                # Format list to msg string for printing in discord channel
                for entry in queue:
                    level = str(entry[1]) if entry[1] >= 10 else ' ' + str(entry[1])
                    msg += "[BC " + level + "]\t" + entry[0] + "\n"
                msg += "```"

        await message.channel.send(msg)

    async def swap_message(self, message):
        msg = ""
        toons = message.content[5:].split('-')
        if len(toons) < 2:
            msg = "**Failed**: Must give 2 arg separated by a hyphen. Example: `!swap [Runnable] [-] [Static Void]`"
        elif not self.splits:
            msg = "**Failed**: The queue hasn't been split yet fam."
        else:
            toon1 = toons[0].strip().upper()
            toon2 = toons[1].strip().upper()
            msg = swapGroups(toon1, toon2, self.splits, self.fireNums)

        await message.channel.send(msg)

    async def help_message(self, message):
        msg = "**Welcome to RunBot by  <@!285861225491857408>**\n\n"

        msg += "𝟏)\tUse `!add` in #run-queue to register for the CEO each run.\n"
        msg += "𝟐)\tIf more than 8 people sign up, `!split` will auto organize groups so everyone gets the highest possible amount of fires.\n"
        msg += "\n__**COMMANDS**__\n\n"

        # !add
        msg += "`!add`\n"
        msg += "Use this to add yourself or anyone else to the CEO queue!\n"
        msg += "```Usage:\t  !add [Name] [Suit Level]\n"
        msg += "Example:\t!add Runnable 50```\n"
        msg += "__NOTE__: Your name can be multiple words, and Suit level must be >= 8 and <= 50.\n\n\n"

        # !remove
        msg += "`!remove`\n"
        msg += "Use this to remove someone you added to the queue.\n"
        msg += "```Usage:\t  !remove [Name in queue]\n"
        msg += "Example:\t!remove Static Void```\n"
        # msg += "__NOTE__: To prevent trolling, you can only remove people you personally added to the queue.\n"
        msg += "__NOTE__: If you made a mistake or want to update your entry, use this to remove the old one, and then re-add it.\n\n\n"

        # !queue
        msg += "`!queue`\n"
        msg += "Use this to view everyone currently signed up for the CEO run.\n"
        msg += "```Usage:\t  !queue```\n"
        msg += "__NOTE__: This command takes no arguments.\n\n\n"

        # !split
        msg += "`!split`\n"
        msg += "Use this to evenly split the queue into teams for the highest fires possible.\n"
        msg += "```Usage:\t  !split\n```"
        msg += "__NOTE__: This command takes no arguments.\n"
        msg += "__NOTE__: This bot is capable of evenly splitting an unlimited amount of groups evenly.\n"
        msg += "__NOTE__: Calling !split after groups are already split will reset any swaps done.\n\n\n"

        # !swap
        msg += "`!swap`\n"
        msg += "Use this to swap two people between two groups.\n"
        msg += "```Usage:\t  !swap [Name1] [-] [Name2]\n"
        msg += "Example:\t!swap Runnable - Static Void```\n"
        msg += "__NOTE__: It works with or without spaces around the hyphen!\n\n\n"
        #msg += "__NOTE__: To prevent unbalancing groups, for now, you can only swap people around who are the same level.\n\n\n"

        # !wipe
        msg += "`!wipe`\n"
        msg += "Use this to wipe the current queue and start from scratch.\n"
        msg += "```Usage:\t  !wipe```\n"
        msg += "__NOTE__: This command takes no arguments.\n"
        msg += "__NOTE__: To prevent trolling, **only** these roles can wipe the queue: "
        msg += "**The Chief Cheese, Cheese Executive Officer, Aged Gouda**"

        await message.channel.send(msg)
