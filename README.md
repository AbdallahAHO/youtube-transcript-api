# YouTube Transcript Fetcher

A simple web application to fetch transcripts from YouTube videos using the YouTube Transcript API.

## Features

- Fetch transcripts from any YouTube video
- View available transcript languages
- Export transcripts as text or JSON
- Clean and modern UI
- Support for both auto-generated and manual transcripts
- Optional proxy support to bypass YouTube IP blocking

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Configure proxy to bypass YouTube blocking:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Webshare proxy credentials
# Get credentials from: https://dashboard.webshare.io/proxy/settings
```

## Proxy Configuration (Recommended)

YouTube blocks transcript fetching from many IPs. To reliably fetch transcripts, you'll need to use a proxy service.

### Using Webshare Proxies

1. Create a [Webshare account](https://www.webshare.io/?referral_code=w0xno53eb50g)
2. Purchase a "Residential" proxy package (NOT "Proxy Server" or "Static Residential")
3. Get your credentials from [Webshare Proxy Settings](https://dashboard.webshare.io/proxy/settings?referral_code=w0xno53eb50g)
4. Add credentials to `.env` file:

```env
WEBSHARE_PROXY_USERNAME=your_username_here
WEBSHARE_PROXY_PASSWORD=your_password_here
```

The app will automatically use proxies when credentials are configured. Without proxies, you can still list available transcripts but fetching may be blocked.

## Usage

1. Run the application:
```bash
python app.py
```

Or use the startup script:
```bash
./run.sh
```

2. Open your browser and navigate to:
```
http://localhost:9585
```

3. Paste a YouTube URL and click "Get Transcript" or "List Available Languages"

## API Endpoints

### Get Transcript
```
POST /api/transcript
Body: { "url": "youtube_url" }
```

### List Available Transcripts
```
POST /api/list-transcripts
Body: { "url": "youtube_url" }
```

## Supported URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- `VIDEO_ID` (direct video ID)

## Export Options

- **Text Format**: Plain text with timestamps
- **JSON Format**: Full transcript data including timing information

## Technologies Used

- Flask (Backend)
- YouTube Transcript API
- HTML/CSS/JavaScript (Frontend)
