import os
import re
import json
import base64
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# States for conversation
TXT_FILE, BATCH_NAME, CREDIT_NAME, CONFIRM = range(4)

# Store user data temporarily
user_data_store = {}

def encrypt_link(link):
    """Simple encoding for link (No Password)"""
    encrypted = base64.b64encode(link.encode()).decode()
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
        
        # Method 1: [CATEGORY] Title: URL (Allows spaces in URL)
        category_match = re.match(r'^\[([^\]]+)\]\s*(.+?):\s*(https?://.+)', line)
        if category_match:
            parsed_lines += 1
            category = category_match.group(1).strip()
            title = category_match.group(2).strip()
            link = category_match.group(3).strip()
            
            if category not in categories: categories[category] = []
            categories[category].append({'title': title, 'link': link, 'type': detect_file_type(link)})
            continue
        
        # Method 2: Title: URL (Handle spaces if single URL ending in extension)
        # Check for single URL with spaces (e.g. PDF/Video) at end of line
        space_url_match = re.search(r'(?:.+?:\s*)?(https?://.*\.(?:pdf|mp4|mkv|mov|avi|flv|webm|m3u8|ts|3gp|jpg|png|jpeg))$', line, re.IGNORECASE)

        if space_url_match:
            urls = [space_url_match.group(1)]
        else:
            # Fallback to standard non-space split
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

def generate_html(categories, batch_name, credit_name):
    """Generate Premium UI HTML"""
    
    # Encrypt data
    encrypted_data = {}
    for category, items in categories.items():
        encrypted_data[category] = []
        for item in items:
            encrypted_data[category].append({
                'title': item['title'],
                'link': encrypt_link(item['link']),
                'type': item['type']
            })
    
    encrypted_json = json.dumps(encrypted_data)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{batch_name}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/hls.js/1.4.0/hls.min.js"></script>
    <style>
        :root {{
            --primary: #4f46e5;
            --primary-glow: rgba(79, 70, 229, 0.4);
            --bg-body: #0f172a;
            --surface: #1e293b;
            --surface-glass: rgba(30, 41, 59, 0.7);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: rgba(148, 163, 184, 0.1);
            --radius-lg: 20px;
            --radius-md: 12px;
            --radius-sm: 8px;
            --gradient-1: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        }}

        body.theme-light {{
            --bg-body: #f8fafc;
            --surface: #ffffff;
            --surface-glass: rgba(255, 255, 255, 0.8);
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border: rgba(148, 163, 184, 0.2);
        }}

        body.theme-midnight {{
            --bg-body: #020617;
            --surface: #0f172a;
            --surface-glass: rgba(15, 23, 42, 0.8);
            --primary: #7c3aed;
            --gradient-1: linear-gradient(135deg, #7c3aed 0%, #c026d3 100%);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}

        body {{
            font-family: 'Outfit', sans-serif;
            background: var(--bg-body);
            color: var(--text-main);
            min-height: 100vh;
            overflow-x: hidden;
            transition: all 0.3s ease;
        }}

        /* Enhanced Scrollbar */
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: var(--text-muted); opacity: 0.3; border-radius: 10px; }}

        /* --- Header --- */
        .app-header {{
            position: sticky;
            top: 0;
            z-index: 50;
            background: var(--surface-glass);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .brand {{
            font-weight: 800;
            font-size: 1.4rem;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }}

        .theme-toggle {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: rgba(125,125,125,0.1);
            border: none;
            color: var(--text-main);
            font-size: 1.2rem;
            cursor: pointer;
            transition: 0.3s;
        }}

        .theme-toggle:hover {{ background: var(--primary); color: white; }}

        /* --- List View --- */
        .container {{ max-width: 900px; margin: 0 auto; padding: 24px; }}

        .stat-bar {{
            display: flex;
            gap: 12px;
            margin-bottom: 30px;
            overflow-x: auto;
            padding-bottom: 5px;
        }}

        .stat-pill {{
            padding: 10px 20px;
            background: var(--surface);
            border-radius: 100px;
            border: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.9rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            white-space: nowrap;
        }}

        .stat-pill.active {{
            background: var(--gradient-1);
            color: white;
            border-color: transparent;
        }}

        .section-title {{
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-muted);
            font-weight: 700;
            margin: 30px 0 15px;
            padding-left: 10px;
            border-left: 3px solid var(--primary);
        }}

        .content-card {{
            background: var(--surface);
            border-radius: var(--radius-lg);
            padding: 20px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 20px;
            border: 1px solid var(--border);
            transition: all 0.2s;
            cursor: pointer;
        }}

        .content-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px -5px rgba(0,0,0,0.1);
            border-color: var(--primary);
        }}

        .card-icon {{
            width: 56px;
            height: 56px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            flex-shrink: 0;
            background: rgba(125,125,125,0.05);
        }}

        .type-video .card-icon {{ color: #f43f5e; background: rgba(244, 63, 94, 0.1); }}
        .type-pdf .card-icon {{ color: #f59e0b; background: rgba(245, 158, 11, 0.1); }}
        .type-image .card-icon {{ color: #10b981; background: rgba(16, 185, 129, 0.1); }}

        .card-info {{ flex: 1; min-width: 0; }}

        .card-title {{
            font-weight: 600;
            font-size: 1.05rem;
            margin-bottom: 6px;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        .card-meta {{
            font-size: 0.8rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        /* --- Player (Improved) --- */
        #player-view {{
            position: fixed;
            inset: 0;
            background: black;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            transform: translateY(100%);
            transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        #player-view.active {{
            transform: translateY(0);
        }}

        .video-container {{
            width: 100%;
            background: black;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 40vh;
            position: relative;
        }}

        video {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}

        .player-controls {{
            flex: 1;
            background: var(--bg-body);
            border-top: 1px solid var(--border);
            border-radius: 24px 24px 0 0;
            padding: 30px 24px;
            overflow-y: auto;
            position: relative;
            display: flex;
            flex-direction: column;
            box-shadow: 0 -10px 40px rgba(0,0,0,0.3);
        }}

        .track-info {{ margin-bottom: 25px; }}

        .track-title {{
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(to right, var(--text-main), var(--text-muted));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.3;
        }}

        .control-panel {{
            background: var(--surface);
            border-radius: 20px;
            padding: 20px;
            border: 1px solid var(--border);
            margin-bottom: 20px;
            transition: transform 0.2s;
        }}

        .control-panel:active {{ transform: scale(0.99); }}

        .panel-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            margin-bottom: 12px;
            font-weight: 700;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        /* Custom Sliders */
        .custom-slider {{
            width: 100%;
            height: 6px;
            background: rgba(125,125,125,0.15);
            border-radius: 10px;
            outline: none;
            -webkit-appearance: none;
            position: relative;
        }}

        .custom-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 22px;
            height: 22px;
            background: var(--primary);
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 0 4px var(--primary-glow);
            border: 2px solid var(--bg-body);
            transition: transform 0.1s;
        }}

        .custom-slider::-webkit-slider-thumb:active {{ transform: scale(1.2); }}

        .speed-presets {{
            display: flex;
            gap: 8px;
            margin-top: 15px;
        }}

        .speed-chip {{
            flex: 1;
            padding: 8px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            font-size: 0.8rem;
            color: var(--text-muted);
            text-align: center;
            cursor: pointer;
            border: 1px solid transparent;
            transition: 0.2s;
        }}

        .speed-chip.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}

        /* Quality Menu */
        #quality-menu {{
            display: none;
            margin-top: 10px;
            background: var(--bg-body);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
        }}

        .quality-opt {{
            padding: 12px;
            font-size: 0.9rem;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            display: flex;
            justify-content: space-between;
        }}

        .quality-opt:last-child {{ border-bottom: none; }}
        .quality-opt.active {{ background: rgba(79, 70, 229, 0.1); color: var(--primary); }}
        .quality-opt:hover {{ background: rgba(255,255,255,0.02); }}

        .action-grid {{
            margin-top: auto;
            display: grid;
            gap: 12px;
        }}

        .close-btn {{
            width: 100%;
            padding: 18px;
            border-radius: 16px;
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text-main);
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            cursor: pointer;
            transition: 0.2s;
        }}

        .close-btn:hover {{
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
            border-color: #ef4444;
        }}

        /* Theme Modal */
        .modal-overlay {{
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.8);
            backdrop-filter: blur(5px);
            z-index: 9000;
            display: none;
            opacity: 0;
            transition: 0.3s;
        }}
        .modal-overlay.active {{ opacity: 1; display: block; }}

        .bottom-sheet {{
            position: fixed;
            bottom: -100%;
            left: 0;
            width: 100%;
            background: var(--surface);
            border-radius: 30px 30px 0 0;
            padding: 30px;
            z-index: 9500;
            transition: bottom 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            border-top: 1px solid var(--border);
        }}
        .bottom-sheet.active {{ bottom: 0; }}

        .theme-row {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-top: 20px;
        }}

        .theme-card {{
            padding: 20px;
            border-radius: 16px;
            background: var(--bg-body);
            border: 2px solid var(--border);
            text-align: center;
            cursor: pointer;
        }}

        .theme-card.active {{ border-color: var(--primary); background: rgba(79, 70, 229, 0.05); }}

    </style>
</head>
<body>

    <!-- Main Application -->
    <div id="app-view">
        <header class="app-header">
            <div class="brand">
                <i class="fas fa-cube" style="color: var(--primary); margin-right: 8px;"></i>Hub
            </div>
            <button class="theme-toggle" onclick="toggleThemeModal()">
                <i class="fas fa-palette"></i>
            </button>
        </header>

        <div class="container">
            <!-- Header Info -->
            <div style="margin-bottom: 30px;">
                <h1 style="font-size: 1.8rem; font-weight: 700; margin-bottom: 8px;">{batch_name}</h1>
                <p style="color: var(--text-muted); font-size: 0.9rem;">
                    <i class="fas fa-user-circle"></i> Created by {credit_name}
                </p>
            </div>

            <!-- Stats -->
            <div class="stat-bar" id="stats-bar"></div>

            <!-- Content List -->
            <div id="content-list"></div>

            <div style="text-align: center; margin-top: 50px; opacity: 0.3; font-size: 0.8rem;">
                <i class="fas fa-shield-alt"></i> Secure Content Viewer
            </div>
        </div>
    </div>

    <!-- Enhanced Player View -->
    <div id="player-view">
        <div class="video-container">
            <video id="main-player" controls controlsList="nodownload" oncontextmenu="return false;" playsinline>
                Your browser does not support video.
            </video>
        </div>

        <div class="player-controls">
            <div class="track-info">
                <div class="track-title" id="player-title">Video Title</div>
                <div style="font-size: 0.85rem; color: var(--text-muted); display: flex; align-items: center; gap: 8px;">
                    <span style="background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.7rem;">SECURE</span>
                    <span><i class="fas fa-shield-alt"></i> No Downloads</span>
                </div>
            </div>

            <!-- Quality (Hidden if not HLS) -->
            <div class="control-panel" id="quality-panel" style="display:none;">
                <div class="panel-label" onclick="toggleQuality()" style="cursor: pointer;">
                    <span><i class="fas fa-cog"></i> Video Quality</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div id="quality-menu"></div>
            </div>

            <!-- Speed (Slider) -->
            <div class="control-panel">
                <div class="panel-label">
                    <span><i class="fas fa-tachometer-alt"></i> Speed</span>
                    <span id="speed-val" style="color: var(--primary);">1.0x</span>
                </div>
                <input type="range" class="custom-slider" min="0.25" max="3" step="0.05" value="1" oninput="updateSpeed(this.value)">

                <div class="speed-presets">
                    <div class="speed-chip" onclick="updateSpeed(1)">1.0x</div>
                    <div class="speed-chip" onclick="updateSpeed(1.5)">1.5x</div>
                    <div class="speed-chip" onclick="updateSpeed(2)">2.0x</div>
                    <div class="speed-chip" onclick="updateSpeed(3)">3.0x</div>
                </div>
            </div>

            <!-- Volume -->
            <div class="control-panel">
                <div class="panel-label" style="display: flex; justify-content: space-between;">
                    <span><i class="fas fa-volume-up"></i> Volume</span>
                    <span id="vol-display" style="color: var(--primary);">100%</span>
                </div>
                <input type="range" class="custom-slider" min="0" max="1" step="0.05" value="1" oninput="setVolume(this.value)">
            </div>

            <div class="action-grid">
                <button class="close-btn" onclick="closePlayer()">
                    <i class="fas fa-chevron-down"></i> Minimize Player
                </button>
            </div>
        </div>
    </div>

    <!-- Theme Sheet -->
    <div class="modal-overlay" id="modal-overlay" onclick="toggleThemeModal()"></div>
    <div class="bottom-sheet" id="theme-sheet">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
            <h3 style="font-size: 1.2rem;">Appearance</h3>
            <button onclick="toggleThemeModal()" style="background: none; border: none; font-size: 1.5rem; color: var(--text-muted);"><i class="fas fa-times"></i></button>
        </div>

        <div class="theme-row">
            <div class="theme-card active" onclick="setTheme('dark')">
                <i class="fas fa-moon" style="font-size: 1.5rem; margin-bottom: 10px;"></i>
                <div>Dark Dimmed</div>
            </div>
            <div class="theme-card" onclick="setTheme('midnight')">
                <i class="fas fa-meteor" style="font-size: 1.5rem; margin-bottom: 10px; color: #a855f7;"></i>
                <div>Midnight</div>
            </div>
            <div class="theme-card" onclick="setTheme('light')">
                <i class="fas fa-sun" style="font-size: 1.5rem; margin-bottom: 10px; color: #f59e0b;"></i>
                <div>Light Mode</div>
            </div>
        </div>
    </div>

    <script>
        // --- Data & Config ---
        const CONFIG = {{
            data: {encrypted_json}
        }};

        const state = {{
            theme: localStorage.getItem('theme') || 'dark'
        }};

        // --- Init ---
        function init() {{
            setTheme(state.theme);
            loadContent();
        }}

        // --- Crypto ---
        function decrypt(str) {{
            try {{
                return atob(str);
            }} catch (e) {{ return null; }}
        }}

        // --- Content Renderer ---
        function loadContent() {{
            const container = document.getElementById('content-list');
            const statsBar = document.getElementById('stats-bar');
            
            let stats = {{ video: 0, pdf: 0, image: 0, total: 0 }};

            for (const [category, items] of Object.entries(CONFIG.data)) {{
                // Section Title
                const title = document.createElement('div');
                title.className = 'section-title';
                title.innerText = category;
                container.appendChild(title);

                // Items
                items.forEach(item => {{
                    stats.total++;
                    if(item.type === 'VIDEO') stats.video++;
                    if(item.type === 'PDF') stats.pdf++;

                    const el = document.createElement('div');
                    el.className = 'content-card type-' + item.type.toLowerCase();
                    el.onclick = () => openItem(item);
                    
                    let iconClass = 'fas fa-file';
                    
                    if (item.type === 'VIDEO') iconClass = 'fas fa-play';
                    else if (item.type === 'PDF') iconClass = 'fas fa-file-pdf';
                    else if (item.type === 'IMAGE') iconClass = 'fas fa-image';

                    el.innerHTML = `
                        <div class="card-icon"><i class="${{iconClass}}"></i></div>
                        <div class="card-info">
                            <div class="card-title">${{item.title}}</div>
                            <div class="card-meta">
                                <span>${{item.type}}</span>
                                <i class="fas fa-chevron-right" style="margin-left: auto; opacity: 0.5;"></i>
                            </div>
                        </div>
                    `;
                    container.appendChild(el);
                }});
            }}

            // Render Stats
            statsBar.innerHTML = `
                <div class="stat-pill active"><i class="fas fa-layer-group"></i> All ${{stats.total}}</div>
                <div class="stat-pill"><i class="fas fa-video"></i> ${{stats.video}} Video</div>
                <div class="stat-pill"><i class="fas fa-file-pdf"></i> ${{stats.pdf}} PDF</div>
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
        let hls = null;

        function openPlayer(url, title) {{
            const view = document.getElementById('player-view');
            document.getElementById('player-title').textContent = title;

            // Reset state
            document.getElementById('quality-panel').style.display = 'none';
            document.getElementById('quality-menu').innerHTML = '';

            // Init HLS or Native
            if (Hls.isSupported() && url.includes('.m3u8')) {{
                if (hls) hls.destroy();
                hls = new Hls();
                hls.loadSource(url);
                hls.attachMedia(player);

                hls.on(Hls.Events.MANIFEST_PARSED, (event, data) => {{
                    if (data.levels.length > 1) {{
                        setupQualityControls(data.levels);
                    }}
                    player.play();
                }});
            }} else if (player.canPlayType('application/vnd.apple.mpegurl')) {{
                // Safari Native HLS
                player.src = url;
                player.play();
            }} else {{
                // Standard MP4
                player.src = url;
                player.play();
            }}

            // Show UI with animation
            view.style.display = 'flex';
            // Force reflow
            void view.offsetWidth;
            view.classList.add('active');
        }}

        function setupQualityControls(levels) {{
            const panel = document.getElementById('quality-panel');
            const menu = document.getElementById('quality-menu');
            panel.style.display = 'block';

            // Auto option
            let html = `<div class="quality-opt active" onclick="setQuality(-1, this)">
                <span>Auto</span>
                <i class="fas fa-check"></i>
            </div>`;

            levels.forEach((lvl, idx) => {{
                html += `<div class="quality-opt" onclick="setQuality(${{idx}}, this)">
                    <span>${{lvl.height}}p</span>
                    <i class="fas fa-check" style="opacity:0"></i>
                </div>`;
            }});

            menu.innerHTML = html;
        }}

        function setQuality(levelIndex, el) {{
            if (hls) hls.currentLevel = levelIndex;

            // UI Update
            document.querySelectorAll('.quality-opt').forEach(opt => {{
                opt.classList.remove('active');
                opt.querySelector('.fa-check').style.opacity = '0';
            }});
            el.classList.add('active');
            el.querySelector('.fa-check').style.opacity = '1';

            toggleQuality(); // Close menu
        }}

        function toggleQuality() {{
            const menu = document.getElementById('quality-menu');
            menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
        }}

        function closePlayer() {{
            const view = document.getElementById('player-view');
            view.classList.remove('active');

            // Wait for animation
            setTimeout(() => {{
                view.style.display = 'none';
                player.pause();
                player.src = '';
                if(hls) {{
                    hls.destroy();
                    hls = null;
                }}
            }}, 400);
        }}

        function updateSpeed(val) {{
            const rate = parseFloat(val);
            player.playbackRate = rate;
            document.getElementById('speed-val').textContent = rate + 'x';

            // Update slider if changed via buttons
            document.querySelector('.custom-slider').value = rate;

            // Highlight chips
            document.querySelectorAll('.speed-chip').forEach(c => {{
                c.classList.toggle('active', parseFloat(c.innerText) === rate);
            }});
        }}

        function setVolume(val) {{
            player.volume = val;
            document.getElementById('vol-display').textContent = Math.round(val * 100) + '%';
        }}

        // --- Theme Logic ---
        function toggleThemeModal() {{
            const sheet = document.getElementById('theme-sheet');
            const overlay = document.getElementById('modal-overlay');
            const isActive = sheet.classList.contains('active');

            if (isActive) {{
                sheet.classList.remove('active');
                overlay.classList.remove('active');
            }} else {{
                sheet.classList.add('active');
                overlay.classList.add('active');
            }}
        }}

        function setTheme(themeName) {{
            document.body.className = `theme-${{themeName}}`;
            localStorage.setItem('theme', themeName);

            // Update Active State
            document.querySelectorAll('.theme-card').forEach(card => {{
                const isMatch = card.textContent.toLowerCase().includes(themeName) ||
                               (themeName === 'midnight' && card.innerText.includes('Midnight'));

                // Simple logic for demo, better to rely on data attribute
                card.classList.remove('active');
                if(card.getAttribute('onclick').includes(themeName)) {{
                    card.classList.add('active');
                }}
            }});

            if (document.getElementById('theme-sheet').classList.contains('active')) {{
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
        "• 🎨 Premium Dark UI\n"
        "• 🎬 Advanced Video Player\n"
        "• 📱 App-like Experience\n"
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
        
        preview_text += "\n📚 Step 2: Batch Name\n\nBatch name enter करें:"
        
        await update.message.reply_text(preview_text)
        return BATCH_NAME
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {str(e)}\n\n"
            "कृपया valid TXT file भेजें!"
        )
        return TXT_FILE

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
