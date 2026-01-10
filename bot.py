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
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{batch_name}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }}

        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --accent-hover: #0ea5e9;
            --border: #475569;
            --danger: #ef4444;
            --success: #22c55e;
            --warning: #eab308;
        }}

        body.theme-light {{
            --bg-primary: #f8fafc;
            --bg-secondary: #ffffff;
            --bg-card: #f1f5f9;
            --text-primary: #0f172a;
            --text-secondary: #64748b;
            --accent: #0284c7;
            --accent-hover: #0369a1;
            --border: #e2e8f0;
        }}

        body.theme-amoled {{
            --bg-primary: #000000;
            --bg-secondary: #111111;
            --bg-card: #1a1a1a;
            --text-primary: #ffffff;
            --text-secondary: #888888;
            --accent: #ffffff;
            --accent-hover: #cccccc;
            --border: #333333;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            transition: background-color 0.3s ease, color 0.3s ease;
            min-height: 100vh;
            overflow-x: hidden;
        }}

        /* Password Screen */
        #passwordScreen {{
            position: fixed;
            inset: 0;
            background: var(--bg-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }}

        .password-box {{
            background: var(--bg-secondary);
            padding: 2rem;
            border-radius: 1.5rem;
            width: 90%;
            max-width: 400px;
            text-align: center;
            border: 1px solid var(--border);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        }}

        .password-box h1 {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}

        .password-box p {{
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }}

        .input-group {{
            position: relative;
            margin-bottom: 1.5rem;
        }}

        .password-box input {{
            width: 100%;
            padding: 1rem;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            color: var(--text-primary);
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s;
        }}

        .password-box input:focus {{
            border-color: var(--accent);
        }}

        .password-box button {{
            width: 100%;
            padding: 1rem;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 0.75rem;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.1s;
        }}

        .password-box button:active {{
            transform: scale(0.98);
        }}

        /* Shake Animation */
        @keyframes shake {{
            0%, 100% {{ transform: translateX(0); }}
            10%, 30%, 50%, 70%, 90% {{ transform: translateX(-5px); }}
            20%, 40%, 60%, 80% {{ transform: translateX(5px); }}
        }}

        .shake {{
            animation: shake 0.5s;
            border-color: var(--danger) !important;
        }}

        /* Main Content */
        #mainContent {{
            display: none; /* Hidden by default */
            max-width: 800px;
            margin: 0 auto;
            padding: 1.5rem;
            padding-bottom: 100px; /* Space for bottom content if needed */
        }}

        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem 1rem;
            background: var(--bg-secondary);
            border-radius: 1.5rem;
            border: 1px solid var(--border);
        }}

        .batch-name {{
            font-size: 1.75rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, var(--accent), #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .developer {{
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 500;
        }}

        /* Stats Grid */
        .stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background: var(--bg-secondary);
            padding: 1.25rem;
            border-radius: 1rem;
            text-align: center;
            border: 1px solid var(--border);
        }}

        .stat-number {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
        }}

        .stat-label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 0.25rem;
        }}

        /* Theme Selector */
        .theme-scroll {{
            display: flex;
            gap: 0.75rem;
            overflow-x: auto;
            padding-bottom: 0.5rem;
            margin-bottom: 2rem;
            scrollbar-width: none;
        }}

        .theme-scroll::-webkit-scrollbar {{
            display: none;
        }}

        .theme-btn {{
            white-space: nowrap;
            padding: 0.6rem 1.2rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 2rem;
            color: var(--text-primary);
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .theme-btn.active, .theme-btn:hover {{
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }}

        /* Categories & Items */
        .category {{
            margin-bottom: 2rem;
        }}

        .category-header {{
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .category-header::before {{
            content: '';
            width: 4px;
            height: 1.2rem;
            background: var(--accent);
            border-radius: 2px;
        }}

        .item {{
            background: var(--bg-secondary);
            padding: 1rem;
            border-radius: 1rem;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            border: 1px solid var(--border);
            transition: transform 0.2s;
            cursor: pointer;
        }}

        .item:active {{
            transform: scale(0.98);
        }}

        .item-icon {{
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            flex-shrink: 0;
        }}

        .type-video .item-icon {{ background: rgba(239, 68, 68, 0.1); color: var(--danger); }}
        .type-pdf .item-icon {{ background: rgba(234, 179, 8, 0.1); color: var(--warning); }}
        .type-image .item-icon {{ background: rgba(168, 85, 247, 0.1); color: #a855f7; }}
        .type-other .item-icon {{ background: rgba(148, 163, 184, 0.1); color: var(--text-secondary); }}

        .item-content {{
            flex: 1;
            min-width: 0;
        }}

        .item-title {{
            font-weight: 500;
            font-size: 0.95rem;
            margin-bottom: 0.2rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .item-meta {{
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}

        .item-action {{
            color: var(--text-secondary);
        }}

        /* Video Modal - Improved */
        #videoModal {{
            display: none;
            position: fixed;
            inset: 0;
            background: #000;
            z-index: 10000;
            flex-direction: column;
        }}

        #videoModal.active {{
            display: flex;
        }}

        /* Video Container to take available space */
        .video-container {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            background: #000;
            position: relative;
        }}

        video {{
            width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}

        /* Controls Section Below Video */
        .modal-controls {{
            background: var(--bg-secondary);
            padding: 1.5rem;
            border-top: 1px solid var(--border);
            flex-shrink: 0; /* Don't shrink */
        }}

        .modal-info {{
            margin-bottom: 1.5rem;
        }}

        .modal-title {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        .control-group {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .control-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }}

        .speed-control, .volume-control {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--bg-primary);
            padding: 0.5rem;
            border-radius: 0.75rem;
            flex: 1;
            justify-content: center;
        }}

        .control-label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-weight: 600;
        }}

        .control-btn {{
            background: var(--bg-card);
            border: none;
            color: var(--text-primary);
            width: 32px;
            height: 32px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .control-btn:active {{
            background: var(--accent);
            color: white;
        }}

        .close-btn {{
            width: 100%;
            padding: 1rem;
            background: var(--bg-primary);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-radius: 1rem;
            font-weight: 600;
            font-size: 1rem;
            margin-top: 1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }}

        .close-btn:active {{
            background: var(--bg-card);
        }}

        @media (min-width: 768px) {{
            #videoModal {{
                padding: 2rem;
                background: rgba(0,0,0,0.9);
                align-items: center;
                justify-content: center;
            }}
            
            .modal-content-wrapper {{
                width: 100%;
                max-width: 1000px;
                background: var(--bg-secondary);
                border-radius: 1.5rem;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                max-height: 90vh;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            }}

            .video-container {{
                height: 60vh;
                background: #000;
            }}

            .modal-controls {{
                background: var(--bg-secondary);
            }}
        }}
    </style>
</head>
<body class="theme-default">
    <!-- Password Screen -->
    <div id="passwordScreen">
        <div class="password-box">
            <h1>🔒</h1>
            <p>Protected Content</p>
            <div class="input-group">
                <input type="password" id="passwordInput" placeholder="Enter Password" onkeypress="if(event.key==='Enter') checkPassword()">
            </div>
            <button onclick="checkPassword()">Unlock Access</button>
        </div>
    </div>

    <!-- Main Content -->
    <div id="mainContent">
        <div class="header">
            <div class="batch-name">{batch_name}</div>
            <div class="developer">Curated by {credit_name}</div>
        </div>

        <div class="theme-scroll">
            <button class="theme-btn active" onclick="setTheme('default')">Dark</button>
            <button class="theme-btn" onclick="setTheme('light')">Light</button>
            <button class="theme-btn" onclick="setTheme('amoled')">Amoled</button>
        </div>

        <div class="stats"></div>

        <div id="categories"></div>
    </div>

    <!-- Video Modal -->
    <div id="videoModal">
        <!-- Wrapper for desktop styling -->
        <div class="modal-content-wrapper">
            <div class="video-container">
                <video id="videoPlayer" controls controlsList="nodownload"></video>
            </div>

            <div class="modal-controls">
                <div class="modal-info">
                    <div class="modal-title" id="videoTitle">Video Title Goes Here</div>
                </div>

                <div class="control-group">
                    <div class="control-row">
                        <!-- Speed Control -->
                        <div class="speed-control">
                            <div class="control-label">Speed</div>
                            <button class="control-btn" onclick="adjustSpeed(-0.25)">-</button>
                            <span id="speedDisplay" style="font-size: 0.9rem; font-weight: 600; width: 40px; text-align: center;">1x</span>
                            <button class="control-btn" onclick="adjustSpeed(0.25)">+</button>
                        </div>

                        <!-- Volume Control (Custom) -->
                         <div class="volume-control">
                            <div class="control-label">Vol</div>
                            <button class="control-btn" onclick="adjustVolume(-0.1)">-</button>
                            <button class="control-btn" onclick="adjustVolume(0.1)">+</button>
                        </div>
                    </div>

                    <button class="close-btn" onclick="closeVideo()">
                        <span>Close Player</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const PASSWORD = "{password}";
        const encryptedData = {encrypted_json};

        function checkPassword() {{
            const input = document.getElementById('passwordInput');
            if (input.value === PASSWORD) {{
                document.getElementById('passwordScreen').style.opacity = '0';
                setTimeout(() => {{
                    document.getElementById('passwordScreen').style.display = 'none';
                    document.getElementById('mainContent').style.display = 'block';
                    loadContent();
                }}, 300);
            }} else {{
                input.style.borderColor = 'var(--danger)';
                input.classList.add('shake');
                setTimeout(() => input.classList.remove('shake'), 500);
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
            let totalImages = 0;
            let totalOther = 0;
            let totalItems = 0;

            const categoriesDiv = document.getElementById('categories');
            categoriesDiv.innerHTML = '';
            
            for (const [category, items] of Object.entries(encryptedData)) {{
                totalItems += items.length;
                items.forEach(item => {{
                    if (item.type === 'VIDEO') totalVideos++;
                    else if (item.type === 'PDF') totalPDFs++;
                    else if (item.type === 'IMAGE') totalImages++;
                    else totalOther++;
                }});

                const categoryDiv = document.createElement('div');
                categoryDiv.className = 'category';
                categoryDiv.innerHTML = `<div class="category-header">${{category}}</div>`;

                items.forEach(item => {{
                    const itemDiv = document.createElement('div');
                    
                    let typeClass = 'type-other';
                    let icon = '📁';
                    let metaText = 'File • Open';
                    
                    if (item.type === 'VIDEO') {{
                        typeClass = 'type-video';
                        icon = '▶';
                        metaText = 'Video • Play Now';
                    }} else if (item.type === 'PDF') {{
                        typeClass = 'type-pdf';
                        icon = '📄';
                        metaText = 'PDF • View';
                    }} else if (item.type === 'IMAGE') {{
                        typeClass = 'type-image';
                        icon = '🖼️';
                        metaText = 'Image • View';
                    }}
                    
                    itemDiv.className = `item ${{typeClass}}`;
                    itemDiv.innerHTML = `
                        <div class="item-icon">${{icon}}</div>
                        <div class="item-content">
                            <div class="item-title">${{item.title}}</div>
                            <div class="item-meta">${{metaText}}</div>
                        </div>
                        <div class="item-action">→</div>
                    `;

                    itemDiv.onclick = () => openItem(item.link, item.title, item.type);
                    categoryDiv.appendChild(itemDiv);
                }});

                categoriesDiv.appendChild(categoryDiv);
            }}

             document.querySelector('.stats').innerHTML = `
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
                    <div class="stat-label">Documents</div>
                </div>
            `;
        }}

        function openItem(encrypted, title, type) {{
            const link = decryptLink(encrypted);
            if (!link) {{
                alert('❌ Invalid link!');
                return;
            }}

            if (type === 'VIDEO') {{
                openVideo(title, link);
            }} else {{
                window.open(link, '_blank');
            }}
        }}

        // Theme Handling
        function setTheme(theme) {{
            document.body.className = `theme-${{theme}}`;
            document.querySelectorAll('.theme-btn').forEach(btn => btn.classList.remove('active'));
            if (event) event.target.classList.add('active');
            localStorage.setItem('theme', theme);
        }}

        // Restore theme
        window.onload = function() {{
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {{
                setTheme(savedTheme);
                // Highlight correct button
                document.querySelectorAll('.theme-btn').forEach(btn => {{
                    if(btn.textContent.toLowerCase() === savedTheme ||
                       (savedTheme === 'default' && btn.textContent === 'Dark')) {{
                        btn.classList.add('active');
                    }} else {{
                        btn.classList.remove('active');
                    }}
                }});
            }}
        }};

        // Video Player Logic
        const videoPlayer = document.getElementById('videoPlayer');
        const videoModal = document.getElementById('videoModal');

        function openVideo(title, url) {{
            document.getElementById('videoTitle').textContent = title;
            videoPlayer.src = url;
            videoModal.classList.add('active');
            videoPlayer.play();
        }}

        function closeVideo() {{
            videoModal.classList.remove('active');
            videoPlayer.pause();
            setTimeout(() => {{
                videoPlayer.src = '';
            }}, 300);
        }}

        function adjustSpeed(change) {{
            let newSpeed = videoPlayer.playbackRate + change;
            if (newSpeed < 0.25) newSpeed = 0.25;
            if (newSpeed > 3) newSpeed = 3;
            videoPlayer.playbackRate = newSpeed;
            document.getElementById('speedDisplay').textContent = newSpeed + 'x';
        }}

        function adjustVolume(change) {{
            let newVol = videoPlayer.volume + change;
            if (newVol < 0) newVol = 0;
            if (newVol > 1) newVol = 1;
            videoPlayer.volume = newVol;
        }}

        document.addEventListener('contextmenu', event => event.preventDefault());
    </script>
</body>
</html>'''
    
    return html

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    keyboard = [[InlineKeyboardButton("📝 Create HTML", callback_data='create')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🎉 Welcome to SUPER PARSER HTML Bot!\n\n"
        "✨ Features:\n"
        "• 🔒 Password Protection\n"
        "• 🎨 7 Beautiful Themes\n"
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
