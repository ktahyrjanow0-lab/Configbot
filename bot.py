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
SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
WAITING_FOR_FILENAME, WAITING_FOR_CONFIG = range(2)

# Base64 encoded JSON
B64_JSON = "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogImhlbWRlbSIsICJwcml2YXRlX2tleV9pZCI6ICJlZjVjNDI1MmQ4OTYwNTdkOGYzZGJmNDhlZTYyZWQyMzRmNGNjOGE0IiwgInByaXZhdGVfa2V5IjogIi0tLS0tQkVHSU4gUFJJVkFURSBLRVktLS0tLVxuTUlJRXZRSUJBREFOQmdrcWhraUc5dzBCQVFFQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUUM5bDN2dTIyOWU2QzhrXG40UjVpZE81WkZiN2YrWU1DK1FxWlE1b0JnMElaUXAwYzBoenUvYVdvK2lUREt1dUtIaWRQRDBpaVA3TlBsOFNMXG54Mjh4Uk82eitHeG90MWQ1SnREUWJkMzFCaWU3YWhtejUwdXdyMTNMbFlPVUNjME1xdXBQbEtLQzlXek5mcmF5XG5idjFHbjNENHZzbjdra1hvMjlhVmI3WVpESlFJRldWNlg2ZGxKS1pLRE1MMVNPT0g5bDhSYzNDSlFPbWE3eXhUXG5VR0pPWm9Fd0h6cDBRTUZWdVdOZmVqMDdVVmIvZnZKS3NiQU1VeElKemZtR3pIT2xLd0V3a3JOcjBCa1JWTTMzXG5pVDBjbFgzY1EreWdNOWdnZUtwbXYremJtbm9kbG02blNXU2pTQVg3cWpDZmtEWll0dUdOSjUzMzRSWUJCamVEXG5aUjVkdFUzTkFnTUJBQUVDZ2dFQUxSbExRRXJQaDhaNGJHL21mK29yeG1JdldPenI5cm1TQlZvNDJMSkY5MmRLXG5vMC94MVFIZU5iOW5Ia3ZuNHArQW4wUlY5VTVzMDNxWkpOem9mTkpXYTlZa3g1WVJSejd0L2g2Y1pVdzFDRlpaXG5UZHV2dkJSREhnbnZWamdzb0I1S0JXc29hem1CUzdLZ04vckI0ZHBNajhjbW1lSzU3OTNYZ2cya1Jmb2hmbmhiXG5ZdTJaSW1QN0VvZjZtY2tKcktBSHVCaGYyY1dnMVZJM0RIK3BDK01zWG51RjVSSDk5UFpObW1XTmhCZzVGSlg2XG5qdlpkUHV0MHZBVkMyUUg0U0JNZ3Q1eml5dGdYV3diODJJdlB3Z2laZjZTYWw2Q1JOQUdqVjBRclJveFlRMTJoXG5ra1VYYUl1US93eVFoS0RFREhKSTZLQUIrMlBPM0laY21TVW0vVXRZTVFLQmdRRHRoSnpUc3NuZzVpWGVSbm0vXG5MbHoyaEthemFBRnhVdGh2cStRNUU0MXJTTlpsbjRIMHFUczRJNStHMnpkbVYvR2ZPTEhxV1dBZHM0dWtzdmV0XG50TllLN0xPcTFIN3M0VnhaZVZSTUhwbHRMRW9nSFMrQ094NDNMR2UxMEl4WnRQWUtSMStBVkhEWFkvaHNsWDhNXG51WnJ5VDNibnZGNCs2WlNXZE5RYjJic1lwUUtCZ1FETVdDeVlkeGl0QjI3RTdZdFRhZEgxTGhhY1psbGhoY0ljXG5vZzY1R3JscnVUUnhGV0ZwT2ovSTZuSFFRdHlCRG1JU3ZEM0RIRWQ2R3JEUmRTejZFL0NoSU1UWnBhNHhzYzNceERWUVp3aTV1WERqKzNUWE9JRldtVk5GZ2J6NzJmVytMUnlVM0FQVXMwNUs1NFVvNlhOOHRDMzY1RUtKMXh3V1xucUhKSWlYQ3dDUUtCZ0NUT3BDNzZTZWFjUThvS1NkdWlwNjFjS1Nrc09PMEMxWitZbDZsd3FqMng3K2VYckYvcFxueWMrTlZhOWtVVlYrMDJiRk5tMEdwS3AxcEhKRmViUmxqYlhyc0h3TXFnNnpiY2cvMFJ4cXNZUUZsUWNjL3J2RFxueFk3dlJyTWFPbVc4Y1ZSdWN4SkVBNmlkU1dZcVZLSDRNVmJUa2EyZnQwc3dqMkl4Z0oxQVJJb3hBb0dBT3NjR1xuRk5qMUJSaEZPV25ta0ppNHB1Q1o2bVRhUXQzNXBzakt tVjNoaGVyM2hJc0gyb2hENk5lMlJ6VWplS2xVYnlxM1xuUXlpV0JQZE1kbHpJd1BNS3RqWHRpaEFSUEpjWXlLYXNlek1YNUd3OTE2WUZ4cjVmSGF5K3NoaU9acGNRUTVhd1xuU1BVOE9OdFdvdDhUZzJBYk12eVUyVHo5RXE4SVNsQXJoMGZaWFJrQ2dZRUFxanVFeHhYN3RsOE0zMHFOYkgrWFxubUo2RmpqdDVoMnlzaXBDTG1sZHFuWTJ4VzJLUlIxTE0xOWRDVkpFR0tDYkVhY0luc2g5K3VnWk1icmFnUlU3Q1xuWVlBb2VWc0tPQVRtcGExcmlPWVB OZXlUUVRuaTBjVlR1a1lYa1lsOXk1WEh5dEJoNlgrMzRtdEFJdDVyTkVSeFxuWnBhNG9ZL2oxOFY2Ulg3eVE5bHpNZEk9XG4tLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tXG4iLCAiY2xpZW50X2VtYWlsIjogImNvbmZpZ2JvdEBoZW1kZW0uaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAiY2xpZW50X2lkIjogIjExMTAxMDkxNTg1NDM5NTMyMDcyNSIsICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsICJ0b2tlbl91cmkiOiAiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4iLCAiYXV0aF9wcm92aWRlcl94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92MS9jZXJ0cyIsICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2NvbmZpZ2JvdCU0MGhlbWRlbS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsICJ1bml2ZXJzZV9kb21haW4iOiAiZ29vZ2xlYXBpcy5jb20ifQ=="

# JSON'u oluştur
SERVICE_ACCOUNT_JSON = base64.b64decode(B64_JSON).decode('utf-8')
with open(SERVICE_ACCOUNT_FILE, 'w') as f:
    f.write(SERVICE_ACCOUNT_JSON)

print("✅ JSON olusturuldu")

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
