# 🎨 Ultra Modern HTML Generator Bot

A beautiful Telegram bot that converts TXT files into stunning, interactive HTML pages!

## ✨ Features

### 🎨 **6 Stunning Themes**
- 🌙 **Dark Mode** - Sleek and modern
- ☀️ **Light Mode** - Clean and bright  
- 🌊 **Ocean Blue** - Calm and serene
- 🌅 **Sunset** - Warm and vibrant
- 🌲 **Forest** - Natural and fresh
- 🎮 **Cyberpunk** - Futuristic and bold

### 🚀 **Advanced Features**
- 🔍 **Smart Search** - Find anything instantly
- 📊 **Advanced Filters** - Filter by type (Videos, PDFs, Images, etc.)
- 🎬 **Video Player** - Built-in player with speed controls (0.5x - 2x)
- 📱 **100% Responsive** - Perfect on all devices
- ⚡ **Lightning Fast** - Handles 1000+ links effortlessly
- 🎯 **Smart Detection** - Auto-categorizes content
- 📈 **Statistics Dashboard** - Real-time stats

## 📁 Project Structure

```
.
├── bot.py              # Main bot handler
├── html_generator.py   # HTML generation with themes
├── parser.py           # TXT file parser
├── config.py           # Theme configurations
├── requirements.txt    # Dependencies
├── Procfile           # Heroku config
├── runtime.txt        # Python version
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## 🚀 Deployment

### Heroku Deployment

1. **Create Heroku App**
   ```bash
   heroku create your-app-name
   ```

2. **Set Bot Token**
   ```bash
   heroku config:set BOT_TOKEN="your_telegram_bot_token"
   ```

3. **Deploy**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push heroku master
   ```

4. **Scale Worker**
   ```bash
   heroku ps:scale worker=1
   ```

### Local Testing

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variable**
   ```bash
   # Windows
   set BOT_TOKEN=your_token_here
   
   # Linux/Mac
   export BOT_TOKEN=your_token_here
   ```

3. **Run Bot**
   ```bash
   python bot.py
   ```

## 🎯 How to Use

1. Start the bot: `/start`
2. Click **"🚀 Create HTML"**
3. Send your TXT file
4. Enter batch name
5. Enter credit name
6. Choose your favorite theme
7. Get your beautiful HTML!

## 📝 TXT Format

```
[Category Name]
Title 1: https://example.com/video.mp4
Title 2: https://example.com/document.pdf

[Another Category]
Title 3: https://example.com/image.jpg
```

## 🎨 HTML Features

### Interface
- Modern glassmorphism design
- Smooth animations
- Beautiful gradients
- Responsive layout

### Functionality
- **Search Bar** - Real-time search
- **Filter Buttons** - Filter by content type
- **Category Organization** - Auto-organized content
- **Statistics Cards** - Visual stats
- **Video Player** - Built-in player with controls
- **Speed Control** - 0.5x to 2x playback
- **Mobile Optimized** - Works perfectly on phones

## 🛠️ Tech Stack

- **Backend**: Python 3.11
- **Bot Framework**: python-telegram-bot 20.7
- **Frontend**: Pure HTML/CSS/JavaScript
- **Design**: Modern glassmorphism with animations
- **Icons**: Font Awesome 6.4
- **Deployment**: Heroku

## 💡 Tips

- Use descriptive batch names
- Choose the theme that matches your content
- Video links should be direct MP4 or M3U8 URLs
- Keep your TXT file well-organized with categories
- The bot handles spaces in URLs perfectly

## 🎭 Themes Preview

Each theme has unique:
- Color schemes
- Gradients
- Animations
- Visual effects

Pick the one that best suits your content!

## 📊 Statistics

The HTML includes:
- Total items count
- Videos count
- Documents count
- Images count

## 🔧 Customization

### Adding More Themes
Edit `config.py` and add your theme configuration:

```python
'your_theme': {
    'name': '🎨 Your Theme',
    'bg_primary': '#color',
    'bg_secondary': '#color',
    # ... more colors
}
```

### Modifying HTML
Edit `html_generator.py` to customize:
- Layout
- Components
- Features
- Styling

## 🐛 Troubleshooting

### Bot not responding
- Check BOT_TOKEN is set correctly
- Ensure worker dyno is running
- Check Heroku logs: `heroku logs --tail`

### HTML not rendering
- Verify TXT file format
- Check if URLs are valid
- Try different browser

## 📞 Support

For issues or suggestions, contact the developer!

## 🌟 Future Updates

- [ ] More themes
- [ ] Playlist support
- [ ] Sorting options
- [ ] Export to PDF
- [ ] Dark/Light mode toggle in HTML
- [ ] Custom theme creator

## 📜 License

Free to use and modify!

---

**Made with ❤️ and ✨ by @FR_SAMMM11**

*Beautiful. Modern. Fast.*
