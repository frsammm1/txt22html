import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

from parser import parse_txt_content
from html_generator import generate_html
from config import THEMES

# Conversation states
TXT_FILE, BATCH_NAME, CREDIT_NAME, THEME_SELECT, CONFIRM = range(5)

# Store user data
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with welcome message"""
    keyboard = [[InlineKeyboardButton("🚀 Create HTML", callback_data='create')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome = (
        "🎨 *Ultra Modern HTML Generator*\n\n"
        "✨ *Features:*\n"
        "• 6 Stunning Themes\n"
        "• 🔍 Smart Search\n"
        "• 📊 Advanced Filters\n"
        "• 🎬 Video Player with Controls\n"
        "• 📱 100% Responsive\n"
        "• ⚡ Lightning Fast\n"
        "• 🎯 Handles 1000+ Links\n\n"
        "Ready to create something beautiful? 👇"
    )
    
    await update.message.reply_text(welcome, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'create':
        msg = (
            "📄 *Step 1: Send TXT File*\n\n"
            "✅ Supported formats:\n"
            "• [Category] Title: URL\n"
            "• Title: URL\n"
            "• Any text with links\n\n"
            "Send your file now! 📤"
        )
        await query.message.reply_text(msg, parse_mode='Markdown')
        return TXT_FILE
    
    elif query.data.startswith('theme_'):
        return await select_theme(query, context)
    
    elif query.data == 'convert':
        return await process_conversion(query, context)

async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and parse TXT file"""
    user_id = update.effective_user.id
    
    await update.message.reply_text("⚡ *Parsing file...*", parse_mode='Markdown')
    
    try:
        file = await update.message.document.get_file()
        content = await file.download_as_bytearray()
        txt_content = content.decode('utf-8')
        
        categories = parse_txt_content(txt_content)
        
        if not categories:
            await update.message.reply_text("❌ No valid links found! Try again.")
            return TXT_FILE
        
        user_sessions[user_id] = {
            'content': txt_content,
            'categories': categories
        }
        
        total = sum(len(items) for items in categories.values())
        videos = sum(1 for cat in categories.values() for item in cat if item['type'] == 'VIDEO')
        pdfs = sum(1 for cat in categories.values() for item in cat if item['type'] == 'PDF')
        
        preview = (
            f"✅ *Parsed Successfully!*\n\n"
            f"📦 Categories: {len(categories)}\n"
            f"📊 Total Items: {total}\n"
            f"🎬 Videos: {videos}\n"
            f"📄 PDFs: {pdfs}\n\n"
            f"📝 *Step 2: Batch Name*\n\n"
            f"Enter a name for this batch:"
        )
        
        await update.message.reply_text(preview, parse_mode='Markdown')
        return BATCH_NAME
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        return TXT_FILE

async def receive_batch_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive batch name"""
    user_id = update.effective_user.id
    batch_name = update.message.text.strip()
    
    if user_id not in user_sessions:
        await update.message.reply_text("❌ Session expired! /start to restart.")
        return ConversationHandler.END
    
    user_sessions[user_id]['batch_name'] = batch_name
    
    await update.message.reply_text(
        f"✅ *Batch:* {batch_name}\n\n"
        f"👨‍💻 *Step 3: Credit Name*\n\n"
        f"Enter your name/username:",
        parse_mode='Markdown'
    )
    return CREDIT_NAME

async def receive_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive credit name and show theme selection"""
    user_id = update.effective_user.id
    credit_name = update.message.text.strip()
    
    if user_id not in user_sessions:
        await update.message.reply_text("❌ Session expired! /start to restart.")
        return ConversationHandler.END
    
    user_sessions[user_id]['credit_name'] = credit_name
    
    # Theme selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("🌙 Dark", callback_data='theme_dark'),
            InlineKeyboardButton("☀️ Light", callback_data='theme_light')
        ],
        [
            InlineKeyboardButton("🌊 Ocean", callback_data='theme_ocean'),
            InlineKeyboardButton("🌅 Sunset", callback_data='theme_sunset')
        ],
        [
            InlineKeyboardButton("🌲 Forest", callback_data='theme_forest'),
            InlineKeyboardButton("🎮 Cyber", callback_data='theme_cyber')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ *Credit:* {credit_name}\n\n"
        f"🎨 *Step 4: Choose Theme*\n\n"
        f"Pick your favorite design:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return THEME_SELECT

async def select_theme(query, context):
    """Handle theme selection"""
    user_id = query.from_user.id
    theme = query.data.replace('theme_', '')
    
    if user_id not in user_sessions:
        await query.message.reply_text("❌ Session expired! /start to restart.")
        return ConversationHandler.END
    
    user_sessions[user_id]['theme'] = theme
    data = user_sessions[user_id]
    
    total = sum(len(items) for items in data['categories'].values())
    
    summary = (
        f"✅ *Ready to Generate!*\n\n"
        f"📚 Batch: {data['batch_name']}\n"
        f"👨‍💻 Credit: {data['credit_name']}\n"
        f"🎨 Theme: {THEMES[theme]['name']}\n"
        f"📦 Categories: {len(data['categories'])}\n"
        f"📊 Total Items: {total}\n\n"
        f"Click Generate! 👇"
    )
    
    keyboard = [[InlineKeyboardButton("✨ Generate HTML", callback_data='convert')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(summary, reply_markup=reply_markup, parse_mode='Markdown')
    return CONFIRM

async def process_conversion(query, context):
    """Generate HTML file"""
    user_id = query.from_user.id
    
    if user_id not in user_sessions:
        await query.message.reply_text("❌ Session expired! /start to restart.")
        return ConversationHandler.END
    
    await query.answer()
    msg = await query.message.reply_text("🎨 *Creating your beautiful HTML...*", parse_mode='Markdown')
    
    try:
        data = user_sessions[user_id]
        
        html_content = generate_html(
            data['categories'],
            data['batch_name'],
            data['credit_name'],
            data['theme']
        )
        
        filename = f"{data['batch_name'].replace(' ', '_')}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        await msg.edit_text("✅ *HTML Generated!* 📤", parse_mode='Markdown')
        
        total = sum(len(items) for items in data['categories'].values())
        caption = (
            f"✨ *Your HTML is Ready!*\n\n"
            f"📚 Batch: {data['batch_name']}\n"
            f"🎨 Theme: {THEMES[data['theme']]['name']}\n"
            f"📊 Items: {total}\n\n"
            f"🎯 Features:\n"
            f"• Smart Search 🔍\n"
            f"• Category Filters\n"
            f"• Video Player\n"
            f"• Fully Responsive\n\n"
            f"Enjoy! 🎉"
        )
        
        with open(filename, 'rb') as f:
            await query.message.reply_document(
                document=f,
                filename=filename,
                caption=caption,
                parse_mode='Markdown'
            )
        
        os.remove(filename)
        del user_sessions[user_id]
        
        await query.message.reply_text(
            "🎉 *Done!*\n\nUse /start for another file!",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")
        print(f"Error: {e}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel handler"""
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await update.message.reply_text("❌ Cancelled! Use /start to restart.")
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler"""
    print(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Error! Use /start to retry.")

def main():
    """Main function"""
    TOKEN = os.getenv('BOT_TOKEN')
    
    if not TOKEN:
        print("❌ BOT_TOKEN not found!")
        return
    
    print("🚀 Starting Modern HTML Bot...")
    
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(button_handler, pattern='^create$')
        ],
        states={
            TXT_FILE: [MessageHandler(filters.Document.ALL, receive_file)],
            BATCH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_batch_name)],
            CREDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_credit)],
            THEME_SELECT: [CallbackQueryHandler(button_handler, pattern='^theme_')],
            CONFIRM: [CallbackQueryHandler(button_handler, pattern='^convert$')],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)
    
    print("✅ Bot is live!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
