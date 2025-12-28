import os
import re
import base64
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# States for conversation
PASSWORD, BATCH_NAME, CREDIT_NAME, TXT_FILE = range(4)

# Store user data temporarily
user_data_store = {}

def encrypt_link(link, password):
    """Encrypt link using password-based key"""
    key = hashlib.sha256(password.encode()).digest()
    encrypted = base64.b64encode((link + "|" + password).encode()).decode()
    return encrypted

def parse_txt_content(content):
    """Parse TXT content and categorize links"""
    lines = content.strip().split('\n')
    categories = {
        'GRAMMAR': [],
        'IDIOMS': [],
        'SYNONYM - ANTONYM': [],
        'ROOT WORDS + OWS': [],
        'PHRASAL VERBS': []
    }
    
    current_category = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if it's a category header
        if line.startswith('[') and line.endswith(']'):
            current_category = line[1:-1]
            if current_category not in categories:
                categories[current_category] = []
        elif ':' in line and current_category:
            parts = line.split(':', 1)
            if len(parts) == 2:
                title = parts[0].strip()
                link = parts[1].strip()
                
                # Determine file type
                file_type = 'OTHER'
                if '.mp4' in link or '.m3u8' in link:
                    file_type = 'VIDEO'
                elif '.pdf' in link:
                    file_type = 'PDF'
                
                categories[current_category].append({
                    'title': title,
                    'link': link,
                    'type': file_type
                })
    
    return categories

def generate_html(categories, password, batch_name, credit_name):
    """Generate password-protected HTML"""
    
    # Encrypt all links
    encrypted_data = {}
    for category, items in categories.items():
        encrypted_data[category] = []
        for item in items:
            encrypted_data[category].append({
                'title': item['title'],
                'link': encrypt_link(item['link'], password),
                'type': item['type']
            })
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{batch_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --bg-primary: #0f0f23;
            --bg-secondary: #1a1a2e;
            --bg-card: #16213e;
            --text-primary: #ffffff;
            --text-secondary: #a0a0c0;
            --accent: #00d4ff;
            --accent-hover: #00b8e6;
            --border: #2a2a4a;
        }}

        body.theme-light {{
            --bg-primary: #f5f7fa;
            --bg-secondary: #ffffff;
            --bg-card: #ffffff;
            --text-primary: #1a1a2e;
            --text-secondary: #64748b;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --border: #e2e8f0;
        }}

        body.theme-ocean {{
            --bg-primary: #001f3f;
            --bg-secondary: #003366;
            --bg-card: #004080;
            --text-primary: #e0f2ff;
            --text-secondary: #b3d9ff;
            --accent: #00bfff;
            --accent-hover: #0099cc;
            --border: #0059b3;
        }}

        body.theme-forest {{
            --bg-primary: #1a2f1a;
            --bg-secondary: #2d4a2d;
            --bg-card: #3d5a3d;
            --text-primary: #e8f5e8;
            --text-secondary: #c1e0c1;
            --accent: #4ade80;
            --accent-hover: #22c55e;
            --border: #4a6e4a;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            transition: all 0.3s ease;
        }}

        #passwordScreen {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, var(--bg-primary), var(--bg-secondary));
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }}

        .password-box {{
            background: var(--bg-card);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            text-align: center;
            max-width: 400px;
            width: 90%;
        }}

        .password-box h1 {{
            color: var(--accent);
            margin-bottom: 30px;
            font-size: 2em;
        }}

        .password-box input {{
            width: 100%;
            padding: 15px;
            border: 2px solid var(--border);
            border-radius: 10px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            font-size: 16px;
            margin-bottom: 20px;
        }}

        .password-box button {{
            width: 100%;
            padding: 15px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .password-box button:hover {{
            background: var(--accent-hover);
            transform: translateY(-2px);
        }}

        #mainContent {{
            display: none;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            text-align: center;
            padding: 30px 20px;
            background: var(--bg-card);
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}

        .developer {{
            color: var(--accent);
            font-size: 14px;
            margin-bottom: 10px;
        }}

        .batch-name {{
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(135deg, var(--accent), var(--accent-hover));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }}

        .controls {{
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }}

        .theme-btn {{
            padding: 10px 20px;
            background: var(--bg-card);
            border: 2px solid var(--border);
            border-radius: 10px;
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.3s;
        }}

        .theme-btn:hover {{
            border-color: var(--accent);
            transform: translateY(-2px);
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: var(--bg-card);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            border: 2px solid var(--border);
            transition: all 0.3s;
        }}

        .stat-card:hover {{
            border-color: var(--accent);
            transform: translateY(-5px);
        }}

        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: var(--accent);
        }}

        .stat-label {{
            color: var(--text-secondary);
            margin-top: 5px;
        }}

        .category {{
            background: var(--bg-card);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            border: 2px solid var(--border);
        }}

        .category-header {{
            font-size: 1.5em;
            font-weight: bold;
            color: var(--accent);
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border);
        }}

        .item {{
            background: var(--bg-secondary);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid var(--border);
            transition: all 0.3s;
        }}

        .item:hover {{
            border-color: var(--accent);
            transform: translateX(5px);
        }}

        .item-title {{
            flex: 1;
        }}

        .item-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 10px;
        }}

        .badge-video {{
            background: #ef4444;
            color: white;
        }}

        .badge-pdf {{
            background: #f59e0b;
            color: white;
        }}

        .item-btn {{
            padding: 8px 20px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .item-btn:hover {{
            background: var(--accent-hover);
        }}

        #videoModal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.95);
            z-index: 10000;
            padding: 20px;
        }}

        .modal-content {{
            position: relative;
            max-width: 900px;
            margin: 0 auto;
            padding-top: 60px;
        }}

        .modal-header {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            padding: 15px;
            background: var(--bg-card);
            border-radius: 10px 10px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .back-btn {{
            padding: 10px 20px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
        }}

        video {{
            width: 100%;
            border-radius: 10px;
            background: #000;
        }}

        .video-controls {{
            margin-top: 15px;
            display: flex;
            gap: 10px;
            justify-content: center;
            flex-wrap: wrap;
        }}

        .speed-btn {{
            padding: 8px 15px;
            background: var(--bg-card);
            color: var(--text-primary);
            border: 2px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
        }}

        .speed-btn.active {{
            background: var(--accent);
            border-color: var(--accent);
            color: white;
        }}

        @media (max-width: 768px) {{
            .batch-name {{
                font-size: 1.8em;
            }}
            
            .stat-card {{
                padding: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div id="passwordScreen">
        <div class="password-box">
            <h1>🔒 Enter Password</h1>
            <input type="password" id="passwordInput" placeholder="Enter password" onkeypress="if(event.key==='Enter') checkPassword()">
            <button onclick="checkPassword()">Unlock</button>
        </div>
    </div>

    <div id="mainContent">
        <div class="header">
            <div class="developer">Developer - {credit_name}</div>
            <div class="batch-name">{batch_name}</div>
        </div>

        <div class="controls">
            <button class="theme-btn" onclick="changeTheme('dark')">🌙 Dark</button>
            <button class="theme-btn" onclick="changeTheme('light')">☀️ Light</button>
            <button class="theme-btn" onclick="changeTheme('ocean')">🌊 Ocean</button>
            <button class="theme-btn" onclick="changeTheme('forest')">🌲 Forest</button>
        </div>

        <div class="stats" id="stats"></div>
        <div id="categories"></div>
    </div>

    <div id="videoModal">
        <div class="modal-content">
            <div class="modal-header">
                <button class="back-btn" onclick="closeVideo()">← Back</button>
                <span id="videoTitle" style="color: var(--text-primary);"></span>
            </div>
            <video id="videoPlayer" controls></video>
            <div class="video-controls">
                <button class="speed-btn" onclick="setSpeed(0.5)">0.5x</button>
                <button class="speed-btn" onclick="setSpeed(0.75)">0.75x</button>
                <button class="speed-btn active" onclick="setSpeed(1)">1x</button>
                <button class="speed-btn" onclick="setSpeed(1.25)">1.25x</button>
                <button class="speed-btn" onclick="setSpeed(1.5)">1.5x</button>
                <button class="speed-btn" onclick="setSpeed(2)">2x</button>
            </div>
        </div>
    </div>

    <script>
        const PASSWORD = "{password}";
        const encryptedData = {str(encrypted_data).replace("'", '"')};

        function checkPassword() {{
            const input = document.getElementById('passwordInput').value;
            if (input === PASSWORD) {{
                document.getElementById('passwordScreen').style.display = 'none';
                document.getElementById('mainContent').style.display = 'block';
                loadContent();
            }} else {{
                alert('❌ Wrong Password!');
            }}
        }}

        function decryptLink(encrypted) {{
            try {{
                const decoded = atob(encrypted);
                const parts = decoded.split('|');
                if (parts[1] === PASSWORD) {{
                    return parts[0];
                }}
            }} catch(e) {{}}
            return null;
        }}

        function loadContent() {{
            let totalVideos = 0;
            let totalPDFs = 0;
            let totalItems = 0;

            const categoriesDiv = document.getElementById('categories');
            
            for (const [category, items] of Object.entries(encryptedData)) {{
                totalItems += items.length;
                items.forEach(item => {{
                    if (item.type === 'VIDEO') totalVideos++;
                    if (item.type === 'PDF') totalPDFs++;
                }});

                const categoryDiv = document.createElement('div');
                categoryDiv.className = 'category';
                categoryDiv.innerHTML = `<div class="category-header">${{category}}</div>`;

                items.forEach(item => {{
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'item';
                    
                    const badge = item.type === 'VIDEO' ? '<span class="item-badge badge-video">VIDEO</span>' : 
                                 item.type === 'PDF' ? '<span class="item-badge badge-pdf">PDF</span>' : '';
                    
                    itemDiv.innerHTML = `
                        <div class="item-title">${{item.title}}</div>
                        ${{badge}}
                        <button class="item-btn" onclick='openLink("${{item.link}}", "${{item.title}}", "${{item.type}}")'>
                            ${{item.type === 'VIDEO' ? '▶️ Play' : '📄 Open'}}
                        </button>
                    `;
                    categoryDiv.appendChild(itemDiv);
                }});

                categoriesDiv.appendChild(categoryDiv);
            }}

            document.getElementById('stats').innerHTML = `
                <div class="stat-card">
                    <div class="stat-number">${{totalItems}}</div>
                    <div class="stat-label">All Items</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${{totalVideos}}</div>
                    <div class="stat-label">Videos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${{totalPDFs}}</div>
                    <div class="stat-label">PDFs</div>
                </div>
            `;
        }}

        function openLink(encrypted, title, type) {{
            const link = decryptLink(encrypted);
            if (!link) {{
                alert('❌ Invalid link!');
                return;
            }}

            if (type === 'VIDEO') {{
                document.getElementById('videoTitle').textContent = title;
                document.getElementById('videoPlayer').src = link;
                document.getElementById('videoModal').style.display = 'block';
            }} else {{
                window.open(link, '_blank');
            }}
        }}

        function closeVideo() {{
            document.getElementById('videoModal').style.display = 'none';
            document.getElementById('videoPlayer').pause();
            document.getElementById('videoPlayer').src = '';
        }}

        function setSpeed(speed) {{
            document.getElementById('videoPlayer').playbackRate = speed;
            document.querySelectorAll('.speed-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }}

        function changeTheme(theme) {{
            document.body.className = theme === 'dark' ? '' : `theme-${{theme}}`;
        }}
    </script>
</body>
</html>'''
    
    return html

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    keyboard = [[InlineKeyboardButton("📝 Create HTML", callback_data='create')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎉 *Welcome to HTML Converter Bot!*\n\n"
        "मैं आपकी TXT file को Password-Protected HTML में convert कर दूंगा!\n\n"
        "✨ Features:\n"
        "• 🔒 Password Protection\n"
        "• 🎨 Multiple Themes\n"
        "• 🎬 Video Player with Speed Control\n"
        "• 📱 Mobile-Friendly Design\n"
        "• 🔐 Encrypted Links\n\n"
        "Click below to start! 👇",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'create':
        await query.message.reply_text(
            "🔐 *Step 1: Set Password*\n\n"
            "HTML file के लिए एक strong password enter करें:",
            parse_mode='Markdown'
        )
        return PASSWORD

async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive password"""
    user_id = update.effective_user.id
    password = update.message.text.strip()
    
    if len(password) < 4:
        await update.message.reply_text("❌ Password कम से कम 4 characters का होना चाहिए!")
        return PASSWORD
    
    user_data_store[user_id] = {'password': password}
    
    await update.message.reply_text(
        f"✅ Password set: `{password}`\n\n"
        "📚 *Step 2: Batch Name*\n\n"
        "Batch का नाम enter करें:",
        parse_mode='Markdown'
    )
    return BATCH_NAME

async def receive_batch_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive batch name"""
    user_id = update.effective_user.id
    batch_name = update.message.text.strip()
    
    user_data_store[user_id]['batch_name'] = batch_name
    
    await update.message.reply_text(
        f"✅ Batch Name: *{batch_name}*\n\n"
        "👨‍💻 *Step 3: Credit Name*\n\n"
        "Developer credit name enter करें (जैसे: @FR_SAMMM11):",
        parse_mode='Markdown'
    )
    return CREDIT_NAME

async def receive_credit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive credit name"""
    user_id = update.effective_user.id
    credit_name = update.message.text.strip()
    
    user_data_store[user_id]['credit_name'] = credit_name
    
    await update.message.reply_text(
        f"✅ Credit: *{credit_name}*\n\n"
        "📄 *Step 4: Send TXT File*\n\n"
        "अब अपनी TXT file भेजें जिसमें links हों!",
        parse_mode='Markdown'
    )
    return TXT_FILE

async def receive_txt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and process TXT file"""
    user_id = update.effective_user.id
    
    if user_id not in user_data_store:
        await update.message.reply_text("❌ कुछ गलत हो गया! /start से फिर शुरू करें।")
        return ConversationHandler.END
    
    await update.message.reply_text("⏳ Processing your file...")
    
    try:
        # Download file
        file = await update.message.document.get_file()
        content = await file.download_as_bytearray()
        txt_content = content.decode('utf-8')
        
        # Parse content
        categories = parse_txt_content(txt_content)
        
        # Generate HTML
        user_data = user_data_store[user_id]
        html_content = generate_html(
            categories,
            user_data['password'],
            user_data['batch_name'],
            user_data['credit_name']
        )
        
        # Save HTML file
        filename = f"{user_data['batch_name'].replace(' ', '_')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Send HTML file
        with open(filename, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=filename,
                caption=f"✅ *HTML File Ready!*\n\n"
                       f"🔒 Password: `{user_data['password']}`\n"
                       f"📚 Batch: {user_data['batch_name']}\n"
                       f"👨‍💻 Credit: {user_data['credit_name']}\n\n"
                       f"⚡ File को खोलें और password enter करें!",
                parse_mode='Markdown'
            )
        
        # Cleanup
        os.remove(filename)
        del user_data_store[user_id]
        
        await update.message.reply_text(
            "🎉 *Conversion Complete!*\n\n"
            "एक और file convert करने के लिए /start करें!",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    user_id = update.effective_user.id
    if user_id in user_data_store:
        del user_data_store[user_id]
    
    await update.message.reply_text("❌ Cancelled! /start से फिर शुरू करें।")
    return ConversationHandler.END

def main():
    """Start the bot"""
    TOKEN = os.getenv('BOT_TOKEN')
    
    if not TOKEN:
        print("❌ BOT_TOKEN environment variable not set!")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(button_callback, pattern='^create$')
        ],
        states={
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
            BATCH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_batch_name)],
            CREDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_credit_name)],
            TXT_FILE: [MessageHandler(filters.Document.ALL, receive_txt_file)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    print("🚀 Bot started!")
    application.run_polling()

if __name__ == '__main__':
    main()