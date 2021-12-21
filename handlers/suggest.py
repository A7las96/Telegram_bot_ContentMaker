from aiogram import types, Dispatcher

import PIL
import imagehash
from aiogram.types import MediaGroup, PollAnswer
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from data_base import sqlite_db
from PIL import Image
import os

file_to_send_id = ""
vote_result: types.Message
channel_id = -1001739507227
group_id = -703074017


class FSMSuggest(StatesGroup):
    photo = State()


group_members = 0
numbers_yes = 0
numbers_no = 0


# начало диалога о публикации записи
@dp.message_handler(commands='suggest', state=None)
async def photo_suggest(message: types.Message):
    await FSMSuggest.photo.set()
    await message.reply('Пришлите фото')


# ловим фото от пользователя
@dp.message_handler(content_types=['photo', 'document'], state=FSMSuggest.photo)
async def load_pic(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        error = False
        file_name = 'user_photo.jpg'
        file_path = file_name
        try:
            await message.photo[-1].download(destination_file=file_path)
            image = Image.open(file_path)
            global file_to_send_id
            data['photo'] = message.photo[-1].file_id
            file_to_send_id = data['photo']
            data['d_hash'] = str(imagehash.dhash(image, hash_size=11))
            data['p_hash'] = str(imagehash.phash(image, hash_size=11))
        except IndexError:
            await message.document.download(destination_file=file_path)
            try:
                image = Image.open(file_path)
                data['photo'] = message.document.file_id
                data['d_hash'] = str(imagehash.dhash(image, hash_size=11))
                data['p_hash'] = str(imagehash.phash(image, hash_size=11))
            except PIL.UnidentifiedImageError:
                error = True
                await message.reply('Данный тип файла не может быть обработан, пришлите фото формата JPEG или PNG')
                await state.finish()
    os.remove(file_path)
    if not error:
        res_dubl, res_sim_photo_list = await sqlite_db.duplicate_check(state)
        if not res_dubl:
            await message.answer('Фото было проверено и уже направилось на одобрение к модераторам!')
            if len(res_sim_photo_list) == 0:
                await bot.send_photo(group_id, data['photo'], "На проверку пришло новое фото!")
            elif len(res_sim_photo_list) == 1:
                await bot.send_photo(group_id, data['photo'], "На проверку пришло новое фото!")
                await bot.send_photo(group_id, res_sim_photo_list[0], "Похожая фотография")
            elif len(res_sim_photo_list) > 1:
                await bot.send_photo(group_id, data['photo'], "На проверку пришло новое фото!")
                media_group = MediaGroup()
                for i in range(len(res_sim_photo_list)):
                    if i == 0:
                        media_group.attach_photo(res_sim_photo_list[i], "Похожие фотографии")
                    else:
                        media_group.attach_photo(res_sim_photo_list[i])
                await bot.send_media_group(group_id, media_group)
            global vote_result
            global numbers_yes
            global numbers_no
            numbers_no = 0
            numbers_yes = 0
            vote_result = await bot.send_poll(chat_id=group_id, question='Публиковать в основной канал?',
                                              options=['Да ✅️', 'Нет ❌'], is_anonymous=False)
            await sqlite_db.poll_id_save(state, id_poll=vote_result.message_id)
        else:
            await message.answer('Данное фото уже было отправлено данному боту!')
        await state.finish()


@dp.poll_answer_handler()
async def handle_poll_answer(poll_answer: PollAnswer):
    # проверяем ответ
    global numbers_yes
    global numbers_no
    global vote_result
    global group_members
    group_members = await bot.get_chat_members_count(group_id)
    if poll_answer.option_ids[0] == 0:
        numbers_yes += 1
    elif poll_answer.option_ids[0] == 1:
        numbers_no += 1

    if int(numbers_yes/group_members) * 100 > 70:
        await bot.send_photo(channel_id, file_to_send_id)
        await bot.stop_poll(group_id, vote_result.message_id)
        await bot.send_message(text='Фото было опубликовано!', chat_id=group_id)


# выход из машины состяний
@dp.message_handler(commands='stop', state='*')
@dp.message_handler(Text(equals='stop', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Процесс публикации отменен')


# регистрируем хэндлеры
def register_handlers_suggest(dp: Dispatcher):
    dp.register_message_handler(photo_suggest, commands='suggest', state=None)
    dp.register_message_handler(load_pic, content_types='photo', state=FSMSuggest.photo)
    dp.register_message_handler(cancel_handler, commands='stop', state='*')
    dp.register_message_handler(cancel_handler, Text(equals='stop', ignore_case=True), state='*')
