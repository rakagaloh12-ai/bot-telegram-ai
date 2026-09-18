import os
import telebot
import yt_dlp

# Token Bot Telegram Kamu
TOKEN = "8838743968:AAGjIYur0Haoy5j-Btb8XR1oVfdTdM5f6Z4"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "🤖 *Bot Media Downloader & AI*\n\n"
        "Cara pakai:\n"
        "1. `/lagu <judul>` -> Cari & download MP3 YouTube\n"
        "2. *Kirim Link Langsung* -> Download video/reels dari TikTok, IG, YT, X, FB, dll."
    )
    bot.reply_to(message, text, parse_mode='Markdown')

# --- 1. FITUR CARI LAGU VIA COMMAND /lagu ---
@bot.message_handler(commands=['lagu'])
def download_song(message):
    query_str = message.text.replace('/lagu', '').strip()
    
    if not query_str:
        bot.reply_to(message, "Harap masukkan judul lagu. Contoh: `/lagu Wonderwall`", parse_mode='Markdown')
        return

    msg = bot.reply_to(message, f"🔍 Mencarikan lagu *{query_str}*...", parse_mode='Markdown')

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'max_filesize': 50 * 1024 * 1024, # Max 50 MB
        'ffmpeg_location': '.', # Lokasi ffmpeg lokal di folder bot
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    filename = None
    try:
        search_query = f"ytsearch1:{query_str}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            if 'entries' in info and len(info['entries']) > 0:
                info = info['entries'][0]
            
            base_filename = ydl.prepare_filename(info)
            filename = os.path.splitext(base_filename)[0] + ".mp3"
            title = info.get('title', query_str)

        if os.path.exists(filename):
            if os.path.getsize(filename) > 50 * 1024 * 1024:
                bot.edit_message_text("❌ Ukuran file lebih dari 50 MB (batas Telegram).", message.chat.id, msg.message_id)
                os.remove(filename)
            else:
                with open(filename, 'rb') as audio:
                    bot.send_audio(message.chat.id, audio, caption=f"🎧 *{title}*", parse_mode='Markdown')
                bot.delete_message(message.chat.id, msg.message_id)
                os.remove(filename)
        else:
            bot.edit_message_text("❌ Gagal memproses file lagu.", message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, msg.message_id)
        if filename and os.path.exists(filename):
            os.remove(filename)


# --- 2. FITUR DOWNLOAD LANGSUNG LEWAT LINK (TikTok, IG, YT, dll) ---
@bot.message_handler(func=lambda message: message.text and message.text.startswith(('http://', 'https://')))
def download_from_link(message):
    url = message.text.strip()
    msg = bot.reply_to(message, "⏳ Sedang mengunduh media dari link...")

    ydl_opts = {
        'format': 'best[filesize<50M]/bestvideo[filesize<25M]+bestaudio/best',
        'outtmpl': 'downloaded_media.%(ext)s',
        'max_filesize': 50 * 1024 * 1024,
        'ffmpeg_location': '.', # Lokasi ffmpeg lokal
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'quiet': True
    }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Media')

        if os.path.exists(filename):
            if os.path.getsize(filename) > 50 * 1024 * 1024:
                bot.edit_message_text("❌ Ukuran media lebih dari 50 MB.", message.chat.id, msg.message_id)
                os.remove(filename)
            else:
                with open(filename, 'rb') as media_file:
                    if filename.endswith(('.mp4', '.mkv', '.webm', '.mov')):
                        bot.send_video(message.chat.id, media_file, caption=f"🎬 *{title}*", parse_mode='Markdown')
                    else:
                        bot.send_document(message.chat.id, media_file, caption=f"📁 *{title}*", parse_mode='Markdown')
                
                bot.delete_message(message.chat.id, msg.message_id)
                os.remove(filename)
        else:
            bot.edit_message_text("❌ Gagal mengunduh file dari link tersebut.", message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Gagal download dari link. Error: {str(e)}", message.chat.id, msg.message_id)
        if filename and os.path.exists(filename):
            os.remove(filename)

# Jalankan Bot
bot.infinity_polling()
