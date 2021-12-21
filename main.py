from create_bot import dp
from aiogram import types
from data_base import sqlite_db
from aiogram.utils import executor

from handlers.suggest import register_handlers_suggest
from handlers.admin import register_handlers_admin
from handlers.user import register_handlers_user

from handlers.suggest import group_id


async def set_default_commands(dp):
    await dp.bot.set_my_commands([], types.bot_command_scope.BotCommandScopeChat(group_id))

    await dp.bot.set_my_commands([
        types.BotCommand('accept', "Опубликовать досрочно ✅"),
        types.BotCommand('cancel', "Отклонить досрочно ❌"),
        types.BotCommand('drop_database', "Очистить базу данных ♻"),
        types.BotCommand('help', "Справка по командам 📒")
    ], types.bot_command_scope.BotCommandScopeChatAdministrators(group_id))

    await dp.bot.set_my_commands([
        types.BotCommand('help', "Справка по командам 📒"),
        types.BotCommand('dice', "Бросить кубики? 🎲"),
        types.BotCommand('suggest', "Предложить фото 🌠")
    ], types.bot_command_scope.BotCommandScopeAllPrivateChats())


async def on_startup(_):
    print('Бот вышел в онлайн')
    sqlite_db.init_db(force=True)

    await set_default_commands(dp)


register_handlers_admin(dp)
register_handlers_suggest(dp)
register_handlers_user(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates= True, on_startup=on_startup)
