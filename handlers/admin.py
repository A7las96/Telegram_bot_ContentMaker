from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import BoundFilter, IsReplyFilter
from aiogram.utils.markdown import text, bold
from aiogram.types import ParseMode

from create_bot import dp, bot

import sqlite3 as sq

from handlers import suggest


class MyFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def check(self, message: types.Message):
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.is_chat_admin()


dp.filters_factory.bind(MyFilter)
dp.filters_factory.bind(IsReplyFilter)


@dp.message_handler(is_admin=True, is_reply=True, commands=['accept'])
async def publication_success(message: types.Message):
    conn = sq.connect('photo.db')
    cur = conn.cursor()
    file_to_send_id = cur.execute('SELECT file_id FROM photo WHERE poll_id = ?',
                                  (str(message.reply_to_message.message_id),)).fetchone()
    await bot.send_photo(suggest.channel_id, file_to_send_id[0])
    await bot.stop_poll(suggest.group_id, message.reply_to_message.message_id)
    await message.answer('Фото было опубликовано!')
    await bot.delete_message(chat_id=suggest.group_id, message_id=message.message_id)


@dp.message_handler(is_admin=True, is_reply=True, commands=['cancel'])
async def publication_failed(message: types.Message):
    await bot.stop_poll(suggest.group_id, message.reply_to_message.message_id)
    await message.answer('Публикация была отменена!')
    await bot.delete_message(chat_id=suggest.group_id, message_id=message.message_id)


@dp.message_handler(is_admin=True, commands=['drop_db'])
async def db_drop(message: types.Message):
    conn = sq.connect('photo.db')
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS photo')

    cur.execute('''
         CREATE TABLE IF NOT EXISTS photo(
             file_id TEXT ,
             dHash TEXT PRIMARY KEY,
             pHash TEXT,
             poll_id TEXT)
            '''
                )
    # сохраннение изменений
    conn.commit()
    await message.answer('База данных была успешно очищена!')
    await bot.delete_message(chat_id=suggest.group_id, message_id=message.message_id)


@dp.message_handler(is_admin=True, commands=['help'])
async def process_help_admin(message: types.Message):
    msg = text(bold('В качестве модератора, у вас есть возможность досрочно исполнять процесс публикации или '
                    'наоборот останавливать его' + '\n\nДля этого пропишите соответствующие команды ответным сообщением '
                    'на сообщение с опросом' + '\n\nТакже вы можете очистить базу данных с информацией о фото'))
    await bot.send_message(message.from_user.id, text=msg, parse_mode=ParseMode.MARKDOWN)
    await bot.delete_message(chat_id=suggest.group_id, message_id=message.message_id)


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(publication_success, commands='accept')
    dp.register_message_handler(publication_failed, commands='cancel')
    dp.register_message_handler(db_drop, commands='bd_drop')
    dp.register_message_handler(process_help_admin, commands='help')
