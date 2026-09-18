import os
import telebot
import yt_dlp

# Masukkan Token Bot Telegram Kamu di sini
TOKEN = "TOKEN_BOT_TELEGRAM_KAMU"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Halo! Kirim perintah /lagu <judul lagu> untuk mendownload musik.")

@bot.message_handler(commands=['lagu'])
def download_song(message):
    query_str = message.text.replace('/lagu', '').strip()
    
    if not query_str:
        bot.reply_to(message, "Harap masukkan judul lagu. Contoh: `/lagu Wonderwall`", parse_mode='Markdown')
        return

    msg = bot.reply_to(message, f"🔍 Mencarikan lagu *{query_str}*...", parse_mode='Markdown')

    # Pengaturan yt-dlp dengan bypass client android & batas ukuran file 50MB
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'max_filesize': 50 * 1024 * 1024, # Batas max 50 MB
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
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
            
            # Mendapatkan nama file yang terunduh (.mp3)
            base_filename = ydl.prepare_filename(info)
            filename = os.path.splitext(base_filename)[0] + ".mp3"
            title = info.get('title', query_str)

        # Cek ukuran file sebelum dikirim ke Telegram
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            max_bytes = 50 * 1024 * 1024  # 50 MB

            if file_size > max_bytes:
                bot.edit_message_text("❌ Ukuran file terlalu besar (lebih dari 50 MB). Batas maksimal dari Telegram adalah 50 MB.", message.chat.id, msg.message_id)
                os.remove(filename)
            else:
                # Kirim Audio ke User
                with open(filename, 'rb') as audio:
                    bot.send_audio(
                        message.chat.id,
                        audio,
                        caption=f"🎧 *{title}*",
                        parse_mode='Markdown'
                    )
                bot.delete_message(message.chat.id, msg.message_id)
                
                # Auto-delete file dari server Alwaysdata
                os.remove(filename)
        else:
            bot.edit_message_text("❌ Gagal memproses file lagu.", message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Gagal nemuin/download lagu. Error: {str(e)}", message.chat.id, msg.message_id)
        if filename and os.path.exists(filename):
            os.remove(filename)

# Jalankan Bot
bot.infinity_polling()
