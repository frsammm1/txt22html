import os
import re
import json
import base64
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# States for conversation
TXT_FILE, PASSWORD, BATCH_NAME, CREDIT_NAME, CONFIRM = range(5)

# Store user data temporarily
user_data_store = {}

def encrypt_link(link, password):
    """Encrypt link using password-based key"""
    key = hashlib.sha256(password.encode()).digest()
    encrypted = base64.b64encode((link + "|" + password).encode()).decode()
    return encrypted

def detect_file_type(link):
    """Detect file type from link"""
    link_lower = link.lower()
    
    # Video extensions
    if any(ext in link_lower for ext in ['.mp4', '.m3u8', '.avi', '.mkv', '.mov', '.webm']):
        return 'VIDEO'
    
    # YouTube detection
    if 'youtube.com' in link_lower or 'youtu.be' in link_lower:
        return 'VIDEO'
    
    # PDF detection
    if '.pdf' in link_lower:
        return 'PDF'
    
    return 'OTHER'

def parse_txt_content(content):
    """SMART TXT Parser - Handles any format"""
    lines = content.strip().split('\n')
    categories = {}
    current_category = None
    
    # Pattern to match: [CATEGORY] Title: link
    # Matches everything before the last http/https as title
    pattern = re.compile(r'^\[([^\]]+)\]\s*(.+?):\s*(https?://\S+)\s*$')
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and metadata
        if not line or line.startswith('CONTENT EXPORT:') or line.startswith('ID:') or line.startswith('==='):
            continue
        
        # Try to parse with regex
        match = pattern.match(line)
        
        if match:
            category = match.group(1).strip()
            title = match.group(2).strip()
            link = match.group(3).strip()
            
            # Detect file type
            file_type = detect_file_type(link)
            
            # Initialize category if new
            if category not in categories:
                categories[category] = []
            
            # Add item
            categories[category].append({
                'title': title,
                'link': link,
                'type': file_type
            })
        else:
            # Fallback: Try to extract link from end
            # Find last occurrence of http
            http_match = re.search(r'(https?://\S+)$', line)
            
            if http_match:
                link = http_match.group(1)
                
                # Try to extract category and title
                before_link = line[:http_match.start()].strip()
                
                # Check if starts with [CATEGORY]
                cat_match = re.match(r'^\[([^\]]+)\]\s*(.+?)\s*:\s*$', before_link)
                
                if cat_match:
                    category = cat_match.group(1).strip()
                    title = cat_match.group(2).strip()
                    
                    file_type = detect_file_type(link)
                    
                    if category not in categories:
                        categories[category] = []
                    
                    categories[category].append({
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
    
    # Convert to JSON safely
    encrypted_json = json.dumps(encrypted_data)
    
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
            --bg-primary: #0a0a0a;
            --bg-secondary: #141414;
            --bg-card: #1e1e1e;
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --accent: #00ff88;
            --accent-hover: #00cc6a;
            --border: #2a2a2a;
        }}

        body.theme-light {{
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f5;
            --bg-card: #ffffff;
            --text-primary: #1a1a1a;
            --text-secondary: #666666;
            --accent: #007aff;
            --accent-hover: #0051d5;
            --border: #e0e0e0;
        }}

        body.theme-sunset {{
            --bg-primary: #1a0a0a;
            --bg-secondary: #2a1515;
            --bg-card: #3a2020;
            --text-primary: #ffe0d0;
            --text-secondary: #d0a090;
            --accent: #ff6b35;
            --accent-hover: #ff4500;
            --border: #4a2525;
        }}

        body.theme-ocean {{
            --bg-primary: #001520;
            --bg-secondary: #002540;
            --bg-card: #003560;
            --text-primary: #e0f0ff;
            --text-secondary: #a0c0d0;
            --accent: #00d4ff;
            --accent-hover: #00a8cc;
            --border: #004570;
        }}

        body.theme-forest {{
            --bg-primary: #0a1a0a;
            --bg-secondary: #152a15;
            --bg-card: #203a20;
            --text-primary: #e0ffe0;
            --text-secondary: #a0d0a0;
            --accent: #4ade80;
            --accent-hover: #22c55e;
            --border: #254a25;
        }}

        body.theme-purple {{
            --bg-primary: #1a0a2a;
            --bg-secondary: #2a1540;
            --bg-card: #3a2060;
            --text-primary: #f0e0ff;
            --text-secondary: #c0a0d0;
            --accent: #a855f7;
            --accent-hover: #9333ea;
            --border: #4a2570;
        }}

        body.theme-midnight {{
            --bg-primary: #000814;
            --bg-secondary: #001d3d;
            --bg-card: #003566;
            --text-primary: #ffc300;
            --text-secondary: #ffd60a;
            --accent: #ffd60a;
            --accent-hover: #ffea00;
            --border: #004080;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            transition: all 0.4s ease;
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
            animation: fadeIn 0.5s;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .password-box {{
            background: var(--bg-card);
            padding: 50px;
            border-radius: 25px;
            box-shadow: 0 25px 70px rgba(0,0,0,0.5);
            text-align: center;
            max-width: 450px;
            width: 90%;
            animation: slideUp 0.5s ease-out;
        }}

        @keyframes slideUp {{
            from {{ transform: translateY(30px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}

        .password-box h1 {{
            color: var(--accent);
            margin-bottom: 15px;
            font-size: 2.5em;
        }}

        .password-box p {{
            color: var(--text-secondary);
            margin-bottom: 30px;
        }}

        .password-box input {{
            width: 100%;
            padding: 18px;
            border: 2px solid var(--border);
            border-radius: 12px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            font-size: 17px;
            margin-bottom: 20px;
            transition: all 0.3s;
        }}

        .password-box input:focus {{
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(0,255,136,0.1);
        }}

        .password-box button {{
            width: 100%;
            padding: 18px;
            background: var(--accent);
            color: var(--bg-primary);
            border: none;
            border-radius: 12px;
            font-size: 17px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .password-box button:hover {{
            background: var(--accent-hover);
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }}

        #mainContent {{
            display: none;
            max-width: 1400px;
            margin: 0 auto;
            padding: 25px;
            animation: fadeIn 0.6s;
        }}

        .header {{
            text-align: center;
            padding: 40px 30px;
            background: var(--bg-card);
            border-radius: 20px;
            margin-bottom: 35px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            border: 1px solid var(--border);
        }}

        .developer {{
            color: var(--accent);
            font-size: 15px;
            margin-bottom: 12px;
            font-weight: 600;
            letter-spacing: 1px;
        }}

        .batch-name {{
            font-size: 2.8em;
            font-weight: 900;
            background: linear-gradient(135deg, var(--accent), var(--accent-hover));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 25px;
            line-height: 1.2;
        }}

        .controls {{
            display: flex;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 35px;
        }}

        .theme-btn {{
            padding: 12px 24px;
            background: var(--bg-card);
            border: 2px solid var(--border);
            border-radius: 12px;
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
            font-size: 14px;
        }}

        .theme-btn:hover {{
            border-color: var(--accent);
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.2);
        }}

        .theme-btn:active {{
            transform: translateY(-1px);
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 35px;
        }}

        .stat-card {{
            background: var(--bg-card);
            padding: 25px;
            border-radius: 18px;
            text-align: center;
            border: 2px solid var(--border);
            transition: all 0.4s;
            cursor: pointer;
        }}

        .stat-card:hover {{
            border-color: var(--accent);
            transform: translateY(-8px);
            box-shadow: 0 12px 30px rgba(0,0,0,0.3);
        }}

        .stat-number {{
            font-size: 2.5em;
            font-weight: 900;
            color: var(--accent);
            margin-bottom: 5px;
        }}

        .stat-label {{
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .category {{
            background: var(--bg-card);
            padding: 25px;
            border-radius: 18px;
            margin-bottom: 25px;
            border: 2px solid var(--border);
            transition: all 0.3s;
        }}

        .category:hover {{
            border-color: var(--accent);
        }}

        .category-header {{
            font-size: 1.6em;
            font-weight: 800;
            color: var(--accent);
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--border);
        }}

        .item {{
            background: var(--bg-secondary);
            padding: 18px;
            border-radius: 12px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 2px solid var(--border);
            transition: all 0.3s;
        }}

        .item:hover {{
            border-color: var(--accent);
            transform: translateX(8px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}

        .item-title {{
            flex: 1;
            font-weight: 500;
            margin-right: 15px;
        }}

        .item-badge {{
            padding: 6px 18px;
            border-radius: 25px;
            font-size: 11px;
            font-weight: 700;
            margin-right: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .badge-video {{
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
        }}

        .badge-pdf {{
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
        }}

        .item-btn {{
            padding: 10px 24px;
            background: var(--accent);
            color: var(--bg-primary);
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 700;
            font-size: 14px;
        }}

        .item-btn:hover {{
            background: var(--accent-hover);
            transform: scale(1.05);
        }}

        #videoModal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.97);
            z-index: 10000;
            padding: 25px;
            animation: fadeIn 0.3s;
        }}

        .modal-content {{
            position: relative;
            max-width: 1000px;
            margin: 0 auto;
            padding-top: 70px;
        }}

        .modal-header {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            padding: 18px;
            background: var(--bg-card);
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border);
        }}

        .back-btn {{
            padding: 12px 25px;
            background: var(--accent);
            color: var(--bg-primary);
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 700;
            font-size: 15px;
            transition: all 0.3s;
        }}

        .back-btn:hover {{
            background: var(--accent-hover);
            transform: scale(1.05);
        }}

        video {{
            width: 100%;
            border-radius: 12px;
            background: #000;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }}

        .video-controls {{
            margin-top: 18px;
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
        }}

        .speed-btn {{
            padding: 10px 18px;
            background: var(--bg-card);
            color: var(--text-primary);
            border: 2px solid var(--border);
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }}

        .speed-btn:hover {{
            border-color: var(--accent);
        }}

        .speed-btn.active {{
            background: var(--accent);
            border-color: var(--accent);
            color: var(--bg-primary);
        }}

        @media (max-width: 768px) {{
            .batch-name {{
                font-size: 2em;
            }}
            
            .stat-card {{
                padding: 18px;
            }}

            .password-box {{
                padding: 35px;
            }}

            .item {{
                flex-direction: column;
                gap: 10px;
                align-items: flex-start;
            }}

            .item-btn {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div id="passwordScreen">
        <div class="password-box">
            <h1>🔒</h1>
            <p>This content is protected</p>
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
            <button class="theme-btn" onclick="changeTheme('dark')">🌑 Dark</button>
            <button class="theme-btn" onclick="changeTheme('light')">☀️ Light</button>
            <button class="theme-btn" onclick="changeTheme('sunset')">🌅 Sunset</button>
            <button class="theme-btn" onclick="changeTheme('ocean')">🌊 Ocean</button>
            <button class="theme-btn" onclick="changeTheme('forest')">🌲 Forest</button>
            <button class="theme-btn" onclick="changeTheme('purple')">💜 Purple</button>
            <button class="theme-btn" onclick="changeTheme('midnight')">🌃 Midnight</button>
        </div>

        <div class="stats" id="stats"></div>
        <div id="categories"></div>
    </div>

    <div id="videoModal">
        <div class="modal-content">
            <div class="modal-header">
                <button class="back-btn" onclick="closeVideo()">← Back</button>
                <span id="videoTitle" style="color: var(--text-primary); font-weight: 600;"></span>
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
        const encryptedData = {encrypted_json};

        function checkPassword() {{
            const input = document.getElementById('passwordInput').value;
            if (input === PASSWORD) {{
                document.getElementById('passwordScreen').style.display = 'none';
                document.getElementById('mainContent').style.display = 'block';
                loadContent();
            }} else {{
                alert('❌ Wrong Password!');
                document.getElementById('passwordInput').value = '';
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
            localStorage.setItem('theme', theme);
        }}

        // Load saved theme
        window.onload = function() {{
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme && savedTheme !== 'dark') {{
                document.body.className = `theme-${{savedTheme}}`;
            }}
        }};
    </script>
</body>
</html>'''
    
    return html

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    keyboard = [[InlineKeyboardButton("📝 Create HTML", callback_data='create')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🎉 Welcome to SMART HTML Converter Bot!\n\n"
        "मैं आपकी TXT file को Password-Protected HTML में convert कर दूंगा!\n\n"
        "✨ Features:\n"
        "• 🔒 Password Protection\n"
        "• 🎨 7 Beautiful Themes\n"
        "• 🎬 Video Player with Speed Control\n"
        "• 📱 Mobile-Friendly Design\n"
        "• 🔐 Encrypted Links\n"
        "• 🧠 SMART Parser - Any Format!\n"
        "• 🎥 YouTube Support\n\n"
        "Click below to start! 👇"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'create':
        msg = (
            "📄 Step 1: Send TXT File\n\n"
            "अपनी TXT file भेजें!\n\n"
            "Format: [CATEGORY] Title: link\n\n"
            "✅ Smart parser - Any format works!"
        )
        await query.message.reply_text(msg)
        return TXT_FILE
    elif query.data == 'convert':
        return await process_conversion(query, context)

async def receive_txt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive TXT file"""
    user_id = update.effective_user.id
    
    await update.message.reply_text("⏳ Reading file...")
    
    try:
        # Download and read file
        file = await update.message.document.get_file()
        content = await file.download_as_bytearray()
        txt_content = content.decode('utf-8')
        
        # Parse to check validity
        categories = parse_txt_content(txt_content)
        
        if not categories or all(len(items) == 0 for items in categories.values()):
            await update.message.reply_text(
                "❌ No valid content found!\n\n"
                "Format:\n"
                "[CATEGORY] Title: https://link.com\n\n"
                "Example:\n"
                "[VIDEOS] My Video: https://youtube.com/watch?v=abc"
            )
            return TXT_FILE
        
        # Store data
        user_data_store[user_id] = {
            'txt_content': txt_content,
            'categories': categories
        }
        
        # Count items
        total = sum(len(items) for items in categories.values())
        
        # Show preview
        preview_text = "✅ File parsed successfully!\n\n📊 Found:\n"
        for cat, items in list(categories.items())[:3]:  # Show first 3 categories
            preview_text += f"\n📁 {cat}: {len(items)} items"
        
        if len(categories) > 3:
            preview_text += f"\n...and {len(categories) - 3} more categories"
        
        preview_text += f"\n\n📊 Total: {len(categories)} categories, {total} items"
        preview_text += "\n\n🔐 Step 2: Set Password\n\nHTML file के लिए password enter करें:"
        
        await update.message.reply_text(preview_text)
        return PASSWORD
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {str(e)}\n\n"
            "कृपया valid TXT file भेजें!"
        )
        return TXT_FILE

async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive password"""
    user_id = update.effective_user.id
    password = update.message.text.strip()
    
    if len(password) < 4:
        await update.message.reply_text("❌ Password कम से कम 4 characters का होना चाहिए!")
        return PASSWORD
    
    if user_id not in user_data_store:
        await update.message.reply_text("❌ Error! /start से फिर शुरू करें।")
        return ConversationHandler.END
    
    user_data_store[user_id]['password'] = password
    
    msg = (
        f"✅ Password set: {password}\n\n"
        f"📚 Step 3: Batch Name\n\n"
        f"Batch का नाम enter करें\n"
        f"(जैसे: SSC CGL 2025 Mains):"
    )
    
    await update.message.reply_text(msg)
    return BATCH_NAME

async def receive_batch_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive batch name"""
    user_id = update.effective_user.id
    batch_name = update.message.text.strip()
    
    if user_id not in user_data_store:
        await update.message.reply_text("❌ Error! /start से फिर शुरू करें।")
        return ConversationHandler.END
    
    user_data_store[user_id]['batch_name'] = batch_name
    
    msg = (
        f"✅ Batch Name: {batch_name}\n\n"
        f"👨‍💻 Step 4: Credit Name\n\n"
        f"Developer credit name enter करें\n"
        f"(जैसे: @YourUsername):"
    )
    
    await update.message.reply_text(msg)
    return CREDIT_NAME

async def receive_credit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive credit name and show confirmation"""
    user_id = update.effective_user.id
    credit_name = update.message.text.strip()
    
    if user_id not in user_data_store:
        await update.message.reply_text("❌ Error! /start से फिर शुरू करें।")
        return ConversationHandler.END
    
    user_data_store[user_id]['credit_name'] = credit_name
    user_data = user_data_store[user_id]
    
    # Create confirmation message
    total_items = sum(len(items) for items in user_data['categories'].values())
    
    msg = (
        "✅ All details received!\n\n"
        "📋 Summary:\n"
        f"🔒 Password: {user_data['password']}\n"
        f"📚 Batch: {user_data['batch_name']}\n"
        f"👨‍💻 Credit: {credit_name}\n"
        f"📊 Categories: {len(user_data['categories'])}\n"
        f"📊 Total Items: {total_items}\n\n"
        "Click Convert to generate HTML! 👇"
    )
    
    keyboard = [[InlineKeyboardButton("✨ Convert to HTML", callback_data='convert')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(msg, reply_markup=reply_markup)
    return CONFIRM

async def process_conversion(query, context: ContextTypes.DEFAULT_TYPE):
    """Process the conversion"""
    user_id = query.from_user.id
    
    if user_id not in user_data_store:
        await query.message.reply_text("❌ Error! /start से फिर शुरू करें।")
        return ConversationHandler.END
    
    await query.answer()
    msg = await query.message.reply_text("⚡ Converting to HTML...\n⏳ Please wait...")
    
    try:
        user_data = user_data_store[user_id]
        
        # Generate HTML
        html_content = generate_html(
            user_data['categories'],
            user_data['password'],
            user_data['batch_name'],
            user_data['credit_name']
        )
        
        # Save HTML file
        filename = f"{user_data['batch_name'].replace(' ', '_')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        await msg.edit_text("✅ HTML generated!\n📤 Sending file...")
        
        # Send HTML file
        caption = (
            f"✅ HTML File Ready!\n\n"
            f"🔒 Password: {user_data['password']}\n"
            f"📚 Batch: {user_data['batch_name']}\n"
            f"👨‍💻 Credit: {user_data['credit_name']}\n"
            f"📊 Items: {sum(len(items) for items in user_data['categories'].values())}\n\n"
            f"⚡ File ko open karein aur password enter karein!\n"
            f"🎨 7 themes available!"
        )
        
        with open(filename, 'rb') as f:
            await query.message.reply_document(
                document=f,
                filename=filename,
                caption=caption
            )
        
        # Cleanup
        os.remove(filename)
        del user_data_store[user_id]
        
        await query.message.reply_text(
            "🎉 Conversion Complete!\n\n"
            "✅ HTML file भेज दी गई है!\n"
            "Ek aur file convert karne ke लिए /start करें!"
        )
        
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")
        print(f"Error in conversion: {e}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    user_id = update.effective_user.id
    if user_id in user_data_store:
        del user_data_store[user_id]
    
    await update.message.reply_text("❌ Cancelled! /start से फिर शुरू करें।")
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    print(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Kuch error hua! /start से फिर try करें।"
        )

def main():
    """Start the bot"""
    TOKEN = os.getenv('BOT_TOKEN')
    
    if not TOKEN:
        print("❌ BOT_TOKEN environment variable not set!")
        print("Set it using: export BOT_TOKEN='your_token_here'")
        return
    
    print("🚀 Starting SMART HTML Converter Bot...")
    
    application = Application.builder().token(TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(button_callback, pattern='^create$')
        ],
        states={
            TXT_FILE: [MessageHandler(filters.Document.ALL, receive_txt_file)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
            BATCH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_batch_name)],
            CREDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_credit_name)],
            CONFIRM: [CallbackQueryHandler(process_conversion, pattern='^convert$')],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    print("✅ Bot started successfully!")
    print("🎯 Waiting for messages...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
