"""
Telegram Bot for Team Time Zone Management
------------------------------------------
This Telegram bot helps distributed teams work together more effectively by providing
instant access to the current local time of each team member.
Purpose:
- Simplifies collaboration across different time zones
- Helps team members schedule meetings at convenient times for everyone
- Reduces confusion about availability and working hours
- Makes it easier to respect work-life balance across global teams
Features:
- Responds to the /localTime command with current times for all team members
- Displays time with date in a clear, formatted list
- Includes location information for context
- Easy to configure with new team members
Usage:
1. Set up a BOT_TOKEN in your .env file (obtained from BotFather on Telegram)
2. Configure your team members with their names, locations and time zones
3. Run the bot and use the /localTime command in your Telegram chat
The bot uses the aiogram framework for Telegram integration and pytz for accurate
timezone calculations.
"""
import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List

import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv


class BotConfig:
    """Configuration settings for the Telegram bot."""
    # Environment variables
    ENV_BOT_TOKEN = "BOT_TOKEN"

    # Command names
    CMD_LOCAL_TIME = "localtime"
    CMD_HELP = "help"
    CMD_START = "start"

    # Formatting settings
    MARKDOWN_MODE = "HTML"
    TIME_FORMAT = "%H:%M"
    TEAM_CONFIG_FILE = "team_members.json"

    # Message templates
    MESSAGE_HEADER = ""
    MESSAGE_FORMAT = "{name}: {local_time}\n"
    HELP_MESSAGE = """
<b>Time Zone Bot Help</b>
Available commands:
• /localTime - Shows the current local time for all team members
• /help - Shows this help message
This bot helps you coordinate with team members across different time zones.
"""
    WELCOME_MESSAGE = """
<b>Welcome to the Time Zone Bot!</b>
This bot helps you coordinate with team members across different time zones.
Use /localTime to see the current time for all team members.
Use /help for more information.
"""
    ERROR_MESSAGE = "Sorry, an error occurred while processing your request."

    # Logging
    DEFAULT_LOG_LEVEL = logging.INFO


# Configure logging
logging.basicConfig(level=BotConfig.DEFAULT_LOG_LEVEL)
logger = logging.getLogger(__name__)


@dataclass
class TeamMember:
    """Class to represent a team member with location and timezone information."""
    name: str
    city: str
    timezone: str

    def get_local_time(self) -> str:
        """Return the current local time for this team member."""
        try:
            tz = pytz.timezone(self.timezone)
            return datetime.now(tz).strftime(BotConfig.TIME_FORMAT)
        except pytz.exceptions.UnknownTimeZoneError:
            logger.error(f"Unknown timezone: {self.timezone}")
            return "Unknown timezone"


class LocalTimeBot:
    """Telegram bot that shows local time for team members."""

    def __init__(self, token: str, team_members: List[TeamMember]):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.team_members = team_members
        self._register_handlers()

    def _register_handlers(self):
        """Register message handlers."""
        self.dp.message.register(self.cmd_local_time, Command(BotConfig.CMD_LOCAL_TIME))
        self.dp.message.register(self.cmd_help, Command(BotConfig.CMD_HELP))
        self.dp.message.register(self.cmd_start, Command(BotConfig.CMD_START))

    def format_local_time_message(self) -> str:
        """Format the message showing local time for each team member."""
        response_text = BotConfig.MESSAGE_HEADER
        for member in self.team_members:
            local_time = member.get_local_time()
            response_text += BotConfig.MESSAGE_FORMAT.format(
                name=member.name,
                city=member.city,
                local_time=local_time
            )
        return response_text

    async def _send_reply(self, message: types.Message, content: str) -> None:
        """Send a reply with error handling."""
        try:
            await message.reply(content, parse_mode=BotConfig.MARKDOWN_MODE)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await message.reply(BotConfig.ERROR_MESSAGE)

    # Command handlers
    async def cmd_local_time(self, message: types.Message) -> None:
        """Handler for the /localTime command."""
        response_text = self.format_local_time_message()
        await self._send_reply(message, response_text)

    async def cmd_help(self, message: types.Message) -> None:
        """Handler for the /help command."""
        await self._send_reply(message, BotConfig.HELP_MESSAGE)

    async def cmd_start(self, message: types.Message) -> None:
        """Handler for the /start command."""
        await self._send_reply(message, BotConfig.WELCOME_MESSAGE)

    # Bot lifecycle methods
    async def start(self) -> None:
        """Start the bot and handle polling."""
        logger.info("Starting bot...")
        await self.dp.start_polling(self.bot, skip_updates=True)

    async def stop(self) -> None:
        """Stop the bot gracefully."""
        logger.info("Stopping bot...")
        if self.bot.session:
            await self.bot.session.close()


def load_team_members() -> List[TeamMember]:
    """Load team members configuration from file if available, otherwise use defaults."""
    # If configuration file exists, load team members from it
    if os.path.exists(BotConfig.TEAM_CONFIG_FILE):
        try:
            with open(BotConfig.TEAM_CONFIG_FILE, 'r', encoding='utf-8') as f:
                members_data = json.load(f)
                return [
                    TeamMember(m["name"], m["city"], m["timezone"])
                    for m in members_data
                ]
        except Exception as e:
            logger.error(f"Error loading team members from file: {e}")

    # Default team members if no config file or loading fails
    logger.info("Using default team members configuration")
    return [
        TeamMember("mayer", "Иркутск", "Asia/Irkutsk"),
        TeamMember("Antonio_Margaretti", "Златоуст", "Asia/Yekaterinburg"),
        TeamMember("Deadhoko", "Волгоград", "Europe/Volgograd"),
        TeamMember("Чайковский", "Москва", "Europe/Moscow"),
        TeamMember("seregatipich", "Испания", "Europe/Madrid")
    ]


async def main() -> None:
    """Initialize and start the bot."""
    # Ensure environment variables are loaded
    load_dotenv()

    # Get bot token from environment
    bot_token = os.getenv(BotConfig.ENV_BOT_TOKEN)
    if not bot_token:
        logger.error(f"{BotConfig.ENV_BOT_TOKEN} is missing! Please add it to your .env file")
        exit(1)

    # Initialize bot
    team_members = load_team_members()
    bot = LocalTimeBot(bot_token, team_members)

    try:
        # Start the bot
        await bot.start()
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        await bot.stop()
        exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        exit(1)
