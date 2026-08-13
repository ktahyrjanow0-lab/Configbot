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

# JSON'u environment variable'dan oku
SERVICE_ACCOUNT_JSON = os.environ.get('SERVICE_ACCOUNT_JSON', '')

# JSON dosyasını oluştur
if SERVICE_ACCOUNT_JSON:
    with open('service_account.json', 'w') as f:
        f.write(SERVICE_ACCOUNT_JSON)
    print("✅ JSON dosyasi olusturuldu!")
else:
    print("❌ SERVICE_ACCOUNT_JSON environment variable bulunamadi!")

SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
WAITING_FOR_FILENAME, WAITING_FOR_CONFIG = range(2)

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