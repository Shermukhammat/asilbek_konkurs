import asyncio
from typing import List

from aiogram import types, F, Bot, exceptions
from aiogram.filters.command import Command
from aiogram.filters import BaseFilter
from aiogram.filters.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder

from aiogram_media_group import media_group_handler

from manager.m import dp, db, bot


class Form(StatesGroup):
    get_msg1 = State()
    get_msg2 = State()
    get_link = State()
    get_count = State()

    send_message = State()
    choose_chat1 = State()
    choose_chat2 = State()


class IsAdmin(BaseFilter):
    async def __call__(self, event):
        user_id = event.from_user.id

        if user_id in [1661189380, 5816151899, 5811443685]:
            return True
        return False


def select_chat():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(
                    text="Kanal Tanlash",
                    request_chat=types.KeyboardButtonRequestChat(request_id=1, chat_is_channel=True)
                ),
                types.KeyboardButton(
                    text="Gruppa Tanlash",
                    request_chat=types.KeyboardButtonRequestChat(request_id=2, chat_is_channel=False)
                ),
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def required_chat():
    keyboards = []

    chats = db.get_required_joins()
    c = 1
    for chat in chats:
        keyboards.append(
            [
                types.InlineKeyboardButton(text=f"{c}", callback_data=f"delete_chat:{chat.chat_id}"),
            ]
        )
        c += 1

    keyboards.append(
        [
            types.InlineKeyboardButton(text="❌", callback_data="delete")
        ]
    )

    return types.InlineKeyboardMarkup(
        inline_keyboard=keyboards
    )


@dp.message(IsAdmin(), Command("cancel"))
async def admin_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi")


@dp.message(IsAdmin(), Command("admin"))
async def admin_handler(message: types.Message):
    text = (
        "Admin commandalar ro'yxati:"
        "\n\n/admin - Admin panel"
        "\n\n/set_start_text - Startdagi matnni o'zgartrish"
        "\n\n/set_chat - Maxfiy chatni o'zgartrish"
        "\n\n/set_post_text - Postdagi matnni o'zgartrish"
        "\n\n/set_add_count - Odam qo'shish sonini o'zgartrish"
        "\n\n/add_chat - Majburiy kanal/group qo'shishi"
        "\n\n/del_chat - Majburiy kanal/group ni olib tashlash"
        "\n\n/stat - Statistika"
        "\n\n/send_message - Xabar yuborish"
        "\n\n/base - Bazani yuklab olish"
    )

    await message.answer(text=text)


@dp.message(IsAdmin(), Command("base"))
async def admin_handler(message: types.Message):
    file = types.FSInputFile('base.db')
    await message.answer_document(file, caption="Botdagi barcha malumotlar")


@dp.message(IsAdmin(), Command("set_start_text"))
async def admin_handler(message: types.Message, state: FSMContext):
    await state.set_state(Form.get_msg1)
    await message.answer("Start uchun matn yuboring:")


@dp.message(Form.get_msg1)
async def get_msg1(message: types.Message, state: FSMContext):
    new = message.text
    db.edit_settings('msg1', new)

    await state.clear()
    await message.answer("O'zgartrildi")


@dp.message(IsAdmin(), Command("set_post_text"))
async def admin_handler(message: types.Message, state: FSMContext):
    await state.set_state(Form.get_msg2)
    await message.answer("Post uchun matn yuboring:")


@dp.message(Form.get_msg2)
async def get_msg1(message: types.Message, state: FSMContext):
    new = message.text
    db.edit_settings('msg2', new)

    await state.clear()
    await message.answer("O'zgartrildi")


@dp.message(IsAdmin(), Command("set_add_count"))
async def admin_handler(message: types.Message, state: FSMContext):
    await state.set_state(Form.get_count)
    await message.answer("Qancha odam qo'shgach havola berilsin:")


@dp.message(Form.get_count)
async def get_msg1(message: types.Message, state: FSMContext):
    new = message.text

    if new.isdigit():
        db.edit_settings('max_add_count', new)

        await state.clear()
        await message.answer("O'zgartrildi")

    else:
        await message.answer("Faqat raqam kriting: ")


@dp.message(IsAdmin(), Command("add_chat"))
async def admin_handler(message: types.Message, state: FSMContext):
    await state.set_state(Form.choose_chat1)
    await message.answer("Majburiy azolik qo'shish uchun chatni tanlang:", reply_markup=select_chat())


@dp.message(F.chat_shared, Form.choose_chat1)
async def get_chat(message: types.Message, state: FSMContext):
    await state.update_data(chat_id=message.chat_shared.chat_id)
    await message.answer("Yaxshi, chatga qo'shilish linkini yuboring")

    await state.set_state(Form.get_link)


@dp.message(Form.get_link)
async def get_msg1(message: types.Message, state: FSMContext):
    data = await state.get_data()
    link = message.text
    chat_id = data['chat_id']

    db.add_required_joins(chat_id=chat_id, link=link)

    await message.answer("Qo'shildi botni admin qilish esdan chiqmasin !!!")
    await state.clear()


@dp.message(IsAdmin(), Command("del_chat"))
async def admin_handler(message: types.Message):
    text = "Majburiy azolikdan olib tashlash uchun chatni tanlang:"

    chats = db.get_required_joins()
    c = 1
    for chat in chats:
        text += f"\n{c}) {chat.link}"
        c += 1

    await message.answer(text, reply_markup=required_chat())


@dp.callback_query(F.data.startswith("delete_chat:"))
async def delete_chat(call: types.CallbackQuery):
    chat_id = call.data.split(":")[1]
    db.delete_required_joins(chat_id)

    await call.answer("O'chirib yuborildi !", show_alert=True)
    await call.message.delete()


@dp.callback_query(F.data == "delete")
async def del_msg(call: types.CallbackQuery):
    await call.message.delete()


@dp.message(IsAdmin(), Command("stat"))
async def admin_handler(message: types.Message, state: FSMContext):
    all_users = db.get_all_users()
    await state.set_state(Form.send_message)
    await message.answer(f"Botdagi barcha azolar soni: {len(all_users)}")


@dp.message(IsAdmin(), Command("send_message"))
async def admin_handler(message: types.Message, state: FSMContext):
    await state.set_state(Form.send_message)
    await message.answer(f"Xabar yuboring: \nBekor qilish uchun /cancel")


@dp.message(IsAdmin(), Command("set_chat"))
async def admin_handler(message: types.Message, state: FSMContext):
    await state.set_state(Form.choose_chat2)
    await message.answer("Chat ni tanlang:", reply_markup=select_chat())


@dp.message(F.chat_shared, Form.choose_chat2)
async def get_chat(message: types.Message, state: FSMContext):
    chat_id = message.chat_shared.chat_id

    # Check if bot is admin
    try:
        bot_id = db.bot.id
        member = await bot.get_chat_member(chat_id, bot_id)
        is_admin = member.status in ["administrator", "creator"]
    except Exception as e:
        await message.answer(f"Xato: botning chatdagi holatini tekshirib bo'lmadi.\n{e}")
        await state.clear()
        return

    if not is_admin:
        await message.answer("Bot bu chatda admin emas! Avval botni admin qiling va qayta urinib ko'ring.")
        await state.clear()
        return

    # Create never-expiring invite link with join request
    try:
        invite = await bot.create_chat_invite_link(
            chat_id,
            creates_join_request=True,
            expire_date=None,
        )
        link = invite.invite_link
    except Exception as e:
        await message.answer(f"Havola yaratishda xato:\n{e}")
        await state.clear()
        return

    db.edit_settings('main_chat', chat_id)
    db.edit_settings('main_chat_url', link)

    await message.answer(f"O'zgartrildi ✅\nHavola: {link}")
    await state.clear()


@dp.message(Form.get_count)
async def get_msg1(message: types.Message, state: FSMContext):
    new = message.text

    if new.isdigit():
        db.edit_settings('max_add_count', new)

        await state.clear()
        await message.answer("O'zgartrildi")

    else:
        await message.answer("Faqat raqam kriting: ")


@dp.message(F.media_group_id, Form.send_message)
@media_group_handler
async def send_user(m: List[types.Message], bot: Bot, state: FSMContext):
    try:
        await state.clear()

        users = db.get_all_users()

        text = (
            "Xabar yuborish jarayoni 💬:"
            "\n  Holati: Yuborilmoqda !"
            "\n\nMalumot ℹ️:"
            f"\n  Foydalanuvchilar soni: {len(users)}"
        )

        await m[-1].answer(text=text)

        caption = ""

        for i in m:
            if i.caption:
                caption = i.caption

        media_group = MediaGroupBuilder(caption=caption)

        for i in m:
            if i.video:
                media_group.add(type="video", media=i.video.file_id)
            elif i.photo:
                media_group.add(type="photo", media=i.photo[0].file_id)

            elif i.document:
                media_group.add(type="document", media=i.document.file_id)

            elif i.audio:
                media_group.add(type="audio", media=i.audio.file_id)

        if users:
            y = n = 0

            for user in users:
                try:
                    await bot.send_media_group(
                        chat_id=user.user_id, media=media_group.build()
                    )
                    await asyncio.sleep(0.06)

                except exceptions.TelegramForbiddenError:
                    n += 1

                except exceptions.TelegramBadRequest:
                    n += 1

                except exceptions.TelegramRetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                    await bot.send_media_group(
                        chat_id=user.user_id, media=media_group.build()
                    )
                    await asyncio.sleep(0.06)

                else:
                    y += 1

            text = (
                "Xabar yuborish jarayoni 💬:"
                "\n  Holati: Yuborildi!"
                "\n\nMalumot ℹ️:"
                f"\n  Yuborildi: {y}"
                f"\n  Yuborilmadi: {n}"
            )

            try:
                await m[-1].answer(text=text)
            except Exception as e:
                print(e)

        else:
            text = (
                "Xabar yuborish jarayoni 💬:"
                "\n  Holati: Xato"
                "\n\nMalumot ℹ️:"
                f"\n  Foydalanuvchilar topilmadi"
            )

            try:
                await m[-1].answer(text=text)
            except Exception as e:
                print(e)

    except Exception as e:
        print(e)


@dp.message(Form.send_message)
async def getmsg(m: types.Message, state: FSMContext):
    try:
        await state.clear()
        await m.delete()

        users = db.get_all_users()

        text = (
            "Xabar yuborish jarayoni 💬:"
            "\n  Holati: Yuborilmoqda !"
            "\n\nMalumot ℹ️:"
            f"\n  Foydalanuvchilar soni: {len(users)}"
        )

        await m.answer(text=text)

        if users:
            y = n = 0

            for user in users:
                try:
                    await m.send_copy(chat_id=user.user_id)
                    await asyncio.sleep(0.06)

                except exceptions.TelegramForbiddenError:
                    n += 1

                except exceptions.TelegramBadRequest:
                    n += 1

                except exceptions.TelegramRetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                    await m.send_copy(chat_id=user.user_id)
                    await asyncio.sleep(0.06)

                else:
                    y += 1

            text = (
                "Xabar yuborish jarayoni 💬:"
                "\n  Holati: Yuborildi!"
                "\n\nMalumot ℹ️:"
                f"\n  Yuborildi: {y}"
                f"\n  Yuborilmadi: {n}"
            )

            try:
                await m.answer(text=text)
            except Exception as e:
                print(e)

        else:
            text = (
                "Xabar yuborish jarayoni 💬:"
                "\n  Holati: Xato"
                "\n\nMalumot ℹ️:"
                f"\n  Foydalanuvchilar topilmadi"
            )

            try:
                await m.answer(text=text)
            except Exception as e:
                print(e)

    except Exception as e:
        print(e)
