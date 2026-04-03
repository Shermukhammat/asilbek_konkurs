from aiogram import Bot, types, Dispatcher
from aiogram.client.default import DefaultBotProperties

from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Dict, Any

from data.settings import TOKEN, THUMB
from utils.database import DataBase


from aiogram.types import Chat, User
from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    waiting_new_user = State()
    waiting_channel_join = State()



bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
db = DataBase()


def subcription():
    keyboards = []

    chats = db.get_required_joins()
    for chat in chats:
        keyboards.append(
            [
                types.InlineKeyboardButton(text="Qo'shilish ➕", url=chat.link)
            ]
        )

    keyboards.append(
        [
            types.InlineKeyboardButton(text="✅ A'zo bo'ldim", callback_data="check_joins")
        ]
    )

    return types.InlineKeyboardMarkup(
        inline_keyboard=keyboards
    )


class SubcriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any],
    ):
        calldata = data["event_update"].callback_query
    
        if calldata and calldata.data in ["check_joins"]:
            return await handler(event, data)

        elif not calldata:
            if event.text and 'start' in event.text:
                return await handler(event, data)

        chats = db.get_required_joins()
        status = []

        for chat in chats:
            try:
                res = await event.bot.get_chat_member(chat.chat_id, event.from_user.id)
                status.append(res.status)
            except:
                pass

        if "left" in status:
            if isinstance(event, types.Message) and event.chat.id in [6980153003, 5816151899]:
                return await handler(event, data)

            elif isinstance(event, types.CallbackQuery) and event.message.from_user.id in [6980153003, 5816151899]:
                return await handler(event, data)
            
            
            text = (
                "🚀 Loyihada ishtirok etish uchun quyidagilarga kanallarga azo boʼling."
                "\n\nKeyin ✅ А'zo boʼldim tugmasini bosing"
            )

            if isinstance(event, types.Message):
                await event.answer(text, reply_markup=subcription())

            elif isinstance(event, types.CallbackQuery):
                await event.message.answer(text, reply_markup=subcription())

        else:
            return await handler(event, data)
        


async def check_subscription(update : types.Message):
    chats = db.get_required_joins()
    status = []

    for chat in chats:
        try:
            res = await bot.get_chat_member(chat.chat_id, update.from_user.id)
            status.append(res.status)
        except:
            pass

        if "left" in status:            
            text = (
                "🚀 Loyihada ishtirok etish uchun quyidagilarga kanallarga azo boʼling."
                "\n\nKeyin ✅ А'zo boʼldim tugmasini bosing"
            )
            await update.answer(text, reply_markup=subcription())
            return False
        return True





