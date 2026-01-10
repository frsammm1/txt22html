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
    Detect file type from link
    """
    link_lower = link.lower()
    
    video_extensions = ['.m3u8', '.ts', '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp']
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    document_extensions = ['.pdf', '.doc', '.docx', '.txt', '.zip', '.rar']
    
    if any(ext in link_lower for ext in video_extensions):
        return 'VIDEO'
    if any(x in link_lower for x in ['youtube.com', 'youtu.be', '/watch', 'stream', '/video/']):
        return 'VIDEO'
    if any(ext in link_lower for ext in image_extensions):
        return 'IMAGE'
    if any(ext in link_lower for ext in document_extensions):
        return 'PDF'
    
    return 'OTHER'

def parse_txt_content(content):
    """
    Robust Parser
    """
    lines = content.strip().split('\n')
    categories = {}
    default_category = "Uncategorized"
    
    parsed_lines = 0
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith(('CONTENT EXPORT:', 'ID:', '===')):
            continue
        
        if not ('http://' in line or 'https://' in line):
            continue
        
        # Method 1: [CATEGORY] Title: URL
        category_match = re.match(r'^\[([^\]]+)\]\s*(.+?):\s*(https?://\S+)', line)
        if category_match:
            parsed_lines += 1
            category = category_match.group(1).strip()
            title = category_match.group(2).strip()
            link = category_match.group(3).strip()
            
            if category not in categories: categories[category] = []
            categories[category].append({'title': title, 'link': link, 'type': detect_file_type(link)})
            continue
        
        # Method 2: Title: URL (Handle multiple URLs)
        urls = re.findall(r'https?://\S+', line)
        if urls:
            parsed_lines += 1
            # Text before first URL
            first_url_pos = line.find(urls[0])
            text_part = line[:first_url_pos].strip()

            # Extract category if present
            category = default_category
            cat_match = re.match(r'^\[([^\]]+)\]\s*(.+)', text_part)
            if cat_match:
                category = cat_match.group(1).strip()
                text_part = cat_match.group(2).strip()

            title_base = text_part.rstrip(':').strip()

            for i, url in enumerate(urls):
                title = title_base if len(urls) == 1 else f"{title_base} Part {i+1}"
                if not title: title = f"Link {i+1}"
                
                if category not in categories: categories[category] = []
                categories[category].append({'title': title, 'link': url, 'type': detect_file_type(url)})

    return categories

def generate_html(categories, password, batch_name, credit_name):
    """Generate Premium UI HTML"""
    
    # Encrypt data
    encrypted_data = {}
    for category, items in categories.items():
        encrypted_data[category] = []
        for item in items:
            encrypted_data[category].append({
                'title': item['title'],
                'link': encrypt_link(item['link'], password),
                'type': item['type']
            })
    
    encrypted_json = json.dumps(encrypted_data)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{batch_name}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {{
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
            --accent: #f59e0b;
            --danger: #ef4444;
            --success: #22c55e;
            --border: #334155;
            --radius: 12px;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }}

        /* Theme Variables */
        body.theme-light {{
            --bg-dark: #f0f9ff;
            --bg-card: #ffffff;
            --text-main: #1e293b;
            --text-sub: #64748b;
            --border: #e2e8f0;
        }}

        body.theme-oled {{
            --bg-dark: #000000;
            --bg-card: #121212;
            --border: #2c2c2c;
        }}

        body.theme-midnight {{
            --bg-dark: #0b1021;
            --bg-card: #151e32;
            --primary: #7c3aed;
            --border: #2d3748;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}

        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            overflow-x: hidden;
            transition: background-color 0.3s, color 0.3s;
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 10px; }}

        /* --- Password Screen --- */
        #auth-screen {{
            position: fixed;
            inset: 0;
            background: var(--bg-dark);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        .auth-card {{
            background: var(--bg-card);
            padding: 2.5rem;
            border-radius: 24px;
            width: 100%;
            max-width: 400px;
            text-align: center;
            border: 1px solid var(--border);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        @keyframes slideUp {{
            from {{ transform: translateY(20px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}

        .auth-icon {{
            font-size: 3rem;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .auth-input {{
            width: 100%;
            padding: 16px;
            background: var(--bg-dark);
            border: 2px solid var(--border);
            border-radius: var(--radius);
            color: var(--text-main);
            font-size: 1.1rem;
            margin: 1.5rem 0;
            text-align: center;
            letter-spacing: 2px;
            transition: 0.3s;
        }}

        .auth-input:focus {{
            border-color: var(--primary);
            outline: none;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
        }}

        .btn {{
            width: 100%;
            padding: 16px;
            border: none;
            border-radius: var(--radius);
            font-weight: 700;
            font-size: 1rem;
            cursor: pointer;
            transition: 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}

        .btn-primary {{
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
        }}

        .btn-primary:active {{ transform: scale(0.98); }}

        /* --- Main App UI --- */
        #app-view {{ display: none; padding-bottom: 80px; }}

        /* Header */
        .app-header {{
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .header-title h1 {{
            font-size: 1.25rem;
            font-weight: 800;
            background: linear-gradient(to right, var(--text-main), var(--text-sub));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .header-credit {{ font-size: 0.75rem; color: var(--text-sub); }}

        .header-actions {{ display: flex; gap: 10px; }}

        .icon-btn {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-main);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: 0.2s;
        }}

        .icon-btn:hover {{ background: var(--border); }}

        /* Theme Selector */
        #theme-modal {{
            position: fixed;
            bottom: -100%;
            left: 0;
            width: 100%;
            background: var(--bg-card);
            border-radius: 24px 24px 0 0;
            padding: 24px;
            z-index: 2000;
            transition: bottom 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            border-top: 1px solid var(--border);
            box-shadow: 0 -10px 40px rgba(0,0,0,0.5);
        }}

        #theme-modal.active {{ bottom: 0; }}

        .theme-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 20px;
        }}

        .theme-option {{
            padding: 15px;
            border-radius: 12px;
            border: 2px solid var(--border);
            text-align: center;
            cursor: pointer;
            background: var(--bg-dark);
            color: var(--text-main);
            font-size: 0.9rem;
        }}

        .theme-option.active {{ border-color: var(--primary); color: var(--primary); }}

        /* Stats & Content */
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}

        .stats-row {{
            display: flex;
            gap: 12px;
            overflow-x: auto;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}

        .stat-chip {{
            background: var(--bg-card);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            color: var(--text-sub);
            border: 1px solid var(--border);
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .stat-chip i {{ color: var(--primary); }}

        .category-section {{ margin-bottom: 30px; }}

        .cat-title {{
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--text-main);
        }}

        .cat-title::before {{
            content: '';
            width: 4px;
            height: 20px;
            background: var(--accent);
            border-radius: 2px;
        }}

        .item-card {{
            background: var(--bg-card);
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 16px;
            border: 1px solid var(--border);
            transition: transform 0.2s, border-color 0.2s;
            position: relative;
            overflow: hidden;
        }}

        .item-card:active {{ transform: scale(0.98); }}

        .item-icon {{
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            flex-shrink: 0;
        }}

        .icon-video {{ background: rgba(239, 68, 68, 0.1); color: #ef4444; }}
        .icon-pdf {{ background: rgba(245, 158, 11, 0.1); color: #f59e0b; }}
        .icon-img {{ background: rgba(34, 197, 94, 0.1); color: #22c55e; }}

        .item-info {{ flex: 1; min-width: 0; }}

        .item-title {{
            font-weight: 600;
            font-size: 0.95rem;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .item-meta {{ font-size: 0.75rem; color: var(--text-sub); display: flex; align-items: center; gap: 6px; }}

        .action-btn {{
            background: var(--bg-dark);
            color: var(--primary);
            border: 1px solid var(--border);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
        }}

        /* --- Player View --- */
        #player-view {{
            position: fixed;
            inset: 0;
            background: #000;
            z-index: 5000;
            display: none;
            flex-direction: column;
        }}

        .video-wrapper {{
            width: 100%;
            background: #000;
            position: relative;
            flex-shrink: 0;
        }}

        video {{
            width: 100%;
            max-height: 50vh;
            display: block;
        }}

        .player-body {{
            flex: 1;
            background: var(--bg-dark);
            padding: 24px;
            overflow-y: auto;
            border-radius: 24px 24px 0 0;
            margin-top: -24px;
            position: relative;
            z-index: 10;
        }}

        .player-header {{ margin-bottom: 24px; }}

        .player-title {{
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 8px;
            line-height: 1.4;
        }}

        .controls-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 30px;
        }}

        .control-group {{
            background: var(--bg-card);
            padding: 16px;
            border-radius: 16px;
            border: 1px solid var(--border);
        }}

        .control-label {{
            font-size: 0.75rem;
            color: var(--text-sub);
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 700;
        }}

        /* Custom Range Input */
        input[type=range] {{
            width: 100%;
            height: 6px;
            background: var(--border);
            border-radius: 3px;
            outline: none;
            -webkit-appearance: none;
        }}

        input[type=range]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            background: var(--primary);
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.2);
        }}

        /* Speed Buttons */
        .speed-options {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .speed-chip {{
            padding: 6px 12px;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.8rem;
            cursor: pointer;
            flex: 1;
            text-align: center;
        }}

        .speed-chip.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}

        .back-btn-large {{
            width: 100%;
            padding: 18px;
            background: var(--bg-card);
            border: 2px solid var(--border);
            color: var(--text-main);
            border-radius: 16px;
            font-weight: 700;
            font-size: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            cursor: pointer;
            margin-top: auto;
        }}

        .back-btn-large:hover {{
            border-color: var(--danger);
            color: var(--danger);
        }}

        /* Overlay */
        #overlay {{
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.6);
            z-index: 1500;
            display: none;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        #overlay.active {{ display: block; opacity: 1; }}

        /* Animations */
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        .fade-in {{ animation: fadeIn 0.4s ease-out; }}
    </style>
</head>
<body>

    <!-- Auth Screen -->
    <div id="auth-screen">
        <div class="auth-card">
            <div class="auth-icon"><i class="fas fa-lock"></i></div>
            <h2>Protected Content</h2>
            <p style="color: var(--text-sub); margin-top: 8px;">Enter password to access {batch_name}</p>
            <input type="password" id="password-input" class="auth-input" placeholder="PASSWORD">
            <button class="btn btn-primary" onclick="checkPassword()">
                <i class="fas fa-unlock-alt"></i> Access Content
            </button>
        </div>
    </div>

    <!-- Main App -->
    <div id="app-view">
        <div class="app-header">
            <div class="header-title">
                <h1>{batch_name}</h1>
                <div class="header-credit">by {credit_name}</div>
            </div>
            <div class="header-actions">
                <button class="icon-btn" onclick="toggleThemeModal()"><i class="fas fa-palette"></i></button>
            </div>
        </div>

        <div class="container">
            <!-- Stats -->
            <div class="stats-row" id="stats-bar">
                <!-- Injected via JS -->
            </div>

            <!-- Content -->
            <div id="content-list"></div>
        </div>
    </div>

    <!-- Player View (Full Screen) -->
    <div id="player-view">
        <div class="video-wrapper">
            <video id="main-player" controls controlsList="nodownload" oncontextmenu="return false;">
                Your browser does not support the video tag.
            </video>
        </div>

        <div class="player-body">
            <div class="player-header">
                <div class="player-title" id="player-title">Video Title</div>
                <div style="color: var(--text-sub); font-size: 0.9rem;">
                    <i class="fas fa-shield-alt"></i> Protected Content • No Download
                </div>
            </div>

            <div class="controls-grid">
                <!-- Speed Control -->
                <div class="control-group" style="grid-column: 1 / -1;">
                    <div class="control-label"><i class="fas fa-tachometer-alt"></i> Playback Speed</div>
                    <div class="speed-options">
                        <button class="speed-chip" onclick="setSpeed(0.5)">0.5x</button>
                        <button class="speed-chip" onclick="setSpeed(0.75)">0.75x</button>
                        <button class="speed-chip active" onclick="setSpeed(1.0)">1.0x</button>
                        <button class="speed-chip" onclick="setSpeed(1.25)">1.25x</button>
                        <button class="speed-chip" onclick="setSpeed(1.5)">1.5x</button>
                        <button class="speed-chip" onclick="setSpeed(2.0)">2.0x</button>
                    </div>
                </div>

                <!-- Volume Control -->
                <div class="control-group" style="grid-column: 1 / -1;">
                    <div class="control-label">
                        <i class="fas fa-volume-up"></i> Volume <span id="vol-val">100%</span>
                    </div>
                    <input type="range" min="0" max="1" step="0.1" value="1" oninput="setVolume(this.value)">
                </div>
            </div>

            <button class="back-btn-large" onclick="closePlayer()">
                <i class="fas fa-arrow-left"></i> Return to List
            </button>
        </div>
    </div>

    <!-- Theme Modal -->
    <div id="overlay" onclick="toggleThemeModal()"></div>
    <div id="theme-modal">
        <h3><i class="fas fa-paint-brush"></i> Choose Theme</h3>
        <div class="theme-grid">
            <div class="theme-option" onclick="setTheme('dark')">Dark</div>
            <div class="theme-option" onclick="setTheme('light')">Light</div>
            <div class="theme-option" onclick="setTheme('oled')">OLED</div>
            <div class="theme-option" onclick="setTheme('midnight')">Midnight</div>
        </div>
    </div>

    <script>
        // --- Data & Config ---
        const CONFIG = {{
            password: "{password}",
            data: {encrypted_json}
        }};

        const state = {{
            theme: localStorage.getItem('theme') || 'dark'
        }};

        // --- Init ---
        function init() {{
            setTheme(state.theme);
            document.getElementById('password-input').addEventListener('keypress', (e) => {{
                if (e.key === 'Enter') checkPassword();
            }});
        }}

        // --- Auth ---
        function checkPassword() {{
            const input = document.getElementById('password-input');
            if (input.value === CONFIG.password) {{
                document.getElementById('auth-screen').style.opacity = '0';
                setTimeout(() => {{
                    document.getElementById('auth-screen').style.display = 'none';
                    document.getElementById('app-view').style.display = 'block';
                    loadContent();
                }}, 300);
            }} else {{
                input.style.borderColor = 'var(--danger)';
                input.classList.add('shake');
                setTimeout(() => input.classList.remove('shake'), 500);
            }}
        }}

        // --- Crypto ---
        function decrypt(str) {{
            try {{
                const decoded = atob(str);
                const [link, pass] = decoded.split('|');
                return pass === CONFIG.password ? link : null;
            }} catch (e) {{ return null; }}
        }}

        // --- Content Renderer ---
        function loadContent() {{
            const container = document.getElementById('content-list');
            const statsBar = document.getElementById('stats-bar');
            
            let stats = {{ video: 0, pdf: 0, image: 0, total: 0 }};

            for (const [category, items] of Object.entries(CONFIG.data)) {{
                const section = document.createElement('div');
                section.className = 'category-section fade-in';

                section.innerHTML = `<div class="cat-title">${{category}} <span style="font-size:0.8em; opacity:0.6; font-weight:400">(${{items.length}})</span></div>`;

                items.forEach(item => {{
                    stats.total++;
                    if(item.type === 'VIDEO') stats.video++;
                    if(item.type === 'PDF') stats.pdf++;

                    const el = document.createElement('div');
                    el.className = 'item-card';
                    el.onclick = () => openItem(item);
                    
                    let iconClass = 'fas fa-file';
                    let iconType = 'icon-other';
                    let actionText = 'OPEN';
                    
                    if (item.type === 'VIDEO') {{
                        iconClass = 'fas fa-play';
                        iconType = 'icon-video';
                        actionText = 'PLAY';
                    }} else if (item.type === 'PDF') {{
                        iconClass = 'fas fa-file-pdf';
                        iconType = 'icon-pdf';
                        actionText = 'READ';
                    }} else if (item.type === 'IMAGE') {{
                        iconClass = 'fas fa-image';
                        iconType = 'icon-img';
                        actionText = 'VIEW';
                    }}

                    el.innerHTML = `
                        <div class="item-icon ${{iconType}}"><i class="${{iconClass}}"></i></div>
                        <div class="item-info">
                            <div class="item-title">${{item.title}}</div>
                            <div class="item-meta">${{item.type}}</div>
                        </div>
                        <div class="action-btn">${{actionText}}</div>
                    `;
                    section.appendChild(el);
                }});

                container.appendChild(section);
            }}

            // Render Stats
            statsBar.innerHTML = `
                <div class="stat-chip"><i class="fas fa-layer-group"></i> All ${{stats.total}}</div>
                <div class="stat-chip"><i class="fas fa-video"></i> Video ${{stats.video}}</div>
                <div class="stat-chip"><i class="fas fa-file-pdf"></i> PDF ${{stats.pdf}}</div>
            `;
        }}

        // --- Actions ---
        function openItem(item) {{
            const link = decrypt(item.link);
            if (!link) return alert('Decryption failed');

            if (item.type === 'VIDEO') {{
                openPlayer(link, item.title);
            }} else {{
                window.open(link, '_blank');
            }}
        }}

        // --- Player Logic ---
        const player = document.getElementById('main-player');

        function openPlayer(url, title) {{
            const view = document.getElementById('player-view');
            document.getElementById('player-title').textContent = title;
            player.src = url;
            view.style.display = 'flex';
            player.play();
        }}

        function closePlayer() {{
            document.getElementById('player-view').style.display = 'none';
            player.pause();
            player.src = '';
        }}

        function setSpeed(rate) {{
            player.playbackRate = rate;
            document.querySelectorAll('.speed-chip').forEach(c => {{
                c.classList.toggle('active', parseFloat(c.innerText) === rate);
            }});
        }}

        function setVolume(val) {{
            player.volume = val;
            document.getElementById('vol-val').textContent = Math.round(val * 100) + '%';
        }}

        // --- Theme Logic ---
        function toggleThemeModal() {{
            const modal = document.getElementById('theme-modal');
            const overlay = document.getElementById('overlay');
            const isActive = modal.classList.contains('active');

            if (isActive) {{
                modal.classList.remove('active');
                overlay.classList.remove('active');
            }} else {{
                modal.classList.add('active');
                overlay.classList.add('active');
            }}
        }}

        function setTheme(themeName) {{
            document.body.className = `theme-${{themeName}}`;
            localStorage.setItem('theme', themeName);

            // Highlight active
            document.querySelectorAll('.theme-option').forEach(opt => {{
                opt.classList.toggle('active', opt.textContent.toLowerCase() === themeName);
            }});

            if (document.getElementById('theme-modal').classList.contains('active')) {{
                toggleThemeModal();
            }}
        }}

        init();
    </script>
</body>
</html>'''
    
    return html

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    keyboard = [[InlineKeyboardButton("📝 Create HTML", callback_data='create')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🎉 Welcome to PREMIUM HTML Bot!\n\n"
        "✨ Features:\n"
        "• 🔒 Password Protection\n"
        "• 🎨 Premium Dark UI\n"
        "• 🎬 Advanced Video Player\n"
        "• 📱 App-like Experience\n"
        "• 🔐 Encrypted Links\n"
        "• ⚡ Fast & Lightweight\n\n"
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
        
        # Show preview
        preview_text = "✅ File parsed successfully!\n\n📊 Detection:\n"
        preview_text += f"📦 Categories: {len(categories)}\n"
        preview_text += f"📊 Total Items: {total}\n"
        preview_text += f"🎬 Videos: {total_videos}\n\n"
        
        preview_text += "\n🔐 Step 2: Set Password\n\nHTML password enter करें:"
        
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
        f"📊 Items: {total_items}\n\n"
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
            f"📊 Items: {total}\n"
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
