import os
import glob
import telebot
import yt_dlp

# Token Bot Telegram
TOKEN = "8838743968:AAGjIYur0Haoy5j-Btb8XR1oVfdTdM5f6Z4"
bot = telebot.TeleBot(TOKEN)

# Dapatkan direktori saat ini untuk lokasi ffmpeg lokal
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "🤖 *Bot Media Downloader*\n\n"
        "Cara pakai:\n"
        "1. `/lagu <judul>` -> Cari & download MP3 YouTube\n"
        "2. *Kirim Link Langsung* -> Download video/reels/gambar dari TikTok, IG, YT, X, FB, dll."
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
        'outtmpl': os.path.join(BASE_DIR, 'song_%(id)s.%(ext)s'),
        'max_filesize': 50 * 1024 * 1024, # Max 50 MB
        'ffmpeg_location': BASE_DIR,
        'socket_timeout': 60,
        'retries': 10,
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
            
            title = info.get('title', query_str)
            media_id = info.get('id', '')
            
            # Cari file mp3 yang dihasilkan
            possible_files = glob.glob(os.path.join(BASE_DIR, f"song_{media_id}.*"))
            if possible_files:
                filename = possible_files[0]

        if filename and os.path.exists(filename):
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
            try:
                os.remove(filename)
            except:
                pass


# --- 2. FITUR DOWNLOAD LANGSUNG LEWAT LINK (TikTok, IG, YT, dll) ---
@bot.message_handler(func=lambda message: message.text and message.text.startswith(('http://', 'https://')))
def download_from_link(message):
    url = message.text.strip()
    msg = bot.reply_to(message, "⏳ Sedang mengunduh media dari link...")

    # yt-dlp otomatis memilih opsi video/foto/audio terbaik di bawah 50MB
    ydl_opts = {
        'format': 'best[filesize<50M]/bestvideo[filesize<40M]+bestaudio/best',
        'outtmpl': os.path.join(BASE_DIR, 'media_%(id)s.%(ext)s'),
        'max_filesize': 50 * 1024 * 1024,
        'ffmpeg_location': BASE_DIR,
        'socket_timeout': 60,  # Cegah Read Timeout
        'retries': 10,         # Coba ulang koneksi jika lag
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'quiet': True
    }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Media')
            media_id = info.get('id', '')

            # Cari file hasil unduhan
            possible_files = glob.glob(os.path.join(BASE_DIR, f"media_{media_id}.*"))
            if possible_files:
                filename = possible_files[0]

        if filename and os.path.exists(filename):
            if os.path.getsize(filename) > 50 * 1024 * 1024:
                bot.edit_message_text("❌ Ukuran media lebih dari 50 MB.", message.chat.id, msg.message_id)
                os.remove(filename)
            else:
                ext = os.path.splitext(filename)[1].lower()
                with open(filename, 'rb') as media_file:
                    if ext in ['.mp4', '.mkv', '.webm', '.mov']:
                        bot.send_video(message.chat.id, media_file, caption=f"🎬 *{title}*", parse_mode='Markdown')
                    elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        bot.send_photo(message.chat.id, media_file, caption=f"🖼️ *{title}*", parse_mode='Markdown')
                    elif ext in ['.mp3', '.m4a', '.ogg', '.wav']:
                        bot.send_audio(message.chat.id, media_file, caption=f"🎵 *{title}*", parse_mode='Markdown')
                    else:
                        bot.send_document(message.chat.id, media_file, caption=f"📁 *{title}*", parse_mode='Markdown')
                
                bot.delete_message(message.chat.id, msg.message_id)
                os.remove(filename)
        else:
            bot.edit_message_text("❌ Gagal mengunduh file dari link tersebut.", message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Gagal download dari link. Error: {str(e)}", message.chat.id, msg.message_id)
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

# Jalankan Bot
bot.infinity_polling()
