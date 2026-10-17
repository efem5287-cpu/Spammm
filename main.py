# language: Python, file: main.py, target: Railway Deploy
import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

print("-> Mini sunucu başlatılıyor...", flush=True)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot aktif!")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()
print("-> Mini sunucu aktifleşti, port dinleniyor.", flush=True)

API_ID = 35762182
API_HASH = "126917ba7359f8cddb0780ad16e0b1ba"
BOT_TOKEN = "8967100543:AAGtDqBnFaC7dXe_NeNyqvxgxWMUiUAz14E"
CHANNEL_USERNAME = "swarovskiyeniden"

print("-> Pyrogram istemcisi oluşturuluyor...", flush=True)
app = Client("swarovski_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_states = {}

async def check_membership(client: Client, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception:
        return False
    return False

@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    is_member = await check_membership(client, user_id)
    
    if is_member:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Spam İşlemleri", callback_data="spam_menu")],
            [InlineKeyboardButton("Yapımcı", callback_data="author_info")]
        ])
        await message.reply_text("Hoş geldiniz! Kanala katılımınız doğrulandı. İşleminizi seçin:", reply_markup=keyboard)
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Kanala Katıl", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton("Kontrol Et", callback_data="check_join")]
        ])
        await message.reply_text("Botu kullanabilmek için önce kanalımıza katılmalısınız:", reply_markup=keyboard)

@app.on_callback_query(filters.regex("check_join"))
async def verify_join(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    is_member = await check_membership(client, user_id)
    
    if is_member:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Spam İşlemleri", callback_data="spam_menu")],
            [InlineKeyboardButton("Yapımcı", callback_data="author_info")]
        ])
        await callback_query.message.edit_text("Teşekkürler! Katılım doğrulandı, menüye yönlendiriliyorsunuz:", reply_markup=keyboard)
    else:
        await callback_query.answer("Hala kanala katılmadınız! Lütfen önce katılın.", show_alert=True)

@app.on_callback_query(filters.regex("author_info"))
async def author_handler(client: Client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Geri", callback_data="back_start")]])
    await callback_query.message.edit_text("Yapımcı: @Onlymx", reply_markup=keyboard)

@app.on_callback_query(filters.regex("back_start"))
async def back_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    is_member = await check_membership(client, user_id)
    if is_member:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Spam İşlemleri", callback_data="spam_menu")],
            [InlineKeyboardButton("Yapımcı", callback_data="author_info")]
        ])
        await callback_query.message.edit_text("Ana menüdesiniz:", reply_markup=keyboard)

@app.on_callback_query(filters.regex("spam_menu"))
async def spam_menu_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_states[user_id] = {"step": "waiting_target"}
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Geri", callback_data="back_start")]])
    await callback_query.message.edit_text("Hangi gruba veya kanala spam atmak istiyorsunuz? Lütfen bağlantıyı veya kullanıcı adını gönderin (Örn: @kanaladi):", reply_markup=keyboard)

@app.on_message(filters.text & ~filters.command("start"))
async def message_flow_handler(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return
    
    state = user_states[user_id].get("step")
    
    if state == "waiting_target":
        user_states[user_id]["target"] = message.text
        user_states[user_id]["step"] = "waiting_text"
        await message.reply_text("Beni kanala/gruba yönetici olarak ekleyin ve ne yazacağımı söyleyin:")
        
    elif state == "waiting_text":
        user_states[user_id]["text"] = message.text
        user_states[user_id]["step"] = "waiting_count"
        await message.reply_text("Kaç tane atayım? (Maksimum 150):")
        
    elif state == "waiting_count":
        try:
            count = int(message.text)
            if count > 150:
                count = 150
            elif count < 1:
                count = 1
        except ValueError:
            await message.reply_text("Lütfen geçerli bir sayı girin (Maks 150):")
            return
        
        target = user_states[user_id]["target"]
        text = user_states[user_id]["text"]
        
        await message.reply_text(f"Spam işlemi başlatıldı! Hedef: {target} | Adet: {count}")
        asyncio.create_task(run_spam_loop(client, message, target, text, count))
        del user_states[user_id]

async def run_spam_loop(client, message, target, text, count):
    success = 0
    for i in range(count):
        try:
            await client.send_message(target, text)
            success += 1
            await asyncio.sleep(1.5)
        except Exception as e:
            await message.reply_text(f"Hata oluştu ({i+1}. mesaj): {e}")
            break
    await message.reply_text(f"İşlem tamamlandı! Toplam {success} mesaj gönderildi.")

async def main():
    print("-> Bot Telegram'a bağlanıyor...", flush=True)
    await app.start()
    print("-> BOT BAŞARIYLA AKTİF EDİLDİ!", flush=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
    
