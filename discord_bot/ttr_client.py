import discord  # 0.16.12
import asyncio
import logging

from datetime import datetime
import pytz # Force datetime into EST since my server is UTC

from group_helpers import (
    balanceGroups,
    howManyGroups,
    calculateWeeklySchedule,
    getRunAlertTimes,
    checkList,
    swapGroups,
)
from ttr_helpers import verifyRole

from mongo_helpers import (
    printQueue,
    addToQueue,
    toonExistsInDB,
    wipeDB
)

OFFICIAL_SCHEDULE_CHANNEL = '553493689880543242' # Cheese server's #weekly-schedule
OFFICIAL_ANNOUNCEMENTS_CHANNEL = '481295173113085973' # Cheese server's #announcements
TEST_CHANNEL = '553420403033505792' # Local test server's #run-queue

# TTRClient eats the arg it requires (token), then passes the rest
# onto discord.Client's __init__ (*args, **kwargs). in my case nothing
class TTRClient(discord.Client):
    def __init__(self, token, db, *args, **kwargs):
        self._token = token
        self._db = db
        self._logger = logging.getLogger(__name__)
        self.queue = []
        self.splits = []
        self.fireNums = []
        super(TTRClient, self).__init__(*args, **kwargs)
        self.loop.create_task(self.schedulePoll())
        self.loop.create_task(self.pingServerForRun())
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

    def wipeQueue(self):
        self.queue.clear()

    async def get_logs_from(self, channel, numMsgs=4):
        poll = []
        async for msg in self.logs_from(channel, limit=numMsgs):
            poll.append(msg)
        return poll

    async def schedulePoll(self):
        await self.wait_until_ready()
        message_channel = self.get_channel(OFFICIAL_SCHEDULE_CHANNEL)
        while not self.is_closed:
            now = datetime.today().strftime("%a %H:%M")
            if now == "Sun 02:00":
                print("It's time to post this week's poll!")
                time = 82800  # sleep 23 hours and then check every minute

                today = datetime.today().strftime("%B %d, %Y")
                msg = "__**Week of " + today + "**__\n\n"

                msg += "**Choose __Weekday__ Schedule**:\n"
                msg += "🇦  Monday\n"
                msg += "🇧  Tuesday\n"
                msg += "🇨  Wednesday\n"
                msg += "🇩  Thursday\n"

                reactions = ["🇦", "🇧", "🇨", "🇩"]

                weekday = await self.send_message(
                    message_channel, msg
                )
                for choice in reactions:
                    await self.add_reaction(weekday, choice)

                msg = "`What Week Day Time? (P.M. EST)`"
                reactions = ["6⃣", "7⃣", "8⃣", "9⃣"]
                weekdayTime = await self.send_message(
                    message_channel, msg
                )
                for choice in reactions:
                    await self.add_reaction(weekdayTime, choice)

                msg = "**Choose __Weekend__ Schedule**:\n"
                msg += "🇦  Friday\n"
                msg += "🇧  Saturday\n"

                reactions = ["🇦", "🇧"]

                weekend = await self.send_message(
                    message_channel, msg
                )
                for choice in reactions:
                    await self.add_reaction(weekend, choice)

                msg = "`What Weekend Time? (P.M. EST)`"
                reactions = ["2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"]
                weekendTime = await self.send_message(
                    message_channel, msg
                )
                for choice in reactions:
                    await self.add_reaction(weekendTime, choice)

            elif now == "Mon 02:00":  # Calculate results and post in #weekly-schedule
                # grab last 4 essages from #weekly-schedule and calculate results
                print("It's time to post this week's schedule!")
                results = await self.get_logs_from(
                    message_channel
                )
                announcement = calculateWeeklySchedule(results)
                await self.send_message(
                    message_channel, announcement
                )
                time = 60  # check every minute

            else:
                print("Not time for Poll or Results yet..")
                time = 60  # check every minute

            await asyncio.sleep(time)

    """
    Checks every hour to see if the next hour is a CEO run!
    If so, ping #announcements saying the  run is in an hour.
    """
    async def pingServerForRun(self):
        await self.wait_until_ready()
        schedule_channel = self.get_channel(OFFICIAL_SCHEDULE_CHANNEL)
        announcements_channel = self.get_channel(OFFICIAL_ANNOUNCEMENTS_CHANNEL)
        while not self.is_closed:
            runTimes = await self.get_logs_from(
                schedule_channel,1
            )

            lastMessage = runTimes[0].content
            # Don't do anything if we're still voting on the upcoming week's schedule
            if lastMessage.find("This week's CEO Schedule:") != -1:
                print("Schedule is posted! Now checking time..")

                times = getRunAlertTimes(lastMessage) # Gets 24hr format
                est = pytz.timezone("US/Eastern") # Convert from UTC to EST
                now = datetime.today().astimezone(est).strftime("%A %H") # Format ex: Friday 21 (9PM)
                if now in times:
                    print("IT'S CEO TIME. Pinging!")
                    msg = "CEO in one hour! @here"
                    # Alert announcements we have a CEO in one hour!
                    runPing = await self.send_message(
                        announcements_channel, msg
                    )
                    time = 3600 # Wait an hour so we don't ping every minute this hour
                else:
                    print("It's currently " + str(now) + ". Gonna ping at " + str(times[0]) + " and " + str(times[1]) + ".")
                    time = 300 # Wait 5 minutes to prevent rate limit exception
            else:
                print("No schedule for this week yet..")
                time = 300 # Wait 5 minutes to prevent rate limit exception.

            await asyncio.sleep(time) # Check every minute

    async def on_message(self, message):
        # await client.change_presence(game=discord.Game(name="I'm being updated!"))
        await self.change_presence(game=discord.Game(name="5 Fire C.E.O."))
        # we do not want the bot to reply to itself
        if message.author == self.user or message.server is None:
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
        toonName = ' '.join(cmd[1:-1])

        if not cmd[len(cmd) - 1].isdigit() or len(cmd) < 3:
            msg = "**Failed**: Idk what you mean fam. Type `!add [Name] [Suit Level]`.\n__Example__:  `!add Static Void 50`"

        elif int(cmd[(len(cmd) - 1)]) < 8 or int(cmd[(len(cmd) - 1)]) > 50:
            msg = "**Failed**: Your suit level must be between 8 and 50. Get rekt."

        elif toonExistsInDB(self._db, toonName):
            msg = "**Failed**: This person already exists in the queue.\nIf you added them, you can update the entry by using !remove and re-adding them."

        else:  # we gucci fam
            self.queue.append(
                (str(toonName), int(cmd[len(cmd) - 1]), "{0.author.mention}".format(message))
            )
            entry = {}
            entry['_id'] = toonName
            entry['level'] = int(cmd[len(cmd) - 1])
            addToQueue(self._db, entry)
            msg = (
                "{0.author.mention}".format(message)
                + " added `"
                + str(toonName)
                + " [BC "
                + str(cmd[2])
                + "]` to the queue.\nTo edit the entry, type **!remove "
                + str(cmd[1])
                + "** and then re-add it.\n\n"
            )
            msg += "Current queue:\n```"
            for i in self.queue:
                msg += "[BC " + str(i[1]) + "]\t" + i[0] + "\n"
            msg += "```"
        await self.send_message(message.channel, msg)

    async def queue_message(self, message):
        if not self.queue:
            msg = "List is empty! use `!add [Name] [8-50]` to add someone!"
        else:
            msg = "```"
            for i in self.queue:
                msg += "[BC " + str(i[1]) + "]\t" + i[0] + "\n"
            msg += "```"
        await self.send_message(message.channel, msg)

    async def split_message(self, message):
        if len(self.queue) is 0:
            msg = "**Failed**: There's nobody in the queue fam.\n```U cAnT dO tHaT```"
            await self.send_message(message.channel, msg)
            return
        numGroups = howManyGroups(self.queue)
        self.wipeSplits()
        msg = balanceGroups(numGroups, self.queue, self.splits, self.fireNums)
        await self.send_message(message.channel, msg)

    async def wipe_message(self, message):
        msg = ""
        if verifyRole(
            "{0.author.top_role}".format(message)
        ):  # User has permission to wipe queue
            self.wipeQueue() # TODO: Phase out local copy of queue, splits
            wipeDB(self._db)
            msg = "Emptied queue!"
        else:
            msg = "**Failed**: You do not have permission to wipe the queue."

        await self.send_message(message.channel, msg)

    async def remove_message(self, message):
        msg = ""
        cmd = message.content.split()  # split by spaces

        name = ' '.join(cmd[1:])

        # Check queue for this person
        index = checkList(self.queue, name)
        requestor = "{0.author.mention}".format(message)
        if index is -1:  # returns False if DNE
            msg = "This person does not exist fam.\nTry again or type **!queue** to view the queue."
        # Verify the person removing the entry actually added it in the first place
        # elif queue[index][2] != requestor:
        #    msg = "**Failed**: You cannot remove someone that you didn't add to the queue.\n```Get rekt.```"
        else:
            del self.queue[index]
            msg = "**Success**. `" + name + "` has been removed from the queue."

        await self.send_message(message.channel, msg)

    async def swap_message(self, message):
        msg = ""
        toons = message.content[5:].split('-')
        if len(toons) < 2:
            msg = "**Failed**: Must give 2 arg separated by a hyphen. Example: `!swap [Runnable] [-] [Static Void]`"
        elif not self.splits:
            msg = "**Failed**: The queue hasn't been split yet fam."
        else:
            toon1 = toons[0].strip()
            toon2 = toons[1].strip()
            msg = swapGroups(toon1, toon2, self.splits, self.fireNums)

        await self.send_message(message.channel, msg)

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

        await self.send_message(message.channel, msg)
