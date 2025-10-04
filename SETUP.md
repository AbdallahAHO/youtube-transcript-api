# Setup Guide

## Quick Start (No Proxy)

```bash
cd youtube-transcript-api-example
source venv/bin/activate
python app.py
```

Visit http://localhost:9585

**Note:** Without proxy configuration, you can list available transcripts but YouTube may block actual transcript fetching.

## Full Setup with Proxy Support

### 1. Install Dependencies

```bash
cd youtube-transcript-api-example
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Webshare Proxy (Recommended)

To bypass YouTube's IP blocking and reliably fetch transcripts:

1. **Create Webshare Account**
   - Visit: https://www.webshare.io/?referral_code=w0xno53eb50g
   - Sign up for an account

2. **Purchase Residential Proxies**
   - Go to proxy plans
   - Select a **"Residential"** proxy package
   - **Important:** Do NOT purchase "Proxy Server" or "Static Residential"

3. **Get Your Credentials**
   - Visit: https://dashboard.webshare.io/proxy/settings?referral_code=w0xno53eb50g
   - Copy your "Proxy Username"
   - Copy your "Proxy Password"

4. **Configure the App**
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env and add your credentials
   nano .env
   ```

   Add your credentials:
   ```env
   WEBSHARE_PROXY_USERNAME=your_username_here
   WEBSHARE_PROXY_PASSWORD=your_password_here
   ```

### 3. Run the Application

```bash
# Using the startup script
./run.sh

# Or manually
source venv/bin/activate
python app.py
```

### 4. Access the App

Open your browser and navigate to:
```
http://localhost:9585
```

## Testing

Try these URLs:
- https://www.youtube.com/watch?v=dQw4w9WgXcQ
- https://www.youtube.com/watch?v=bJsjuhOONh4

## Troubleshooting

### "YouTube blocked the request" error
- You need to configure proxy credentials in `.env`
- Make sure you purchased "Residential" proxies, not "Proxy Server"

### Import errors
- Make sure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Port already in use
- The app runs on port 9585
- Kill existing process: `lsof -ti:9585 | xargs kill -9`

## Features Without Proxy

Even without proxy configuration, you can:
- List available transcript languages for any video
- See which transcripts are auto-generated vs manual
- View the app's UI and functionality

## Features With Proxy

With proxy configuration:
- Fetch complete transcripts
- Export transcripts as text or JSON
- View timestamps for each segment
- Full functionality without IP blocking
