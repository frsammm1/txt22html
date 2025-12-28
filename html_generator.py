import json
from config import THEMES

def generate_html(categories, batch_name, credit_name, theme='dark'):
    """Generate modern HTML with selected theme"""
    
    theme_config = THEMES.get(theme, THEMES['dark'])
    content_json = json.dumps(categories)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{batch_name}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --bg-primary: {theme_config['bg_primary']};
            --bg-secondary: {theme_config['bg_secondary']};
            --bg-tertiary: {theme_config['bg_tertiary']};
            --text-primary: {theme_config['text_primary']};
            --text-secondary: {theme_config['text_secondary']};
            --text-muted: {theme_config['text_muted']};
            --accent: {theme_config['accent']};
            --accent-hover: {theme_config['accent_hover']};
            --gradient: {theme_config['gradient']};
            --border: {theme_config['border']};
            --success: {theme_config['success']};
            --warning: {theme_config['warning']};
            --danger: {theme_config['danger']};
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }}

        /* Animated Background */
        .bg-gradient {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background: var(--gradient);
            opacity: 0.05;
            animation: gradientMove 15s ease infinite;
        }}

        @keyframes gradientMove {{
            0%, 100% {{ transform: scale(1) rotate(0deg); }}
            50% {{ transform: scale(1.2) rotate(180deg); }}
        }}

        /* Header */
        .header {{
            background: var(--bg-secondary);
            backdrop-filter: blur(20px);
            padding: 40px 30px;
            border-radius: 25px;
            margin: 30px auto;
            max-width: 1400px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border);
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient);
        }}

        .developer-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid var(--accent);
            border-radius: 50px;
            color: var(--accent);
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 20px;
        }}

        .batch-title {{
            font-size: 3em;
            font-weight: 900;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}

        /* Search & Filters */
        .controls {{
            max-width: 1400px;
            margin: 30px auto;
            padding: 0 30px;
        }}

        .search-box {{
            position: relative;
            margin-bottom: 25px;
        }}

        .search-box input {{
            width: 100%;
            padding: 18px 60px 18px 25px;
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 15px;
            color: var(--text-primary);
            font-size: 16px;
            transition: all 0.3s;
        }}

        .search-box input:focus {{
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.2);
        }}

        .search-box i {{
            position: absolute;
            right: 25px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 20px;
        }}

        /* Filter Buttons */
        .filters {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 25px;
        }}

        .filter-btn {{
            padding: 12px 24px;
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 12px;
            color: var(--text-primary);
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .filter-btn:hover {{
            border-color: var(--accent);
            transform: translateY(-2px);
        }}

        .filter-btn.active {{
            background: var(--gradient);
            border-color: var(--accent);
            color: white;
        }}

        /* Stats Dashboard */
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto 30px;
            padding: 0 30px;
        }}

        .stat-card {{
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 20px;
            border: 1px solid var(--border);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}

        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--gradient);
            opacity: 0;
            transition: opacity 0.4s;
        }}

        .stat-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 20px 50px rgba(99, 102, 241, 0.3);
            border-color: var(--accent);
        }}

        .stat-card:hover::before {{
            opacity: 0.1;
        }}

        .stat-icon {{
            font-size: 2.5em;
            margin-bottom: 15px;
            position: relative;
            z-index: 1;
        }}

        .stat-number {{
            font-size: 3em;
            font-weight: 900;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
            position: relative;
            z-index: 1;
        }}

        .stat-label {{
            color: var(--text-muted);
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            z-index: 1;
        }}

        /* Content Container */
        .content {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 30px 50px;
        }}

        /* Category */
        .category {{
            background: var(--bg-secondary);
            padding: 35px;
            border-radius: 20px;
            margin-bottom: 25px;
            border: 1px solid var(--border);
            transition: all 0.3s;
            animation: fadeIn 0.6s ease-out;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .category:hover {{
            border-color: var(--accent);
        }}

        .category-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid var(--border);
        }}

        .category-title {{
            font-size: 1.8em;
            font-weight: 800;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .category-count {{
            padding: 8px 16px;
            background: var(--bg-tertiary);
            border-radius: 50px;
            color: var(--text-muted);
            font-weight: 600;
            font-size: 14px;
        }}

        /* Item */
        .item {{
            background: var(--bg-tertiary);
            padding: 20px 25px;
            border-radius: 15px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 20px;
            border: 2px solid transparent;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .item:hover {{
            border-color: var(--accent);
            transform: translateX(8px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.2);
        }}

        .item-icon {{
            font-size: 24px;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--bg-secondary);
            border-radius: 12px;
        }}

        .item-content {{
            flex: 1;
        }}

        .item-title {{
            font-weight: 600;
            font-size: 1.05em;
            margin-bottom: 5px;
        }}

        .item-type {{
            color: var(--text-muted);
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .item-badge {{
            padding: 8px 20px;
            border-radius: 50px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .badge-video {{ background: linear-gradient(135deg, #ef4444, #dc2626); color: white; }}
        .badge-pdf {{ background: linear-gradient(135deg, #f59e0b, #d97706); color: white; }}
        .badge-image {{ background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; }}
        .badge-other {{ background: linear-gradient(135deg, #6b7280, #4b5563); color: white; }}

        .item-btn {{
            padding: 12px 28px;
            background: var(--gradient);
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 700;
            font-size: 14px;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .item-btn:hover {{
            transform: scale(1.05);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
        }}

        /* Video Modal */
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.98);
            z-index: 10000;
            animation: fadeIn 0.3s;
        }}

        .modal-content {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 90px 30px 30px;
            height: 100%;
            display: flex;
            flex-direction: column;
        }}

        .modal-header {{
            position: fixed;
            top: 20px;
            left: 20px;
            right: 20px;
            padding: 20px 30px;
            background: var(--bg-secondary);
            backdrop-filter: blur(20px);
            border-radius: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid var(--border);
            z-index: 10001;
        }}

        .back-btn {{
            padding: 12px 28px;
            background: var(--gradient);
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 700;
            font-size: 15px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .back-btn:hover {{
            transform: scale(1.05);
        }}

        video {{
            width: 100%;
            border-radius: 15px;
            background: #000;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.7);
        }}

        .video-controls {{
            margin-top: 20px;
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
        }}

        .speed-btn {{
            padding: 12px 24px;
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 12px;
            color: var(--text-primary);
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }}

        .speed-btn:hover {{
            border-color: var(--accent);
        }}

        .speed-btn.active {{
            background: var(--gradient);
            border-color: var(--accent);
            color: white;
        }}

        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 80px 20px;
        }}

        .empty-state i {{
            font-size: 5em;
            color: var(--text-muted);
            margin-bottom: 20px;
        }}

        .empty-state p {{
            color: var(--text-muted);
            font-size: 1.2em;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .batch-title {{ font-size: 2em; }}
            .filters {{ justify-content: center; }}
            .item {{ flex-direction: column; align-items: flex-start; }}
            .item-btn {{ width: 100%; }}
        }}

        /* Loading Animation */
        .loading {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid var(--text-muted);
            border-radius: 50%;
            border-top-color: var(--accent);
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="bg-gradient"></div>

    <div class="header">
        <div class="developer-badge">
            <i class="fas fa-code"></i> {credit_name}
        </div>
        <div class="batch-title">{batch_name}</div>
    </div>

    <div class="controls">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 Search anything..." oninput="searchItems()">
            <i class="fas fa-search"></i>
        </div>

        <div class="filters">
            <button class="filter-btn active" onclick="filterByType('all')">
                <i class="fas fa-th"></i> All
            </button>
            <button class="filter-btn" onclick="filterByType('VIDEO')">
                <i class="fas fa-video"></i> Videos
            </button>
            <button class="filter-btn" onclick="filterByType('PDF')">
                <i class="fas fa-file-pdf"></i> PDFs
            </button>
            <button class="filter-btn" onclick="filterByType('IMAGE')">
                <i class="fas fa-image"></i> Images
            </button>
            <button class="filter-btn" onclick="filterByType('OTHER')">
                <i class="fas fa-file"></i> Others
            </button>
        </div>
    </div>

    <div class="stats" id="stats"></div>
    <div class="content" id="content"></div>

    <div class="modal" id="videoModal">
        <div class="modal-content">
            <div class="modal-header">
                <button class="back-btn" onclick="closeVideo()">
                    <i class="fas fa-arrow-left"></i> Back
                </button>
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
        const DATA = {content_json};
        let currentFilter = 'all';
        let currentSearch = '';

        function init() {{
            updateStats();
            renderContent();
        }}

        function updateStats() {{
            let totalItems = 0;
            let totalVideos = 0;
            let totalPDFs = 0;
            let totalImages = 0;

            Object.values(DATA).forEach(items => {{
                totalItems += items.length;
                items.forEach(item => {{
                    if (item.type === 'VIDEO') totalVideos++;
                    else if (item.type === 'PDF') totalPDFs++;
                    else if (item.type === 'IMAGE') totalImages++;
                }});
            }});

            document.getElementById('stats').innerHTML = `
                <div class="stat-card">
                    <div class="stat-icon">📦</div>
                    <div class="stat-number">${{totalItems}}</div>
                    <div class="stat-label">Total Items</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">🎬</div>
                    <div class="stat-number">${{totalVideos}}</div>
                    <div class="stat-label">Videos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">📄</div>
                    <div class="stat-number">${{totalPDFs}}</div>
                    <div class="stat-label">Documents</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">🖼️</div>
                    <div class="stat-number">${{totalImages}}</div>
                    <div class="stat-label">Images</div>
                </div>
            `;
        }}

        function getIcon(type) {{
            const icons = {{
                'VIDEO': 'fa-video',
                'PDF': 'fa-file-pdf',
                'IMAGE': 'fa-image',
                'OTHER': 'fa-file'
            }};
            return icons[type] || 'fa-file';
        }}

        function renderContent() {{
            const container = document.getElementById('content');
            container.innerHTML = '';

            let hasResults = false;

            Object.entries(DATA).forEach(([category, items]) => {{
                const filteredItems = items.filter(item => {{
                    const matchesFilter = currentFilter === 'all' || item.type === currentFilter;
                    const matchesSearch = !currentSearch || 
                        item.title.toLowerCase().includes(currentSearch.toLowerCase()) ||
                        category.toLowerCase().includes(currentSearch.toLowerCase());
                    return matchesFilter && matchesSearch;
                }});

                if (filteredItems.length === 0) return;
                hasResults = true;

                const categoryDiv = document.createElement('div');
                categoryDiv.className = 'category';
                
                categoryDiv.innerHTML = `
                    <div class="category-header">
                        <div class="category-title">${{category}}</div>
                        <div class="category-count">${{filteredItems.length}} items</div>
                    </div>
                `;

                filteredItems.forEach(item => {{
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'item';
                    
                    const badgeClass = `badge-${{item.type.toLowerCase()}}`;
                    const buttonText = item.type === 'VIDEO' ? 'Play' : 'Open';
                    const buttonIcon = item.type === 'VIDEO' ? 'fa-play' : 'fa-external-link-alt';
                    
                    itemDiv.innerHTML = `
                        <div class="item-icon">
                            <i class="fas ${{getIcon(item.type)}}"></i>
                        </div>
                        <div class="item-content">
                            <div class="item-title">${{item.title}}</div>
                            <div class="item-type">${{item.type}}</div>
                        </div>
                        <span class="item-badge ${{badgeClass}}">${{item.type}}</span>
                        <button class="item-btn" onclick='openItem(${{JSON.stringify(item)}})'>
                            <i class="fas ${{buttonIcon}}"></i> ${{buttonText}}
                        </button>
                    `;
                    
                    categoryDiv.appendChild(itemDiv);
                }});

                container.appendChild(categoryDiv);
            }});

            if (!hasResults) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <p>No items found</p>
                    </div>
                `;
            }}
        }}

        function filterByType(type) {{
            currentFilter = type;
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.closest('.filter-btn').classList.add('active');
            renderContent();
        }}

        function searchItems() {{
            currentSearch = document.getElementById('searchInput').value;
            renderContent();
        }}

        function openItem(item) {{
            if (item.type === 'VIDEO') {{
                document.getElementById('videoTitle').textContent = item.title;
                document.getElementById('videoPlayer').src = item.link;
                document.getElementById('videoModal').style.display = 'block';
            }} else {{
                window.open(item.link, '_blank');
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

        // Initialize on load
        init();
    </script>
</body>
</html>'''
    
    return html
