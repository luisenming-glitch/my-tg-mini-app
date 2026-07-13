import asyncio
import logging
import sys
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from openai import AsyncOpenAI

# 載入 .env 保險箱
load_dotenv()
# ================= 密鑰設定區 =================
# 現在程式會自動去 .env 檔案裡面抓取密碼，別人看你的 bot.py 也看不到密碼了！
TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# ============================================

dp = Dispatcher()

ai_client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


# 1. 處理 /start 指令 (已修正為底部鍵盤)
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # 這裡改成 ReplyKeyboardMarkup (底部鍵盤)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="打開 AI 工具箱",
                    web_app=WebAppInfo(url="https://luisenming-glitch.github.io/my-tg-mini-app/")
                )
            ]
        ],
        resize_keyboard=True  # 讓按鈕大小自動適應，不會佔滿全螢幕
    )

    await message.answer(
        f"嗨，{html.bold(message.from_user.full_name)}！\n"
        f"看你的畫面最下方 👇\n"
        f"請點擊底部的「打開 AI 工具箱」按鈕來啟動網頁：",
        reply_markup=kb
    )


# 2. 處理對話與網頁傳來的資料
@dp.message()
async def ai_handler(message: Message) -> None:
    try:
        # 情況 A：如果訊息是從 Web App (網頁) 傳送過來的資料
        if message.web_app_data:
            data = message.web_app_data.data
            waiting_msg = await message.answer("🤖 網頁資料已接收，正在為您進行 AI 分析...")

            response = await ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": f"請幫我分析以下內容：\n{data}"}]
            )
            await waiting_msg.edit_text(response.choices[0].message.content)

        # 情況 B：如果是用戶在 Telegram 直接打字的普通對話
        elif message.text:
            waiting_msg = await message.answer("🤔 讓我思考一下...")

            response = await ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system",
                     "content": "你是一個幽默、專業的 Telegram 助手，請用繁體中文簡短、友善地回答用戶的問題。"},
                    {"role": "user", "content": message.text}
                ]
            )
            await waiting_msg.edit_text(response.choices[0].message.content)

    except Exception as e:
        await message.answer(f"哎呀，我的腦袋當機了：\n{e}")


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    print("🚀 DeepSeek AI 機器人已啟動... 按 Ctrl+C 可以停止。")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())