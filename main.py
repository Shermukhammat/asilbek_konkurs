import asyncio

from manager.m import bot, dp, db
from handlers import *


async def on_startup(dispatcher):
    me = await bot.get_me() 
    print(f'bot: [@{me.username}]')
    db.bot = me
async def main():
    dp.startup.register(on_startup)
    print("Running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        quit(0)
