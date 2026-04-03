from email.mime import message

from aiogram import types, F
from aiogram.filters import StateFilter
from aiogram.filters.command import Command, CommandObject
from aiogram.types import FSInputFile
from manager.m import dp, db, UserState, check_subscription, bot, THUMB, subcription
from data.settings import DATA_CHANNEL
from asyncio import Semaphore
from aiogram.fsm.context import FSMContext

semaphore = Semaphore()


async def yopiq_kanal(user_id: int, name: str):
    settings = db.get_settings()
    replay_markup =  types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="↪️ Kanalga o'tish", url=settings.main_chat_url)
            ]
        ],
    )

    await bot.copy_message(chat_id=user_id,
                           from_chat_id=DATA_CHANNEL,
                           message_id=settings.photo_message_id,
                           caption=settings.msg2.replace('{name}', name),
                           reply_markup=replay_markup)

    

@dp.message(Command('start'))
async def startt(message: types.Message, command: CommandObject, state: FSMContext):
    db.add_user(message.from_user.id)
    settings = db.get_settings()

    if settings.main_chat:
        try:
            member = await bot.get_chat_member(settings.main_chat, message.from_user.id)
            if member.status not in ("left", "kicked", "banned"):
                await yopiq_kanal( message.from_user.id, message.from_user.first_name)
                return
        except Exception:
            pass

    await state.set_state(UserState.waiting_channel_join)
    await message.answer(text=settings.msg1, reply_markup=subcription())


@dp.message(StateFilter(UserState.waiting_channel_join))
async def handle_waiting_channel_join(message: types.Message, state: FSMContext):
    db.add_user(message.from_user.id)
    settings = db.get_settings()

    if settings.main_chat:
        try:
            member = await bot.get_chat_member(settings.main_chat, message.from_user.id)
            if member.status not in ("left", "kicked", "banned"):
                await yopiq_kanal(message.from_user.id, message.from_user.first_name)
                return
        except Exception:
            pass

    await state.set_state(UserState.waiting_channel_join)
    await message.answer(text=settings.msg1, reply_markup=subcription())
    


@dp.callback_query(StateFilter(UserState.waiting_channel_join), F.data == "check_joins")
async def check_joins_channel_state(call: types.CallbackQuery, state: FSMContext):
    chats = db.get_required_joins()
    statuses = []
    for chat in chats:
        try:
            res = await call.bot.get_chat_member(chat.chat_id, call.from_user.id)
            statuses.append(res.status)
        except Exception:
            pass

    if "left" in statuses or "kicked" in statuses:
        await call.answer("Barcha kanallarga a'zo bo'lishingiz kerak !", show_alert=True)
        return

    await state.clear()
    await yopiq_kanal(call.message.chat.id, call.from_user.first_name)



@dp.chat_join_request()
async def handle_chat_join_request(update: types.ChatJoinRequest):
    user_id = update.from_user.id
    chat_id = update.chat.id
    chats = db.get_required_joins()

    statuses = []
    for chat in chats:
        try:
            res = await bot.get_chat_member(chat.chat_id, update.from_user.id)
            statuses.append(res.status)
        except Exception:
            pass

    if "left" in statuses or "kicked" in statuses:
        return

    try:
        await bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
        setting = db.get_settings()
        
        await bot.send_message(chat_id = user_id, text = "✅ Kanalga qo'shilish so'rovingiz qabul qilindi!", 
                                   reply_markup = types.InlineKeyboardMarkup(inline_keyboard=[
                                    [types.InlineKeyboardButton(text="↪️ Kanalga o'tish", url=setting.main_chat_url)]   
                                   ]))
    except Exception as e:
        print(f"Error approving join request: {e}")


@dp.message()
async def main_text_handler(message: types.Message, state: FSMContext):
    db.add_user(message.from_user.id)
    settings = db.get_settings()

    if settings.main_chat:
        try:
            member = await bot.get_chat_member(settings.main_chat, message.from_user.id)
            if member.status not in ("left", "kicked", "banned"):
                await yopiq_kanal(message.from_user.id, message.from_user.first_name)
                return
        except Exception:
            pass

    await state.set_state(UserState.waiting_channel_join)
    await message.answer(text=settings.msg1, reply_markup=subcription())