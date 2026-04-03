from aiogram import types, F
from aiogram.filters import StateFilter
from aiogram.filters.command import Command, CommandObject
from aiogram.types import FSInputFile
from manager.m import dp, db, UserState, check_subscription, bot, THUMB, subcription
from asyncio import Semaphore


semaphore = Semaphore()

def ball():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="👥 Taklif qilinganlar"),
            ]
        ],
        resize_keyboard=True
    )


def taklif_post():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🔗 Taklif posti", callback_data="get_post")
            ]
        ],
    )


def post_end(user_id):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🔥 Ishtrok etish 🔥", url=f"t.me/{db.bot.username}?start={user_id}")
            ]
        ],
    )

from aiogram.fsm.context import FSMContext

@dp.message(Command('start'))
async def startt(message: types.Message, command: CommandObject, state: FSMContext):
    db.add_user(message.from_user.id)
    settings = db.get_settings()

    if settings.main_chat:
        try:
            member = await bot.get_chat_member(settings.main_chat, message.from_user.id)
            if member.status not in ("left", "kicked", "banned"):
                await message.answer(
                    "✅ Siz allaqachon yopiq kanalga qo'shilgansiz!",
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                        types.InlineKeyboardButton(text="↪️ Kanalga o'tish", url=settings.main_chat_url)
                    ]])
                )
                return
        except Exception:
            pass

    await state.set_state(UserState.waiting_channel_join)
    await message.answer_photo(photo=FSInputFile('thumb.jpg'), caption=settings.msg1, reply_markup=subcription())


@dp.message(StateFilter(UserState.waiting_channel_join))
async def handle_waiting_channel_join(message: types.Message, state: FSMContext):
    settings = db.get_settings()
    await message.answer_photo(photo=FSInputFile('thumb.jpg'), caption=settings.msg1, reply_markup=subcription())


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
    settings = db.get_settings()

    try:
        await bot.approve_chat_join_request(settings.main_chat, call.from_user.id)
    except Exception:
        pass

    await call.message.delete()
    await call.message.answer(
        "✅ Kanalga qo'shilish so'rovingiz qabul qilindi!",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="↪️ Kanalga o'tish", url=settings.main_chat_url)
        ]])
    )
    await call.answer()


@dp.message(UserState.waiting_new_user)
async def handle_waiting_new_user(message: types.Message, state: FSMContext):
    refer = await state.get_value('refer')
    if refer:
        await update_user_ball(refer)
    await state.clear()

    settings = db.get_settings()

    await message.answer("Ballaringizni ko`rish uchun 👥 Taklif qilinganlar tugmasini bosing", reply_markup=ball())
    await bot.copy_message(chat_id=message.from_user.id,
                               from_chat_id='@audiotd',
                               caption=settings.msg1.replace('{ref}', f"https://t.me/{db.bot.username}?start={message.from_user.id}"),
                               reply_markup=taklif_post(),
                               message_id = THUMB)



@dp.callback_query(UserState.waiting_new_user, F.data == "check_joins")
async def check_joins_in_state(call: types.CallbackQuery, state: FSMContext):
    chats = db.get_required_joins()
    status = []
    for chat in chats:
        try:
            res = await call.bot.get_chat_member(chat.chat_id, call.from_user.id)
            status.append(res.status)
        except Exception as e:
            pass

    if "left" in status:
        await call.answer("Barcha kanallarga a'zo bo'lishingiz kerak !", show_alert=True)

    else:
        refer = await state.get_value('refer')
        if refer:
            await update_user_ball(refer)    
        await state.clear()

        await call.answer("Barchasi tayyor ✅", show_alert=True)
        await call.message.delete()

        settings = db.get_settings()

        await call.message.answer("Ballaringizni ko`rish uchun 👥 Taklif qilinganlar tugmasini bosing", reply_markup=ball())
        await bot.copy_message(chat_id=call.from_user.id,
                               from_chat_id='@audiotd',
                               caption=settings.msg1.replace('{ref}', f"https://t.me/{db.bot.username}?start={call.message.from_user.id}"),
                               reply_markup=taklif_post(),
                               message_id = THUMB)





@dp.callback_query(UserState.waiting_new_user)
async def waiting_user_callback(call: types.CallbackQuery, state: FSMContext):
    refer = await state.get_value('refer')
    if refer:
        await update_user_ball(refer)

    await state.clear()

    await call.answer("Barchasi tayyor ✅", show_alert=True)
    await call.message.delete()


    settings = db.get_settings()

    await call.message.answer("Ballaringizni ko`rish uchun 👥 Taklif qilinganlar tugmasini bosing", reply_markup=ball())
    await bot.copy_message(chat_id=call.from_user.id,
                               from_chat_id='@audiotd',
                               caption=settings.msg1.replace('{ref}', f"https://t.me/{db.bot.username}?start={call.message.from_user.id}"),
                               reply_markup=taklif_post(),
                               message_id = THUMB)



async def update_user_ball(refer : str):
    user_ball = db.update_ball(refer)
    settings = db.get_settings()

    if user_ball and user_ball >= settings.max_add_count:
        try:
            res = await bot.get_chat_member(chat_id=settings.main_chat, user_id=int(refer))
        except Exception as e:
            res = None

        if res and res.status == "left":
            link = settings.main_chat_url or "https://www.google.com"
            await bot.send_message(refer, f"🎉 Tabriklaymiz yopiq kanalimzga qo'shilishingiz mumkun!",
                                   reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                       [types.InlineKeyboardButton(text="🔗 Qo'shilish", url=link )]
                                   ]))


@dp.chat_join_request()
async def handle_chat_join_request(update: types.ChatJoinRequest):
    user_id = update.from_user.id
    chat_id = update.chat.id
    user_ball = db.get_ball(user_id)
    settings = db.get_settings()

    # Approve if user has enough ball, otherwise decline
    if user_ball and user_ball >= settings.max_add_count:
        try:
            await bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
            setting = db.get_settings()
            await bot.send_message(chat_id = user_id, text = "✅ Kanalga qo'shilish so'rovingiz qabul qilindi!", 
                                   reply_markup = types.InlineKeyboardMarkup(inline_keyboard=[
                                    [types.InlineKeyboardButton(text="↪️ Kanalga o'tish", url=setting.main_chat_url)]   
                                   ]))
        except Exception as e:
            print(f"Error approving join request: {e}")
    else:
        try:
            await bot.decline_chat_join_request(chat_id=chat_id, user_id=user_id)
        except Exception as e:
            print(f"Error declining join request: {e}")



@dp.message(F.text == "👥 Taklif qilinganlar")
async def my_ball(message: types.Message):
    balls = db.get_ball(message.from_user.id)
    reply_markup = None
    settings = db.get_settings()
    user_ball = db.get_ball(message.from_user.id)
    if user_ball and user_ball >= settings.max_add_count:
        try:
            res = await bot.get_chat_member(chat_id=settings.main_chat, user_id=message.from_user.id)
        except Exception as e:
            res = None

        if res and res.status == "left":
            link = settings.main_chat_url or "https://www.google.com"
            reply_markup = types.InlineKeyboardMarkup(inline_keyboard=[ [types.InlineKeyboardButton(text="🔗 Qo'shilish", url=link )] ])
            
    if reply_markup:
        await message.answer(f"Siz {balls} ta dostingizni taklif qildingiz! \n\nYopiq kanalga qo'shilishingiz mumkin👇",
                             reply_markup=reply_markup)
    else:
        await message.answer(f"Siz {balls} ta dostingizni taklif qildingiz !")


@dp.callback_query(F.data == "get_post")
async def my_ball(call: types.CallbackQuery):
    settings = db.get_settings()
    text = settings.msg2.format(ref=f"t.me/{db.bot.username}?start={call.from_user.id}")
    await call.message.answer(
        text,
        reply_markup=post_end(call.from_user.id),
        link_preview_options=types.link_preview_options.LinkPreviewOptions(is_disabled=True)
    )

    text = (
        "🔝 Postni do'stlaringizga yuboring."
        f"\n\n{settings.max_add_count} ta do'stingiz sizning taklif "
        f"havolingiz orqali botga kirib kanallarga a'zo bo'lsa,"
        "bot sizga loyiha kanali uchun bir martalik link beradi."
    )

    await call.message.answer(text)


@dp.callback_query(F.data == "check_joins")
async def check_joins(call: types.CallbackQuery):
    chats = db.get_required_joins()

    status = []

    for chat in chats:
        try:
            res = await call.bot.get_chat_member(chat.chat_id, call.from_user.id)
            status.append(res.status)
        except Exception as e:
            pass

    if "left" in status:
        await call.answer("Barcha kanallarga a'zo bo'lishingiz kerak !", show_alert=True)

    else:
        await call.answer("Barchasi tayyor ✅", show_alert=True)
        await call.message.delete()

        res = db.add_user(call.from_user.id)
        settings = db.get_settings()

        await call.message.answer("Ballaringizni ko`rish uchun 👥 Taklif qilinganlar tugmasini bosing", reply_markup=ball())
        await bot.copy_message(chat_id=call.from_user.id,
                               from_chat_id='@audiotd',
                               caption=settings.msg1.replace('{ref}', f"https://t.me/{db.bot.username}?start={call.message.from_user.id}"),
                               reply_markup=taklif_post(),
                               message_id = THUMB)




@dp.message()
async def main_text_handler(message: types.Message, state: FSMContext):
    db.add_user(message.from_user.id)
    settings = db.get_settings()

    if settings.main_chat:
        try:
            member = await bot.get_chat_member(settings.main_chat, message.from_user.id)
            if member.status not in ("left", "kicked", "banned"):
                await message.answer(
                    "✅ Siz allaqachon yopiq kanalga qo'shilgansiz!",
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                        types.InlineKeyboardButton(text="↪️ Kanalga o'tish", url=settings.main_chat_url)
                    ]])
                )
                return
        except Exception:
            pass

    await state.set_state(UserState.waiting_channel_join)
    await message.answer_photo(photo=FSInputFile('thumb.jpg'), caption=settings.msg1, reply_markup=subcription())