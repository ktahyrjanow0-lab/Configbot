import os
import logging
import datetime
import io
import json
import base64
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

# JSON'u base64 olarak göm
SERVICE_ACCOUNT_B64 = "ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAiaGVtZGVtIiwKICAicHJpdmF0ZV9rZXlfaWQiOiAiZjMwMDZjOTg2MDdhYjExNDFhMzM2ODM4YzMzYjAyM2M2ODZjYmI0NCIsCiAgInByaXZhdGVfa2V5IjogIi0tLS0tQkVHSU4gUFJJVkFURSBLRVktLS0tLVxuTUlJRXZRSUJBREFOQmdrcWhraUc5dzBCQVFFQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUUN6MXBWNnJqWGpNMFdHXG5MdVNnNGlCODE1Ky9senJlUHMzT1dSQTZwWm53cWNzejZaYThPUW00K3FBSkRKWkJRKzNWY0E2TW5PcnhRM245XG5OOGdXc1lkaTRlRWs0N2lsVHBWdjJ2dEZkaDE0SG9iLzRuMFJhVXJ6Y2JRc0IySEpHSk9uRDNUbVV1b2lNbEVRXG5nbExQenBkNEpIS1RoUDVOY3hvcmVsalUxK2NiVWFRdlhqNEt2cEdoaEVPZ2p4T1VzOWtwd1dlbGtOQU1ObUMwXG5LZ1V1RW9oU0dNNkV0MlpFRFQxVjV6YlhPZ2RiNWtUQVhmNHF1UGhFT3Zza054VDcyQ1EycXFoMWpQb2Y3b3NFXG4vaGI1Szk0cWZ3ZHdxejdaU04vMGJpUXpSUWhscGhPMm41VzBpT1Q3ZURQT0c5bld3NDhFZGo5U2g5d0NENEZQXG5RMTk2MmtnUEFnTUJBQUVDZ2dFQURlODBpZHJ4eGZiMURoNllESGM0K1ROcUhTNVZQc2N5ejVQYVp2blA2U0lZXG5DOWJSSjVPMnZ1UjhmZmpXVTF4R0UyR3BYdS9Sckh3RCtjRFd1aHRyV0JnVWI5MU5NMUhSZG1kTERPaUlCQVNwXG5oUzR4YnFYdjdza0NvdDYzanZOZWpYVS9JNUdOSHJVelhzb2FUSXUvWk1tK0x2d0JFRk00MWVHVy9IYjJLMBdZXG53ZjJkQ3A3d1JkdVRmcGVUVjU5bzlnTDlIeTJEVjUwbnZGSGZoaGY4T2NSM0JObjVKNHpxaklsS1A0MkF0L1ZjXG5qNTNoR1RMMmRickZHdmQvS01tcHkrSEpUQnR4ZTJnMld5MkhGYkFJT3hZNzl3M245UnBmbko3azR4Ym5jV0NDXG5OYlR0R1JxdXRRVXE2VEZjWTEyNXhCNTVWR3NOa3c1OHQxVUp3QUV1d1FLQmdRRHRPalNwdzZ6ZU8vWUJBcmttXG4zVmM3Q1UzdFl2c2Q5WmtiN1diakI5aUVWSXBmTzNwdlpTQjhLMFBLaWttcUdOZXBXYWM0anRmVFhEMEhlSFBwXG5jcEVXT1I3b25kNncvOFFyTUx0YUZwUXdnR0lBMWMvR2JsL1ZocGgyOUROandRbHJHcnRKVVBYQUxDS3VTNUtceG15eUhXbi9ZWEtvYWJDQjcyMFpHNml3OFFLQmdRRENFY2RTVXl0ZDJ3MFNBMmc2Wkw4WXFTelhbnJ6UkVPUVxudWNaMzlIRmFnemZpcXJBYnpDcmI2ZENOMVY3YmJINHlTa0l1QXV2ektkNVowRGc4ajhremhXR0xVU1BlNlc2TFxubm16RS9haWZGc2dUaS9EL0VsNFFvVlR5QXVLN1VLQWJPTTVoRWxzbEwxRXhMaDc4T1JGV0FQTEVyNkJ4c3Z5QVxuUFpGMHpQS0kvd0tCZ0hiUWlEL2V1VjQxT2VrWHJCUkRGOHdCOTMzeDdVUDhGa3RlaEFHQmxIZnl2N3NpMXhlalxuMXJsYUVnSUhjUTI0azR0R1UvS0gyS0VMdWFWZEIwd05EWTNMM2ljenFxMkw3SHlWVThDenBsVnNkNmxqYlVVOVxuVXRKbkwwV2syWGhFM3FybkNrYnNPeVljT2svQW4rYmpxdDBxemtRU1VwTDNIR2gzdW5TdzNiU0JBb0dCQUtzUlxuMU92aTJIVnhaSUllY3NBV2tzVUFTOERQNGZXU2xTUjhQbEQ3THZpa2RwemQ3VU56bzh3YXZYWnBRYWFXYWwrV1xuU2VRWk96Z3NEZzZKbHlqN2J6Z2ZPUzcvcFdrWHlCUlc0SFo5U3lpQmduaUlnVFczVVNmRHJ3ZHVOOEw2ZlVmQlxudVZxa1BhZjNuOUNFWVZmZ1RrSExzRFJreEQrMWtSTFNNdWdNeVRhdEFvR0FjUlFqQTA3bFBkVXAzUWwvL2tHRFxueXBpQ2pXQVdDRjIzNXVAa0JhOEpMQm9LNDF6eWEwNUx4YVRITkVsYWZaUjRkb3dkdFVncFRXOVRzZGJMcmdmaVxuc1lvei92YlNHbmZYMXNySG0yTStvYnZ5NzZRZE9sbkhaWWJCUTYvQWdNMkU5RktzNFI5QlZUekF1bVc0RFRUWlxuTGRIVWR6ZlJoajA3SWxKVmZNQ3ltRzg9XG4tLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tXG4iLAogICJjbGllbnRfZW1haWwiOiAiYm90Y29uZmlnQGhlbWRlbS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgImNsaWVudF9pZCI6ICIxMTEwNTM0MjYyNDA1OTk4NDQ5NTEiLAogICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsCiAgInRva2VuX3VyaSI6ICJodHRwczovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsCiAgImF1dGhfcHJvdmlkZXJfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLAogICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2JvdGNvbmZpZyU0MGhlbWRlbS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgInVuaXZlcnNlX2RvbWFpbiI6ICJnb29nbGVhcGlzLmNvbSIKfQ=="

# Base64'ten çöz ve JSON dosyasını oluştur
service_account_json = base64.b64decode(SERVICE_ACCOUNT_B64)
with open('service_account.json', 'wb') as f:
    f.write(service_account_json)

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