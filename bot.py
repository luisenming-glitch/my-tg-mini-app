import asyncio
import logging
import sys
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from openai import AsyncOpenAI

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

dp = Dispatcher()
ai_client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# 記憶庫：用嚟記住每個用戶想用邊個人設
user_personalities = {}

# 定義人設內容
PERSONALITIES = {
    "teacher": "你是一個專業英文老師，會糾正用戶語法。",
    "sassy": "你是一個說話很串的香港朋友，喜歡挖苦人，但最後還是會幫忙。",
    "cat": "你是一隻可愛的貓咪，說話結尾都要加上「喵～」。"
}


# 顯示切換按鈕
@dp.message(Command("switch"))
async def cmd_switch(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍🏫 英文老師", callback_data="teacher")],
        [InlineKeyboardButton(text="🤬 寸嘴朋友", callback_data="sassy")],
        [InlineKeyboardButton(text="🐱 貓咪", callback_data="cat")]
    ])
    await message.answer("請選擇你的 AI 好友風格：", reply_markup=kb)


# 處理按鈕點擊
@dp.callback_query()
async def callback_handler(callback: CallbackQuery):
    user_personalities[callback.from_user.id] = PERSONALITIES[callback.data]
    await callback.message.edit_text(f"已切換至：{callback.data} 模式！可以開始傾偈啦。")


# 對話處理
@dp.message(F.text)
async def ai_handler(message: Message):
    # 預設人設
    system_prompt = user_personalities.get(message.from_user.id, "你是一個有用的 AI 助手。")

    waiting_msg = await message.answer("🤔 思考中...")
    try:
        response = await ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message.text}
            ]
        )
        await waiting_msg.edit_text(response.choices[0].message.content)
    except Exception as e:
        await waiting_msg.edit_text(f"當機了: {e}")


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())