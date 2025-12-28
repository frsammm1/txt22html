# 🤖 TXT to HTML Converter Telegram Bot

Password-protected HTML generator bot with encrypted links and beautiful UI!

## 🌟 Features

- 🔒 **Password Protection**: HTML files are password-protected
- 🔐 **Link Encryption**: Links are encrypted and only work within the HTML
- 🎨 **4 Beautiful Themes**: Dark, Light, Ocean, Forest
- 🎬 **Video Player**: Built-in player with speed controls (0.5x to 2x)
- 📱 **Mobile Responsive**: Perfect UI for all devices
- 📊 **Smart Categories**: Auto-categorizes videos, PDFs, and other files
- ⚡ **Fast & Smooth**: Optimized performance

## 📋 Prerequisites

- Python 3.9+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Heroku Account

## 🚀 Heroku Deployment

### Method 1: Using Heroku CLI

1. **Install Heroku CLI**
   ```bash
   # Download from: https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create a new Heroku app**
   ```bash
   heroku create your-bot-name
   ```

4. **Set Bot Token**
   ```bash
   heroku config:set BOT_TOKEN="your_telegram_bot_token_here"
   ```

5. **Deploy**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push heroku master
   ```

6. **Scale the worker**
   ```bash
   heroku ps:scale worker=1
   ```

### Method 2: Using Heroku Dashboard

1. Go to [Heroku Dashboard](https://dashboard.heroku.com/)
2. Click **New** → **Create new app**
3. Enter app name and click **Create app**
4. Go to **Settings** → **Config Vars**
5. Add: `BOT_TOKEN` = `your_telegram_bot_token_here`
6. Go to **Deploy** tab
7. Connect your GitHub repository or use Heroku Git
8. Click **Deploy Branch**
9. Go to **Resources** tab
10. Turn on the **worker** dyno

## 🖥️ Local Testing

1. **Clone/Download the files**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variable**
   ```bash
   # Windows
   set BOT_TOKEN=your_bot_token_here
   
   # Linux/Mac
   export BOT_TOKEN=your_bot_token_here
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## 📝 File Structure

```
.
├── bot.py              # Main bot code
├── requirements.txt    # Python dependencies
├── Procfile           # Heroku configuration
└── README.md          # This file
```

## 🎯 How to Use

1. Start the bot: `/start`
2. Click **"📝 Create HTML"**
3. Enter password for HTML file
4. Enter batch name
5. Enter your credit name (e.g., @FR_SAMMM11)
6. Send your TXT file
7. Receive password-protected HTML file!

## 📄 TXT File Format

Your TXT file should be in this format:

```
[CATEGORY NAME]
Title 1: https://link1.com/video.mp4
Title 2: https://link2.com/document.pdf

[ANOTHER CATEGORY]
Title 3: https://link3.com/file.mp4
```

## 🔒 Security Features

- **Password Protection**: HTML files require password to access
- **Link Encryption**: All links are encrypted using password-based key
- **No External Access**: Encrypted links only work within the HTML file
- **Inspection Protection**: Links cannot be extracted through browser inspection

## 🎨 HTML Features

- **4 Themes**: Dark (default), Light, Ocean, Forest
- **Video Player**: 
  - Play/Pause controls
  - Speed adjustment (0.5x - 2x)
  - Full-screen support
  - Smooth modal interface
- **Statistics Dashboard**: Shows total items, videos, and PDFs
- **Category Organization**: Content organized by categories
- **Mobile Optimized**: Responsive design for all screen sizes

## 🐛 Troubleshooting

### Bot not responding
- Check if BOT_TOKEN is set correctly
- Ensure worker dyno is turned on in Heroku

### HTML file not opening
- Make sure you're entering the correct password
- Try opening in a different browser

### Links not working
- Links are encrypted and only work within the HTML file
- External access to links is blocked by design

## 💡 Tips

- Use strong passwords for better security
- Keep your HTML files safe
- The bot works best with organized TXT files
- Video links should be direct MP4 or M3U8 URLs

## 📞 Support

For issues or questions, contact the developer!

## 📜 License

Free to use and modify!

---

**Developed with ❤️ by @FR_SAMMM11**
