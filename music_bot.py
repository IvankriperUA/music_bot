import asyncio
import os
import glob
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiohttp import web
import static_ffmpeg

# Налаштування FFmpeg
static_ffmpeg.add_paths()

# Отримуємо токен
API_TOKEN = os.getenv("BOT_TOKEN")

if not API_TOKEN:
    print("Error: BOT_TOKEN variable is not set!")
    exit(1)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Веб-сервер для Render ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    print(f"Web server started on port {port}")
    await site.start()

# --- Логіка бота ---
def cleanup():
    """Видаляє всі mp3 файли в папці /tmp"""
    for file in glob.glob("/tmp/*.mp3"):
        try:
            os.remove(file)
        except Exception as e:
            print(f"Cleanup error: {e}")

def download_track(query):
    cleanup() # Очищуємо перед завантаженням
    
    # Render дозволяє писати ТІЛЬКИ в /tmp
    output_template = "/tmp/%(title)s.%(ext)s"
    
    print(f"Downloading track: {query}")

    # Додаємо --no-check-certificate та куки/user-agent, якщо YouTube блокує
    cmd = (
        f'yt-dlp "ytsearch1:{query}"'
        f' --extract-audio'
        f' --audio-format mp3'
        f' --audio-quality 0'
        f' --no-playlist'
        f' --no-check-certificate'
        f' -o "{output_template}"'
    )

    exit_code = os.system(cmd)
    if exit_code != 0:
        print(f"yt-dlp error code: {exit_code}")
        return None

    files = glob.glob("/tmp/*.mp3")
    return files[0] if files else None

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Привіт! Напиши назву пісні, і я її знайду.")

@dp.message()
async def handle_message(message: types.Message):
    if not message.text or message.text.startswith("/"):
        return  

    status_message = await message.answer(f"⏳ Шукаю та завантажую: {message.text}...")

    loop = asyncio.get_event_loop()
    file_path = await loop.run_in_executor(None, download_track, message.text)

    try:
        if file_path:
            await status_message.edit_text(f"✅ Трек знайдено! Надсилаю...")
            audio = FSInputFile(file_path)
            await message.answer_audio(audio, caption=f"🎵 {os.path.basename(file_path)}")
            
            # Видаляємо файл після відправки
            if os.path.exists(file_path):
                os.remove(file_path)
                
            await status_message.delete()
        else:
            await status_message.edit_text("❌ Не вдалося знайти трек. Спробуй іншу назву.")
    except Exception as e:
        print(f"Error sending track: {e}")
        await status_message.edit_text("⚠️ Сталася помилка під час відправки.")

# --- Головна функція ---
async def main():
    print("Starting bot and web server...")
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped")
