from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from os import getenv
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()

bot_token = getenv("BOT_TOKEN")
if not bot_token:
    exit("Error: no token provided")

bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=storage)
