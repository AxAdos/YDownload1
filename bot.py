from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp
import os
import uuid  # لإنشاء أسماء ملفات فريدة

TOKEN = "7344680185:AAEs0-LuI__6rQkVnKHLMGwEMOBfL2g5uuo"  # ← استبدل هذا بالمفتاح الحقيقي

# دالة لاستخراج الجودات المتاحة
def get_available_formats(url):
    ydl = yt_dlp.YoutubeDL()
    info = ydl.extract_info(url, download=False)
    formats = info.get('formats', [])
    
    # تصفية الجودات المتاحة (فيديو + صوت)
    available_formats = []
    for f in formats:
        if f.get('vcodec') != 'none' and f.get('acodec') != 'none':  # فيديو مع صوت
            format_id = f.get('format_id')
            resolution = f.get('resolution', 'unknown')
            ext = f.get('ext', 'unknown')
            available_formats.append({
                'format_id': format_id,
                'resolution': resolution,
                'ext': ext,
            })
    
    return available_formats

# دالة لبدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('مرحبا! أرسل رابط فيديو من يوتيوب أو فيسبوك وسأحمله لك.')

# دالة لمعالجة الرابط
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    try:
        # استخراج الجودات المتاحة
        formats = get_available_formats(url)
        if not formats:
            await update.message.reply_text("لم أتمكن من العثور على جودات متاحة.")
            return
        
        # إنشاء قائمة أزرار للجودات
        keyboard = []
        for f in formats:
            button_text = f"{f['resolution']} ({f['ext']})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f['format_id'])])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # إرسال القائمة للمستخدم
        await update.message.reply_text("اختر جودة الفيديو:", reply_markup=reply_markup)
        
        # حفظ الرابط في الذاكرة
        context.user_data['url'] = url
    
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ: {e}")

# دالة لمعالجة اختيار الجودة
async def handle_quality_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    format_id = query.data
    url = context.user_data.get('url')
    
    if not url:
        await query.edit_message_text("حدث خطأ: الرابط غير موجود.")
        return
    
    try:
        # إنشاء اسم ملف فريد
        unique_id = str(uuid.uuid4())  # إنشاء معرف عشوائي
        filename = f"downloaded_video_{unique_id}.mp4"

        # خيارات التحميل بناءً على الجودة المختارة
        ydl_opts = {
            'format': format_id,
            'outtmpl': filename,  # استخدام اسم الملف الفريد
        }

        # التحميل
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_filename = ydl.prepare_filename(info)

        # إرسال الفيديو مع زيادة وقت الانتظار
        await context.bot.send_video(
            chat_id=query.message.chat_id,
            video=open(final_filename, 'rb'),
            read_timeout=120,  # زيادة وقت القراءة إلى 120 ثانية
            write_timeout=120,  # زيادة وقت الكتابة إلى 120 ثانية
            connect_timeout=120,  # زيادة وقت الاتصال إلى 120 ثانية
            pool_timeout=120,  # زيادة وقت الانتظار إلى 120 ثانية
        )
        await query.edit_message_text("تم إرسال الفيديو بنجاح!")
        
        # حذف الفيديو بعد الإرسال
        os.remove(final_filename)
    
    except Exception as e:
        await query.edit_message_text(f"حدث خطأ: {e}")

# دالة رئيسية لتشغيل البوت
def main():
    application = Application.builder().token(TOKEN).build()

    # إضافة handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(handle_quality_choice))

    # بدء البوت
    application.run_polling()

if __name__ == '__main__':
    main()