from aiogram import types, Dispatcher
from aiogram.utils.markdown import text, bold
from aiogram.types import ParseMode
from create_bot import dp, bot
from handlers.suggest import group_id


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Привет!\nЭто бот-предложка, пропиши команду /help, чтобы узнать, что я могу")


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    msg = text(bold('Я могу передать твое фото на рассмотрение в чат модераторов, чтобы сделать это, пропиши команду '
                    '/suggest' + '\n\nТакже ты можешь отменить процесс отправления картинки, '
                                 'прописав слово stop'))
    await bot.send_message(message.from_user.id, text=msg, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=['dice'])
async def cmd_dice(message: types.Message):
    await message.answer_dice(emoji="🎲")


@dp.message_handler(content_types=['photo', 'document'])
async def ph_without_cmd(message: types.message):
    await bot.send_message(message.from_user.id, text='Чтобы отправить фото на рссмотрение, нужно прописать команду ''/suggest')
    await message.delete()


@dp.message_handler()
async def common(message: types.Message):
    if message.text.lower() == 'перерыв':
        await bot.send_message(message.from_user.id,text='Внимание, объявляется перекур 🚬')
    if message.chat.id != group_id:
        await bot.send_message(message.from_user.id,text='Такой команды не существует')
        await message.delete()


def register_handlers_user(dp: Dispatcher):
    dp.register_message_handler(process_start_command, commands='start')
    dp.register_message_handler(process_help_command, commands='help')
    dp.register_message_handler(cmd_dice, commands='dice')
    dp.register_message_handler(common)
