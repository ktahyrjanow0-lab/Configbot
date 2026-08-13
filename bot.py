import os
import logging
import datetime
import io
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, filters
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = '8971630911:AAHXnu44Rp4sKaNRtNoTDFHEHxbLpFaH4fQ'
ADMIN_ID = 5330851495
API_KEY = 'AIzaSyDxZxoxeHEeseIt10HXDo1fkTNvQt1NHSI'
DATABASE_FILE = 'files.json'
SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
WAITING_FOR_FILENAME, WAITING_FOR_CONFIG = range(2)

# JSON'u oluştur
SERVICE_ACCOUNT_DATA = {
    "type": "service_account",
    "project_id": "hemdem",
    "private_key_id": "ef5c4252d896057d8f3dbf48ee62ed234f4cc8a4",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC9l3vu229e6C8k\n4R5idO5ZFb7f+YMC+QqZQ5oBg0IZQp0c0hzu/aWo+iTDKuuKHidPD0iiP7NPl8SL\nx28xRO6z+Gxot1d5JtDQbd31Bie7ahmz50uwr13LlYOUCc0MqupPlKKC9WzNfray\nbv1Gn3D4vsn7klXo29aVb7YZDJQIFWV6X6dlJKZKDML1SNOH9l8Rc3CJQOma7yxT\nUGJOZoEwHzp0QMFVuWNfej07UVb/fvJKsbAMUxIJzfmGzHOlKwEwkrNr0BkRVM33\niT0clX3cQ+ygM9ggeKpmv+zbmnodlm6nSWSjSAX7qjCfkDZYtuGNJ5334RYBBjeD\nZR5dtU3NAgMBAAECggEALRlLQErPh8Z4bG/mf+orxmIvWOzr9rmSBVo42LJF92dK\no0/x1QHeNb9nHkvn4p+An0RV9U5s03qZJNzofNJWa9Ykx5YRRz7t/h6cZUw1CFZZ\nTduvvBRDHgnvVjgsoB5KBWsoazmBS7KgN/rB4dpMj8cmmeK5793Xgg2kRfohfnhb\nYu2ZImP7Eof6mckJrKAHuBhf2cWg1VI3DH+pC+MsXnuF5RH99PZNmmWNhBg5FJX6\njvZdPut0vAVC2QH4SBMgt5ziytgXWwb82IvPwgiZf6Sal6CRNAGjV0QrRoxYQ12h\nkkUXaIuQ/wyQhKDEDHJI6KAB+2PO3IZcmSUm/UtYMQKBgQDthJzTssng5iXeRnm/\nLlz2hKazaAFxUthvq+Q5E41rSNZln4H0qTs4I5+G2zdmV/GfOLHqWWAds4uksvet\ntNYK7LOq1H7s4VxZeVRMHpltLEogHS+COx43LGe10IxZtPYKR1+AVHDXY/hslX8M\nuZryT3bnvF4+6ZSWdNQb2bsYpQKBgQDMWCyYdxitB27E7YtTadH1LhacZllhhcIc\nog65GrlryuTRxFWFpOj/I6nHQQtyBDmISvD3DHEd6GrDRdSz6E/ChIMTZpa4xsc3\nxDVQZwi5uXDj+3TXOIFWmVNFgbz72fW+LRyU3APUs05K54Uo6XN8tC365EKJ1xwW\nqHJIiXCwCQKBgCTOpC76SeacQ8oKSduip61cKSksOO0C1Z+Yl6lwqj2x7+eXrF/p\nyc+NVa9kUVV+02bFNm0GpKp1pHJFebRljbXrsHwMqg6zbcg/0RxqsYQFlQcc/rvD\nxY7vRrMaOmW8cVRucxJEA6idSWYqVKH4MVbTka2ft0swj2IxgJ1ARIoxAoGAOscG\nFNj1BRhFOWnmkJi4puCZ6mTaQt35psjKmV3hher3hIsH2ohD6Ne2RzUjeKlUbyq3\nQyiWBPdMdlzIwPMKtjXtihARPJcYyKasezMX5Gw916YFxr5fHay+shiOZpccQ5aw\nSPU8ONtWot8Tg2AbMvyU2Tz9Eq8ISlArh0fZXRkCgYEAqjuExxX7tl8M30qNbH+X\nmJ6Fjjt5h2ysipCLmldqnY2xW2KRR1LM19dCVJEGKCbEacInsh9+ugZMbragRU7C\nYYAoeVsKOATmpa1riOYPNeyTQTni0cVTukYXkYl9y5XHytBh6X+34mtAIt5rNERx\nZpa4oY/j18V6RX7yQ9lzMdI=\n-----END PRIVATE KEY-----\n",
    "client_email": "configbot@hemdem.iam.gserviceaccount.com",
    "client_id": "111010915854395320725",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/configbot%40hemdem.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

with open(SERVICE_ACCOUNT_FILE, 'w') as f:
    json.dump(SERVICE_ACCOUNT_DATA, f)

class ConfigBot:
    def __init__(self):
        self.drive_service = None
        self.files = []
        self.load_files()
    
    def load_files(self):
        try:
            if os.path.exists(DATABASE_FILE):
                with open(DATABASE_FILE, 'r') as f:
                    self.files = json.load(f)
        except:
            self.files = []
    
    def save_files(self):
        try:
            with open(DATABASE_FILE, 'w') as f:
                json.dump(self.files, f)
        except:
            pass
    
    def init_drive(self):
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            self.drive_service = build('drive', 'v3', credentials=creds)
            print("✅ Drive hazir!")
            return True
        except Exception as e:
            print(f"❌ Drive hatasi: {e}")
            return False
    
    def upload(self, content, file_name=None):
        try:
            if not file_name:
                file_name = f"config_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            for f in self.files:
                if f.get('name') == file_name:
                    return self.update(f['id'], content)
            
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')),
                mimetype='text/plain',
                resumable=False
            )
            
            file = self.drive_service.files().create(
                body={'name': file_name},
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            
            self.drive_service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            
            link = f"https://www.googleapis.com/drive/v3/files/{file_id}?key={API_KEY}&alt=media"
            
            self.files.append({
                'id': file_id,
                'name': file_name,
                'link': link,
                'date': datetime.datetime.now().isoformat()
            })
            self.save_files()
            
            return {'success': True, 'link': link, 'name': file_name}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update(self, file_id, content):
        try:
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')),
                mimetype='text/plain',
                resumable=False
            )
            
            self.drive_service.files().update(
                fileId=file_id,
                media_body=media,
                fields='id,name'
            ).execute()
            
            link = f"https://www.googleapis.com/drive/v3/files/{file_id}?key={API_KEY}&alt=media"
            return {'success': True, 'link': link, 'updated': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete(self, file_id):
        try:
            self.drive_service.files().delete(fileId=file_id).execute()
            self.files = [f for f in self.files if f.get('id') != file_id]
            self.save_files()
            return True
        except:
            return False
    
    def get_files(self):
        return self.files

bot = ConfigBot()

def is_admin(user_id):
    return user_id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Yetkisiz!")
        return
    
    text = """
👋 **Config Manager Bot**

/upload - Yeni config yükle
/files - Dosyalari listele
/delete - Dosya sil

Direkt config göndererek de yükleyebilirsin!
    """
    
    keyboard = [[InlineKeyboardButton("📤 Upload", callback_data='upload')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def upload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    await update.message.reply_text("📤 Dosya adi yaz (örn: vless.txt):")
    return WAITING_FOR_FILENAME

async def handle_filename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_name = update.message.text.strip()
    context.user_data['file_name'] = file_name
    await update.message.reply_text(f"✅ Dosya adi: {file_name}\n\nSimdi config metnini gönder:")
    return WAITING_FOR_CONFIG

async def handle_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    content = update.message.text
    file_name = context.user_data.get('file_name')
    
    msg = await update.message.reply_text("⏳ Yükleniyor...")
    result = bot.upload(content, file_name)
    
    if result.get('success'):
        if result.get('updated'):
            text = f"✅ **Güncellendi!**\n\n🔗 `{result['link']}`"
        else:
            text = f"✅ **Yüklendi!**\n\n📄 {result['name']}\n🔗 `{result['link']}`"
        
        keyboard = [[InlineKeyboardButton("🔗 Linki Aç", url=result['link'])]]
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await msg.edit_text(f"❌ Hata: {result.get('error')}")
    
    context.user_data.clear()
    return ConversationHandler.END

async def files_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    files = bot.get_files()
    
    if not files:
        await update.message.reply_text("📁 Dosya yok!")
        return ConversationHandler.END
    
    text = "📁 **Dosyalar:**\n\n"
    keyboard = []
    
    for i, f in enumerate(files, 1):
        text += f"{i}. {f['name']}\n"
        keyboard.append([
            InlineKeyboardButton(f"🗑 {f['name'][:20]}", callback_data=f"del_{f['id']}")
        ])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    files = bot.get_files()
    
    if not files:
        await update.message.reply_text("📁 Dosya yok!")
        return ConversationHandler.END
    
    text = "🗑 **Silinecek dosya:**\n\n"
    keyboard = []
    
    for f in files:
        text += f"• {f['name']}\n"
        keyboard.append([InlineKeyboardButton(f"🗑 {f['name']}", callback_data=f"del_{f['id']}")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if not is_admin(query.from_user.id):
        return ConversationHandler.END
    
    if data == 'upload':
        await query.message.reply_text("📤 Dosya adi yaz:")
        return WAITING_FOR_FILENAME
    
    elif data.startswith('del_'):
        file_id = data.replace('del_', '')
        if bot.delete(file_id):
            await query.message.reply_text("✅ Silindi!")
        else:
            await query.message.reply_text("❌ Hata!")
        return ConversationHandler.END
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("✅ Iptal edildi.")
    return ConversationHandler.END

def main():
    if not bot.init_drive():
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('upload', upload_cmd),
            CommandHandler('delete', delete_cmd),
            CallbackQueryHandler(button_handler)
        ],
        states={
            WAITING_FOR_FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_filename)],
            WAITING_FOR_CONFIG: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_config)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('files', files_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_config))
    
    print("🤖 Bot calisiyor...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
