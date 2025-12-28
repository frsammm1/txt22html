import re

def detect_file_type(link):
    """Detect file type from URL"""
    link_lower = link.lower()
    
    video_ext = ['.m3u8', '.ts', '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp']
    image_ext = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
    doc_ext = ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx']
    
    if any(ext in link_lower for ext in video_ext):
        return 'VIDEO'
    
    if any(x in link_lower for x in ['youtube.com', 'youtu.be', '/watch', 'stream', '/video/']):
        return 'VIDEO'
    
    if any(ext in link_lower for ext in image_ext):
        return 'IMAGE'
    
    if any(ext in link_lower for ext in doc_ext):
        return 'PDF'
    
    return 'OTHER'

def parse_txt_content(content):
    """Parse TXT content and extract categorized links"""
    lines = content.strip().split('\n')
    categories = {}
    default_category = "Uncategorized"
    
    for line in lines:
        line = line.strip()
        
        # Skip empty or header lines
        if not line or 'CONTENT EXPORT' in line or line.startswith('ID:') or line.startswith('==='):
            continue
        
        # Must contain URL
        if 'http://' not in line and 'https://' not in line:
            continue
        
        # Method 1: [CATEGORY] Title: URL
        category_match = re.match(r'^\[([^\]]+)\]\s*(.+?):\s*(https?://.+)$', line)
        
        if category_match:
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
        
        # Method 2: Title: URL
        if ':' in line:
            http_pos = line.find('http://')
            https_pos = line.find('https://')
            
            url_start = -1
            if http_pos != -1 and https_pos != -1:
                url_start = min(http_pos, https_pos)
            elif http_pos != -1:
                url_start = http_pos
            elif https_pos != -1:
                url_start = https_pos
            
            if url_start != -1:
                url = line[url_start:].strip()
                text_before = line[:url_start].strip()
                
                category = default_category
                cat_match = re.match(r'^\[([^\]]+)\]\s*(.+)', text_before)
                if cat_match:
                    category = cat_match.group(1).strip()
                    text_before = cat_match.group(2).strip()
                
                title = text_before.rstrip(':').strip()
                file_type = detect_file_type(url)
                
                if category not in categories:
                    categories[category] = []
                
                categories[category].append({
                    'title': title if title else "Untitled",
                    'link': url,
                    'type': file_type
                })
                continue
        
        # Method 3: Extract all URLs as fallback
        urls = re.findall(r'https?://\S+', line)
        if urls:
            for idx, url in enumerate(urls):
                url_pos = line.find(url)
                title = line[:url_pos].strip()
                
                title = re.sub(r'^\[([^\]]+)\]\s*', '', title)
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
    
    return categories
