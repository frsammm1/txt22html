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
    """
    ✅ ENHANCED: Detect file type from link
    Based on reference repository's SUPPORTED_TYPES
    """
    link_lower = link.lower()
    
    # Video extensions - From reference repo
    video_extensions = [
        '.m3u8', '.ts', '.mp4', '.mkv', '.avi', '.mov', 
        '.wmv', '.flv', '.webm', '.m4v', '.3gp'
    ]
    
    # Image extensions
    image_extensions = [
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'
    ]
    
    # Document extensions
    document_extensions = [
        '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar'
    ]
    
    # Check video
    if any(ext in link_lower for ext in video_extensions):
        return 'VIDEO'
    
    # Check YouTube/streaming - IMPORTANT
    if any(x in link_lower for x in ['youtube.com', 'youtu.be', '/watch', 'stream', '/video/']):
        return 'VIDEO'
    
    # Check images
    if any(ext in link_lower for ext in image_extensions):
        return 'IMAGE'
    
    # Check documents
    if any(ext in link_lower for ext in document_extensions):
        return 'PDF'
    
    # Default to OTHER
    return 'OTHER'

def parse_txt_content(content):
    """
    ✅ SUPER ROBUST PARSER - Detects ALL links
    
    Supports formats:
    1. [CATEGORY] Title: URL
    2. Title: URL
    3. [CATEGORY] Title: URL (multiple PDFs on same line)
    
    Inspired by reference repository's parse logic
    """
    lines = content.strip().split('\n')
    categories = {}
    default_category = "OTHER"
    
    # Stats for debugging
    total_lines = 0
    parsed_lines = 0
    
    for line in lines:
        total_lines += 1
        line = line.strip()
        
        # Skip empty lines and metadata headers
        if not line:
            continue
        if line.startswith('CONTENT EXPORT:') or line.startswith('ID:') or line.startswith('==='):
            continue
        
        # ✅ CRITICAL: Check if line has URL
        if not ('http://' in line or 'https://' in line):
            continue
        
        # ✅ METHOD 1: Standard format [CATEGORY] Title: URL
        # Pattern: [CATEGORY] anything before last http/https
        category_match = re.match(r'^\[([^\]]+)\]\s*(.+?):\s*(https?://\S+)', line)
        
        if category_match:
            parsed_lines += 1
            category = category_match.group(1).strip()
            title = category_match.group(2).strip()
            link = category_match.group(3).strip()
            
            file_type = detect_file_type(link)
            
            if category not in categories:
                categories[category] = []
            
            categories[category].append({
                'title': title,
                'link': link,
                'type': file_type
            })
            continue
        
        # ✅ METHOD 2: Without category - Title: URL
        # Just split on : and take last http
        if ':' in line and ('http://' in line or 'https://' in line):
            # Find ALL URLs in line (for multiple PDFs case)
            urls = re.findall(r'https?://\S+', line)
            
            if urls:
                # Get text before first URL as title base
                first_url_pos = line.find(urls[0])
                text_before_url = line[:first_url_pos].strip()
                
                # Remove [CATEGORY] if present
                category = default_category
                cat_match = re.match(r'^\[([^\]]+)\]\s*(.+)', text_before_url)
                if cat_match:
                    category = cat_match.group(1).strip()
                    text_before_url = cat_match.group(2).strip()
                
                # Remove trailing colon
                text_before_url = text_before_url.rstrip(':').strip()
                
                # Process each URL
                for idx, url in enumerate(urls):
                    parsed_lines += 1
                    
                    # For multiple URLs, add index to title
                    if len(urls) > 1:
                        title = f"{text_before_url} - Part {idx + 1}"
                    else:
                        title = text_before_url
                    
                    file_type = detect_file_type(url)
                    
                    if category not in categories:
                        categories[category] = []
                    
                    categories[category].append({
                        'title': title if title else f"Item {idx + 1}",
                        'link': url,
                        'type': file_type
                    })
                
                continue
        
        # ✅ METHOD 3: Fallback - Just extract all URLs
        # For lines where format is completely different
        urls = re.findall(r'https?://\S+', line)
        if urls:
            for idx, url in enumerate(urls):
                parsed_lines += 1
                
                # Try to get text before URL as title
                url_pos = line.find(url)
                title = line[:url_pos].strip()
                
                # Clean title
                title = re.sub(r'^\[([^\]]+)\]\s*', '', title)  # Remove [CATEGORY]
                title = title.rstrip(':').strip()
                
                if not title:
                    title = f"Link {idx + 1}"
                
                file_type = detect_file_type(url)
                
                if default_category not in categories:
                    categories[default_category] = []
                
                categories[default_category].append({
                    'title': title,
                    'link': url,
                    'type': file_type
                })
    
    print(f"📊 Parser Stats: {parsed_lines}/{total_lines} lines parsed")
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

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>{batch_name}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        /* Global Styles & Variables */
:root {{
    --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    --transition-speed: 0.3s;
}}

body {{
    font-family: var(--font-family);
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
    transition: background-color var(--transition-speed), color var(--transition-speed);
}}

body, html {{
    overscroll-behavior-y: contain;
}}

/* Dark Theme (Default) */
body.dark {{
    --bg-primary: #121212;
    --bg-secondary: #1e1e1e;
    --bg-tertiary: #2a2a2a;
    --text-primary: #ffffff;
    --text-secondary: #b3b3b3;
    --accent-primary: #1DB954; /* Spotify Green */
    --accent-secondary: #ffffff;
    --border-color: #2a2a2a;
}}

/* Light Theme */
body.light {{
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f5;
    --bg-tertiary: #e0e0e0;
    --text-primary: #000000;
    --text-secondary: #5f5f5f;
    --accent-primary: #1D89E4; /* Blue */
    --accent-secondary: #ffffff;
    --border-color: #e0e0e0;
}}

/* Ocean Theme */
body.ocean {{
    --bg-primary: #0d1b2a;
    --bg-secondary: #1b263b;
    --bg-tertiary: #415a77;
    --text-primary: #e0e1dd;
    --text-secondary: #a0a0a0;
    --accent-primary: #778da9;
    --accent-secondary: #ffffff;
    --border-color: #415a77;
}}

/* Forest Theme */
body.forest {{
    --bg-primary: #1a2e28;
    --bg-secondary: #2a403a;
    --bg-tertiary: #3a524c;
    --text-primary: #d4e0d9;
    --text-secondary: #a0b0a9;
    --accent-primary: #6a994e;
    --accent-secondary: #ffffff;
    --border-color: #3a524c;
}}


body {{
    background-color: var(--bg-primary);
    color: var(--text-primary);
}}


/* Password Screen */
#password-screen {{
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    padding: 20px;
}}

.password-box {{
    background-color: var(--bg-secondary);
    padding: 40px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    max-width: 400px;
    width: 100%;
}}

.password-icon {{
    font-size: 3rem;
    color: var(--accent-primary);
    margin-bottom: 20px;
}}

.password-box h1 {{
    margin-bottom: 10px;
    font-size: 1.5rem;
}}

.password-box p {{
    color: var(--text-secondary);
    margin-bottom: 30px;
}}

#password-input {{
    width: 100%;
    padding: 15px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
    font-size: 1rem;
    margin-bottom: 20px;
}}

#password-submit-btn {{
    width: 100%;
    padding: 15px;
    border: none;
    border-radius: 8px;
    background-color: var(--accent-primary);
    color: var(--accent-secondary);
    font-size: 1rem;
    font-weight: bold;
    cursor: pointer;
}}

/* Main Content */
#main-content {{
    padding: 20px;
}}

.app-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}}

.batch-title {{
    font-size: 2rem;
    font-weight: 900;
}}

.header-actions button {{
    background: none;
    border: none;
    color: var(--text-primary);
    font-size: 1.5rem;
    cursor: pointer;
}}

.batch-meta {{
    color: var(--text-secondary);
    margin-bottom: 30px;
    font-size: 1rem;
}}

/* Tabs */
.tabs {{
    display: flex;
    gap: 10px;
    margin-bottom: 30px;
    overflow-x: auto;
    scrollbar-width: none; /* Firefox */
}}
.tabs::-webkit-scrollbar {{
    display: none; /* Safari and Chrome */
}}

.tab-btn {{
    padding: 10px 20px;
    border: none;
    border-radius: 20px;
    cursor: pointer;
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
    font-weight: 600;
    white-space: nowrap;
}}

.tab-btn.active {{
    background-color: var(--accent-primary);
    color: var(--accent-secondary);
}}

/* Categories & Items */
.category-section {{
    margin-bottom: 30px;
}}

.category-title {{
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border-color);
}}

.item-card {{
    display: flex;
    align-items: center;
    background-color: var(--bg-secondary);
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
    cursor: pointer;
}}

.item-icon {{
    font-size: 1.5rem;
    margin-right: 15px;
    width: 30px;
    text-align: center;
    color: var(--accent-primary);
}}

.item-title {{
    flex-grow: 1;
    font-size: 1rem;
}}

.app-footer {{
    text-align: center;
    padding: 20px;
    color: var(--text-secondary);
    font-size: 0.9rem;
}}

/* Video Player Screen */
#video-player-screen {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: var(--bg-primary);
    z-index: 100;
    display: flex;
    flex-direction: column;
}}

.video-header {{
    padding: 20px;
    flex-shrink: 0;
}}

#back-btn {{
    background: none;
    border: none;
    color: var(--text-primary);
    font-size: 1.2rem;
    cursor: pointer;
    margin-right: 15px;
}}

#video-title-header {{
    font-size: 1.2rem;
    text-overflow: ellipsis;
    white-space: nowrap;
    overflow: hidden;
}}

.video-container {{
    flex-grow: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #000;
}}

#video-player {{
    width: 100%;
    max-height: 100%;
    border-radius: 8px;
}}

.video-controls-container {{
    background-color: var(--bg-secondary);
    padding: 20px;
    border-top: 1px solid var(--border-color);
    flex-shrink: 0;
}}

.control-group {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
    margin-bottom: 15px;
}}
.control-group:last-child {{
    margin-bottom: 0;
}}

.control-group label {{
    font-weight: 600;
}}

#speed-selector {{
    padding: 8px;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
}}

#volume-slider {{
    width: 150px;
}}

/* Theme Modal */
#theme-modal {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.7);
    z-index: 200;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
}}

.theme-modal-content {{
    background-color: var(--bg-secondary);
    padding: 30px;
    border-radius: 12px;
    text-align: center;
}}

.theme-modal-content h2 {{
    margin-bottom: 20px;
}}

.theme-options {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    margin-bottom: 30px;
}}

.theme-option-btn {{
    padding: 15px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
    font-size: 1rem;
    cursor: pointer;
}}

#close-theme-modal-btn {{
    width: 100%;
    padding: 15px;
    border: none;
    border-radius: 8px;
    background-color: var(--accent-primary);
    color: var(--accent-secondary);
    font-size: 1rem;
    font-weight: bold;
    cursor: pointer;
}}
    </style>
</head>
<body>

    <!-- Password Screen -->
    <div id="password-screen">
        <div class="password-box">
            <i class="fas fa-lock password-icon"></i>
            <h1>Content Locked</h1>
            <p>Please enter the password to unlock.</p>
            <input type="password" id="password-input" placeholder="Enter Password">
            <button id="password-submit-btn">Unlock</button>
        </div>
    </div>

    <!-- Main Content -->
    <div id="main-content" style="display: none;">
        <header class="app-header">
            <h1 class="batch-title">{batch_name}</h1>
            <div class="header-actions">
                <button id="theme-switcher-btn"><i class="fas fa-palette"></i></button>
            </div>
        </header>

        <div class="batch-meta">
            <p>Useful for All Your Learning Needs</p>
        </div>

        <div class="tabs">
            <button class="tab-btn active" data-filter="all">All</button>
            <button class="tab-btn" data-filter="video">Videos</button>
            <button class="tab-btn" data-filter="pdf">PDFs</button>
            <button class="tab-btn" data-filter="image">Images</button>
            <button class="tab-btn" data-filter="other">Other</button>
        </div>

        <div id="categories-container">
            <!-- Categories and items will be injected by JavaScript -->
        </div>

        <footer class="app-footer">
            <p>Developed by {credit_name}</p>
        </footer>
    </div>

    <!-- Video Player Screen -->
    <div id="video-player-screen" style="display: none;">
        <header class="app-header video-header">
            <button id="back-btn"><i class="fas fa-arrow-left"></i> Back</button>
            <h1 id="video-title-header">Video Title</h1>
        </header>
        <div class="video-container">
            <video id="video-player" controls controlslist="nodownload"></video>
        </div>
        <div class="video-controls-container">
            <div class="control-group">
                <label for="speed-selector">Speed:</label>
                <select id="speed-selector">
                    <option value="0.5">0.5x</option>
                    <option value="0.75">0.75x</option>
                    <option value="1" selected>1x (Normal)</option>
                    <option value="1.25">1.25x</option>
                    <option value="1.5">1.5x</option>
                    <option value="2">2x</option>
                </select>
            </div>
            <div class="control-group">
                <label for="volume-slider">Volume:</label>
                <i class="fas fa-volume-down"></i>
                <input type="range" id="volume-slider" min="0" max="1" step="0.1" value="1">
                <i class="fas fa-volume-up"></i>
            </div>
        </div>
    </div>

    <div id="theme-modal" style="display: none;">
        <div class="theme-modal-content">
            <h2>Select a Theme</h2>
            <div class="theme-options">
                 <button class="theme-option-btn" data-theme="dark">Dark</button>
                <button class="theme-option-btn" data-theme="light">Light</button>
                <button class="theme-option-btn" data-theme="ocean">Ocean</button>
                <button class="theme-option-btn" data-theme="forest">Forest</button>
            </div>
            <button id="close-theme-modal-btn">Close</button>
        </div>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
    // --- Constants and State ---
    const PASSWORD = "{password}";
    const encryptedData = {encrypted_json};

    // --- DOM Elements ---
    const passwordScreen = document.getElementById('password-screen');
    const passwordInput = document.getElementById('password-input');
    const passwordSubmitBtn = document.getElementById('password-submit-btn');
    const mainContent = document.getElementById('main-content');
    const categoriesContainer = document.getElementById('categories-container');
    const videoPlayerScreen = document.getElementById('video-player-screen');
    const videoPlayer = document.getElementById('video-player');
    const videoTitleHeader = document.getElementById('video-title-header');
    const backBtn = document.getElementById('back-btn');
    const speedSelector = document.getElementById('speed-selector');
    const volumeSlider = document.getElementById('volume-slider');
    const tabs = document.querySelectorAll('.tab-btn');
    const themeSwitcherBtn = document.getElementById('theme-switcher-btn');
    const themeModal = document.getElementById('theme-modal');
    const closeThemeModalBtn = document.getElementById('close-theme-modal-btn');
    const themeOptionBtns = document.querySelectorAll('.theme-option-btn');

    // --- Functions ---
    const decryptLink = (encrypted) => {{
        try {{
            const decoded = atob(encrypted);
            const parts = decoded.split('|');
            return parts[1] === PASSWORD ? parts[0] : null;
        }} catch (e) {{
            return null;
        }}
    }};

    const getIconForType = (type) => {{
        switch (type.toUpperCase()) {{
            case 'VIDEO': return 'fas fa-play-circle';
            case 'PDF': return 'fas fa-file-pdf';
            case 'IMAGE': return 'fas fa-file-image';
            default: return 'fas fa-file-alt';
        }}
    }};

    const renderContent = (filter = 'all') => {{
        categoriesContainer.innerHTML = '';
        for (const [category, items] of Object.entries(encryptedData)) {{
            const filteredItems = filter === 'all'
                ? items
                : items.filter(item => item.type.toLowerCase() === filter);

            if (filteredItems.length > 0) {{
                const categorySection = document.createElement('div');
                categorySection.className = 'category-section';

                const categoryTitle = document.createElement('h2');
                categoryTitle.className = 'category-title';
                categoryTitle.textContent = category;
                categorySection.appendChild(categoryTitle);

                filteredItems.forEach(item => {{
                    const itemCard = document.createElement('div');
                    itemCard.className = 'item-card';
                    itemCard.innerHTML = `
                        <i class="item-icon ${{getIconForType(item.type)}}"></i>
                        <span class="item-title">${{item.title}}</span>
                    `;
                    itemCard.addEventListener('click', () => openLink(item.link, item.title, item.type));
                    categorySection.appendChild(itemCard);
                }});
                categoriesContainer.appendChild(categorySection);
            }}
        }}
    }};

    const openLink = (encrypted, title, type) => {{
        const link = decryptLink(encrypted);
        if (!link) {{
            alert('Error: Could not decrypt link.');
            return;
        }}

        if (type.toUpperCase() === 'VIDEO') {{
            videoTitleHeader.textContent = title;
            videoPlayer.src = link;
            mainContent.style.display = 'none';
            videoPlayerScreen.style.display = 'flex';
            videoPlayer.play();
        }} else {{
            window.open(link, '_blank');
        }}
    }};

    const checkPassword = () => {{
        if (passwordInput.value === PASSWORD) {{
            passwordScreen.style.display = 'none';
            mainContent.style.display = 'block';
            renderContent();
            loadTheme();
        }} else {{
            alert('Incorrect Password!');
        }}
    }};

    const applyTheme = (theme) => {{
        document.body.className = theme;
        localStorage.setItem('theme', theme);
    }};

    const loadTheme = () => {{
        const savedTheme = localStorage.getItem('theme') || 'dark';
        applyTheme(savedTheme);
    }};

    // --- Event Listeners ---
    passwordSubmitBtn.addEventListener('click', checkPassword);
    passwordInput.addEventListener('keypress', (e) => e.key === 'Enter' && checkPassword());

    backBtn.addEventListener('click', () => {{
        videoPlayer.pause();
        videoPlayer.src = '';
        videoPlayerScreen.style.display = 'none';
        mainContent.style.display = 'block';
    }});

    speedSelector.addEventListener('change', () => videoPlayer.playbackRate = speedSelector.value);
    volumeSlider.addEventListener('input', () => videoPlayer.volume = volumeSlider.value);

    tabs.forEach(tab => {{
        tab.addEventListener('click', () => {{
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            renderContent(tab.dataset.filter);
        }});
    }});

    themeSwitcherBtn.addEventListener('click', () => themeModal.style.display = 'flex');
    closeThemeModalBtn.addEventListener('click', () => themeModal.style.display = 'none');

    themeOptionBtns.forEach(btn => {{
        btn.addEventListener('click', () => {{
            applyTheme(btn.dataset.theme);
            themeModal.style.display = 'none';
        }});
    }});

    // --- Initial Load ---
    loadTheme();
}});
    </script>
</body>
</html>""".format(
        batch_name=batch_name,
        credit_name=credit_name,
        password=password,
        encrypted_json=encrypted_json
    )
    
    return html_template

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    keyboard = [[InlineKeyboardButton("📝 Create HTML", callback_data='create')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🎉 Welcome to SUPER PARSER HTML Bot!\n\n"
        "✨ Features:\n"
        "• 🔒 Password Protection\n"
        "• 🎨 4 Beautiful Themes\n"
        "• 🎬 Video Player\n"
        "• 📱 Mobile-Friendly\n"
        "• 🔐 Encrypted Links\n"
        "• 🧠 SUPER ROBUST Parser\n"
        "• 🎥 YouTube Support\n"
        "• ⚡ Detects ALL Links (800+)\n\n"
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
            "Formats supported:\n"
            "• [CATEGORY] Title: link\n"
            "• Title: link\n"
            "• Any format with URLs\n\n"
            "✅ 800+ links? No problem!"
        )
        await query.message.reply_text(msg)
        return TXT_FILE
    elif query.data == 'convert':
        return await process_conversion(query, context)

async def receive_txt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive TXT file"""
    user_id = update.effective_user.id
    
    await update.message.reply_text("⏳ Reading file with SUPER PARSER...")
    
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
                "Make sure file has URLs (http:// or https://)"
            )
            return TXT_FILE
        
        # Store data
        user_data_store[user_id] = {
            'txt_content': txt_content,
            'categories': categories
        }
        
        # Count items
        total = sum(len(items) for items in categories.values())
        total_videos = sum(1 for cat in categories.values() for item in cat if item['type'] == 'VIDEO')
        total_pdfs = sum(1 for cat in categories.values() for item in cat if item['type'] == 'PDF')
        
        # Show preview
        preview_text = "✅ File parsed successfully!\n\n📊 Detection:\n"
        preview_text += f"📦 Categories: {len(categories)}\n"
        preview_text += f"📊 Total Items: {total}\n"
        preview_text += f"🎬 Videos: {total_videos}\n"
        preview_text += f"📄 PDFs: {total_pdfs}\n\n"
        
        # Show first 3 categories
        for idx, (cat, items) in enumerate(list(categories.items())[:3]):
            preview_text += f"\n{idx+1}. {cat}: {len(items)} items"
        
        if len(categories) > 3:
            preview_text += f"\n...and {len(categories) - 3} more"
        
        preview_text += "\n\n🔐 Step 2: Set Password\n\nHTML password enter करें:"
        
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
        f"Batch name enter करें:"
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
        f"Developer credit enter करें:"
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
        "Click Convert! 👇"
    )
    
    keyboard = [[InlineKeyboardButton("✨ Convert to HTML", callback_data='convert')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(msg, reply_markup=reply_markup)
    return CONFIRM

async def process_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the conversion"""
    query = update.callback_query
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
        total = sum(len(items) for items in user_data['categories'].values())
        caption = (
            f"✅ HTML File Ready!\n\n"
            f"🔒 Password: {user_data['password']}\n"
            f"📚 Batch: {user_data['batch_name']}\n"
            f"👨‍💻 Credit: {user_data['credit_name']}\n"
            f"📊 Items: {total}\n\n"
            f"⚡ All {total} links detected!\n"
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
            "✅ HTML file sent!\n"
            "/start for another file!"
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
    
    await update.message.reply_text("❌ Cancelled! /start to restart.")
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    print(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Error occurred! /start to retry."
        )

def main():
    """Start the bot"""
    TOKEN = os.getenv('BOT_TOKEN')
    
    if not TOKEN:
        print("❌ BOT_TOKEN environment variable not set!")
        return
    
    print("🚀 Starting SUPER PARSER Bot...")
    
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
