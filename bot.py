import os
import re
import requests
import telebot
import yt_dlp
import instaloader

TOKEN_TELEGRAM = '8838743968:AAGjIYur0Haoy5j-Btb8XR1oVfdTdM5f6Z4'
API_KEY_GEMINI = 'AQ.Ab8RN6JMPbcA_iehap9WK-8h5gNT9jHL3bacDVBJRk9r6uFQsg'

bot = telebot.TeleBot(TOKEN_TELEGRAM)

SYSTEM_PROMPT = (
    "Lu adalah AI companion di Telegram yang karakternya toxic tapi asik, "
    "sarkas, doyan nge-roast, dan hobi ngomong pake gaya bahasa gaul/santai. "
    "Kalau ada orang yang nanya, nge-tag lu, atau nyari lagu, roasting mereka "
    "dengan panggilan yang kocak tapi tetap menghibur."
)

def tanya_gemini(pertanyaan):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={API_KEY_GEMINI}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": pertanyaan}]}],
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]}
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        hasil = response.json()
        if 'error' in hasil:
            return "Dih, server AI-nya lagi sibuk kebanyakan yang nge-roast. Tapi intinya, pilihan lu basi. 🥱"
        return hasil['candidates'][0]['content']['parts'][0]['text']
    except Exception:
        return "Otak AI gw lagi ngadat, tapi tetep aja selera lagu lu ga ada akhlak. 🤡"

# Inisialisasi Instaloader Khusus Instagram
L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    download_video_thumbnails=False,
    save_metadata=False,
    compress_json=False
)

def download_instagram_khusus(url):
    try:
        match = re.search(r'/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)', url)
        if not match:
            return None, None
        shortcode = match.group(1)
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        if post.is_video:
            resp = requests.get(post.video_url, timeout=15)
            return resp.content, True
        else:
            resp = requests.get(post.url, timeout=15)
            return resp.content, False
    except Exception as e:
        print(f"Error Instaloader: {e}")
        return None, None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "Yo! Bot siap ngobrol sekaligus ngetawain lu.\n\n"
        "📌 *Fitur:* \n"
        "• Kirim *Link (YT/TikTok/IG/X)* buat download video/foto\n"
        "• Ketik `/lagu <judul/lirik>` buat cari & download lagu otomatis\n"
        "• Chat biasa / mention di grup buat diajak bacot!",
        parse_mode='Markdown'
    )

# === FITUR BARU: CARI & AUTO-DOWNLOAD LAGU ===
@bot.message_handler(commands=['lagu', 'cari'])
def handle_cari_lagu(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "❌ *Ketik judul atau lirik lagunya bray!*\nContoh: `/lagu Sheila on 7 Dan`", parse_mode='Markdown')
        return

    query_str = args[1]
    msg = bot.reply_to(message, f"Lagi nyari lagu *{query_str}* di internet sekalian nyiapin bahan buat nge-roast... ⏳", parse_mode='Markdown')

    # Bikin komentar/sindiran Gemini tentang selera musiknya
    roast_caption = tanya_gemini(f"Buatin caption roasting pendek yang kocak dan sinis buat orang yang nyari lagu dengan judul/lirik ini: {query_str}")

    try:
        ydl_opts = {
            'outtmpl': 'downloaded_song.%(ext)s',
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'retries': 5,
        }
        
        search_query = f"ytsearch1:{query_str}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            if 'entries' in info and len(info['entries']) > 0:
                info = info['entries'][0]
            filename = ydl.prepare_filename(info)
            title = info.get('title', query_str)

        with open(filename, 'rb') as audio:
            bot.send_audio(
                message.chat.id, 
                audio, 
                caption=f"🎧 *{title}*\n\n{roast_caption}", 
                parse_mode='Markdown'
            )

        bot.delete_message(message.chat.id, msg.message_id)
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        bot.edit_message_text(f"❌ Gagal nemuin/download lagu. Error: {str(e)}", message.chat.id, msg.message_id)

# === HANDLER UTAMA (LINK & CHAT) ===
@bot.message_handler(func=lambda message: True)
def handle_semua(message):
    text = message.text if message.text else ""
    chat_type = message.chat.type
    
    # 1. JALUR DOWNLOAD LINK (URL DIRECT)
    if text.startswith("http://") or text.startswith("https://"):
        msg = bot.reply_to(message, "Lagi ditarik paksa dari internet sekalian gw siapin bahan buat nge-roast... ⏳")
        
        roast_caption = tanya_gemini(f"Buatin caption roasting pendek yang pedas dan kocak buat kiriman dari link ini: {text}")
        download_success = False

        # JALUR INSTAGRAM (Instaloader)
        if "instagram.com" in text:
            content, is_video = download_instagram_khusus(text)
            if content:
                if is_video:
                    bot.send_video(message.chat.id, content, caption=roast_caption)
                else:
                    bot.send_photo(message.chat.id, content, caption=roast_caption)
                download_success = True

        # JALUR YOUTUBE / TIKTOK / X / DLL (yt-dlp)
        if not download_success:
            try:
                ydl_opts = {
                    'outtmpl': 'downloaded_file.%(ext)s', 
                    'format': 'best', 
                    'quiet': True,
                    'no_warnings': True,
                    'socket_timeout': 30,
                    'retries': 5,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(text, download=True)
                    filename = ydl.prepare_filename(info)
                
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.avif')):
                    with open(filename, 'rb') as photo:
                        bot.send_photo(message.chat.id, photo, caption=roast_caption)
                else:
                    with open(filename, 'rb') as video:
                        bot.send_video(message.chat.id, video, caption=roast_caption)
                
                if os.path.exists(filename):
                    os.remove(filename)
                download_success = True
            except Exception as e:
                print(f"Error yt-dlp: {e}")

        if download_success:
            bot.delete_message(message.chat.id, msg.message_id)
        else:
            bot.edit_message_text("❌ Gagal download. Tuh link ngambek, akunnya diprivate, atau udah dihapus.", message.chat.id, msg.message_id)

    # 2. JALUR NGOBROL / ROASTING AI
    else:
        is_group = chat_type in ['group', 'supergroup']
        is_replied_to = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
        is_mentioned = f"@{bot.get_me().username}" in text

        if not is_group or is_replied_to or is_mentioned:
            bot.send_chat_action(message.chat.id, 'typing')
            clean_text = text.replace(f"@{bot.get_me().username}", "").strip()
            if not clean_text:
                clean_text = "Ngapain lu nge-tag gw?"
                
            jawaban = tanya_gemini(clean_text)
            bot.reply_to(message, jawaban)

if __name__ == "__main__":
    print("Bot Complete (Link + Cari Lagu + IG + AI Roast) Jalan Bro! 🚀🔥")
    bot.infinity_polling()
