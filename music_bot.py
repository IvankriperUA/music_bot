import asyncio
import os
import glob
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

# Токен
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def cleanup():
    for file in glob.glob("*.mp3"):
        try:
            os.remove(file)
        except:
            pass

def download_track(query):
    cleanup()


    print(f"Downloading track: {query}")


    cmd = (
        f'yt-dlp "ytsearch1:{query}"'
        f' --extract-audio'
        f' --audio-format mp3'
        f' --audio-quality 0'
        f' -o "%(title)s.%(ext)s"'
    )

    exit_code = os.system(cmd)

    if exit_code != 0:
        print(f"Error downloading track: {query}")
        return None


    files = glob.glob("*.mp3")


    if files:
        print(f"Track downloaded successfully: {files[0]}")
        return files[0]
    return None

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Привіт! Введи назву треку, який хочеш завантажити.")


@dp.message()
async def handle_message(message: types.Message):
    if not message.text or message.text.startswith("/"):
        return  

    status_message = await message.answer(f"Завантаження  {message.text}...")

    loop = asyncio.get_event_loop()

    file_path = await loop.run_in_executor(None, download_track, message.text)


    try:
        if file_path:
            await status_message.edit_text(f"Трек завантажено: {os.path.basename(file_path)}")

            audio = FSInputFile(file_path)

            await message.answer_audio(audio, caption=f"Ось твій трек: {os.path.basename(file_path)}")

            os.remove(file_path)

            await status_message.delete()
        else:
            await status_message.edit_text("Не вдалося завантажити трек. Спробуйте ще раз.")

    except Exception as e:
        print(f"Error sending track: {e}")

        await status_message.edit_text("Сталася помилка при відправці треку. Спробуйте ще раз.")


async def main():
    print("Starting bot...")
    await dp.start_polling(bot)           


if __name__ == '__main__':
    asyncio.run(main())