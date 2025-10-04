#!/usr/bin/env python3
import logging
import os
import re
import sys

import yt_dlp
from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_restx import Api, Resource, fields
from youtube_transcript_api import (
    IpBlocked,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)
from youtube_transcript_api.proxies import WebshareProxyConfig

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Production configuration
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max request size
app.config["JSON_SORT_KEYS"] = False

# CORS configuration
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)

# Rate limiting configuration
limiter = Limiter(
    app=app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"], storage_uri="memory://"
)

# Configure Flask-RESTX
api = Api(
    app,
    version="1.0",
    title="YouTube Transcript API",
    description="A REST API for fetching YouTube video transcripts with support for multiple languages and proxy configuration",
    doc="/api/docs",
    prefix="/api",
)

# Create namespaces
ns_transcript = api.namespace("transcript", description="Transcript operations")
ns_health = api.namespace("health", description="Health check")

# In-memory cache for transcripts
# Structure: {video_id: {transcript_list: [...], transcripts: {lang_code: {...}}, metadata: {...}}}
transcript_cache = {}

# Define API models for Swagger documentation
transcript_request_model = api.model(
    "TranscriptRequest",
    {
        "url": fields.String(
            required=True, description="YouTube video URL", example="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ),
        "language": fields.String(required=False, description="Language code (optional)", example="en"),
    },
)

list_transcripts_request_model = api.model(
    "ListTranscriptsRequest",
    {
        "url": fields.String(
            required=True, description="YouTube video URL", example="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
    },
)

language_info_model = api.model(
    "LanguageInfo",
    {
        "language": fields.String(description="Language name"),
        "language_code": fields.String(description="Language code"),
        "is_generated": fields.Boolean(description="Whether transcript is auto-generated"),
        "is_translatable": fields.Boolean(description="Whether transcript can be translated"),
    },
)

transcript_segment_model = api.model(
    "TranscriptSegment",
    {
        "text": fields.String(description="Transcript text"),
        "start": fields.Float(description="Start time in seconds"),
        "duration": fields.Float(description="Duration in seconds"),
    },
)

video_metadata_model = api.model(
    "VideoMetadata",
    {
        "title": fields.String(description="Video title"),
        "channel": fields.String(description="Channel name"),
        "channel_id": fields.String(description="Channel ID"),
        "description": fields.String(description="Video description"),
        "duration": fields.Integer(description="Video duration in seconds"),
        "view_count": fields.Integer(description="View count"),
        "upload_date": fields.String(description="Upload date"),
        "thumbnail": fields.String(description="Thumbnail URL"),
    },
)

transcript_response_model = api.model(
    "TranscriptResponse",
    {
        "video_id": fields.String(description="Video ID"),
        "language": fields.String(description="Transcript language"),
        "language_code": fields.String(description="Language code"),
        "is_generated": fields.Boolean(description="Whether transcript is auto-generated"),
        "transcript": fields.List(fields.Nested(transcript_segment_model), description="Transcript segments"),
        "metadata": fields.Nested(video_metadata_model, description="Video metadata"),
        "available_languages": fields.List(fields.Nested(language_info_model), description="Available languages"),
        "from_cache": fields.Boolean(description="Whether loaded from cache"),
    },
)

list_transcripts_response_model = api.model(
    "ListTranscriptsResponse",
    {"transcripts": fields.List(fields.Nested(language_info_model), description="Available transcripts")},
)

error_model = api.model("Error", {"error": fields.String(description="Error message")})

health_response_model = api.model(
    "HealthResponse",
    {"status": fields.String(description="Health status"), "version": fields.String(description="API version")},
)


# Configure proxy if credentials are available
def get_youtube_api():
    """Create YouTubeTranscriptApi instance with optional proxy configuration"""
    proxy_username = os.getenv("WEBSHARE_PROXY_USERNAME")
    proxy_password = os.getenv("WEBSHARE_PROXY_PASSWORD")

    if proxy_username and proxy_password:
        proxy_config = WebshareProxyConfig(
            proxy_username=proxy_username,
            proxy_password=proxy_password,
        )
        return YouTubeTranscriptApi(proxy_config=proxy_config)

    # Return API without proxy if credentials not configured
    return YouTubeTranscriptApi()


def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", r"(?:embed\/)([0-9A-Za-z_-]{11})", r"^([0-9A-Za-z_-]{11})$"]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_video_metadata(video_id):
    """Fetch video metadata using yt-dlp"""
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

            return {
                "title": info.get("title", "Unknown Title"),
                "channel": info.get("uploader", "Unknown Channel"),
                "channel_id": info.get("channel_id", ""),
                "description": info.get("description", ""),
                "duration": info.get("duration", 0),
                "view_count": info.get("view_count", 0),
                "upload_date": info.get("upload_date", ""),
                "thumbnail": info.get("thumbnail", ""),
            }
    except Exception as e:
        print(f"Error fetching video metadata: {e}")
        return {
            "title": "YouTube Video",
            "channel": "Unknown Channel",
            "channel_id": "",
            "description": "",
            "duration": 0,
            "view_count": 0,
            "upload_date": "",
            "thumbnail": "",
        }


@app.route("/")
def index():
    return render_template("index.html")


@ns_health.route("")
class Health(Resource):
    @ns_health.doc("health_check")
    @ns_health.marshal_with(health_response_model)
    def get(self):
        """Health check endpoint"""
        return {"status": "healthy", "version": "1.0"}


@ns_transcript.route("")
class TranscriptResource(Resource):
    @limiter.limit("30 per minute")
    @ns_transcript.doc("get_transcript")
    @ns_transcript.expect(transcript_request_model, validate=True)
    @ns_transcript.marshal_with(transcript_response_model, code=200)
    @ns_transcript.response(400, "Invalid request", error_model)
    @ns_transcript.response(404, "Not found", error_model)
    @ns_transcript.response(429, "Too many requests", error_model)
    @ns_transcript.response(500, "Internal server error", error_model)
    def post(self):
        """Fetch transcript for a YouTube video"""
        logger.info("Transcript request received")
        return get_transcript_logic()


def get_transcript_logic():
    try:
        data = request.json
        url = data.get("url", "").strip()
        requested_language = data.get("language", None)  # Optional language parameter

        if not url:
            return {"error": "Please provide a YouTube URL"}, 400

        video_id = extract_video_id(url)
        if not video_id:
            return {"error": "Invalid YouTube URL"}, 400

        # Initialize cache for this video if not exists
        if video_id not in transcript_cache:
            transcript_cache[video_id] = {"transcript_list": None, "transcripts": {}, "metadata": None}

        # Get or fetch transcript list
        if transcript_cache[video_id]["transcript_list"] is None:
            ytt_api = get_youtube_api()
            transcript_list_obj = ytt_api.list(video_id)

            # Cache the transcript list
            available_transcripts = []
            for t in transcript_list_obj:
                available_transcripts.append(
                    {
                        "language": t.language,
                        "language_code": t.language_code,
                        "is_generated": t.is_generated,
                        "is_translatable": t.is_translatable,
                    }
                )
            transcript_cache[video_id]["transcript_list"] = available_transcripts
        else:
            # Use cached transcript list
            ytt_api = get_youtube_api()
            transcript_list_obj = ytt_api.list(video_id)

        # Determine which language to fetch
        if requested_language:
            # Check cache first
            if requested_language in transcript_cache[video_id]["transcripts"]:
                cached_transcript = transcript_cache[video_id]["transcripts"][requested_language]

                # Get video metadata (check cache first)
                if transcript_cache[video_id]["metadata"] is None:
                    video_metadata = get_video_metadata(video_id)
                    transcript_cache[video_id]["metadata"] = video_metadata
                    print(f"🌐 Video metadata fetched from API for video: {video_id}")
                else:
                    video_metadata = transcript_cache[video_id]["metadata"]
                    print(f"✅ Video metadata loaded from CACHE for video: {video_id}")

                return {
                    "video_id": video_id,
                    "language": cached_transcript["language"],
                    "language_code": cached_transcript["language_code"],
                    "is_generated": cached_transcript["is_generated"],
                    "transcript": cached_transcript["transcript"],
                    "metadata": video_metadata,
                    "available_languages": transcript_cache[video_id]["transcript_list"],
                    "from_cache": True,
                }

            # Fetch the requested language
            transcript = transcript_list_obj.find_transcript([requested_language])
        else:
            # Prioritize manual transcripts over generated ones
            # First, try to find any manual (non-generated) transcript
            manual_transcript = None
            generated_transcript = None

            for t in transcript_list_obj:
                if not t.is_generated and manual_transcript is None:
                    manual_transcript = t
                    break

            # If no manual transcript found, get first generated one
            if manual_transcript is None:
                for t in transcript_list_obj:
                    if t.is_generated:
                        generated_transcript = t
                        break

            # Use manual if available, otherwise use generated
            transcript = manual_transcript if manual_transcript else generated_transcript

            # Fallback to first available if none found (shouldn't happen)
            if transcript is None:
                transcript = next(iter(transcript_list_obj))

        # Check if this specific language is already cached
        lang_code = transcript.language_code
        was_cached = lang_code in transcript_cache[video_id]["transcripts"]

        if not was_cached:
            # Fetch the actual transcript data
            fetched_transcript = transcript.fetch()

            # Cache the transcript
            transcript_cache[video_id]["transcripts"][lang_code] = {
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "transcript": fetched_transcript.to_raw_data(),
            }

        # Get cached transcript
        cached_data = transcript_cache[video_id]["transcripts"][lang_code]

        # Get video metadata (check cache first)
        if transcript_cache[video_id]["metadata"] is None:
            video_metadata = get_video_metadata(video_id)
            transcript_cache[video_id]["metadata"] = video_metadata
            print(f"🌐 Video metadata fetched from API for video: {video_id}")
        else:
            video_metadata = transcript_cache[video_id]["metadata"]
            print(f"✅ Video metadata loaded from CACHE for video: {video_id}")

        # Format response
        response = {
            "video_id": video_id,
            "language": cached_data["language"],
            "language_code": cached_data["language_code"],
            "is_generated": cached_data["is_generated"],
            "transcript": cached_data["transcript"],
            "metadata": video_metadata,
            "available_languages": transcript_cache[video_id]["transcript_list"],
            "from_cache": was_cached,
        }

        return response

    except TranscriptsDisabled:
        return {"error": "Transcripts are disabled for this video"}, 400
    except NoTranscriptFound:
        return {"error": "No transcript found for this video"}, 404
    except VideoUnavailable:
        return {"error": "Video is unavailable"}, 404
    except (IpBlocked, RequestBlocked):
        return {"error": "Too many requests or IP blocked. Please try again later or configure proxy"}, 429
    except Exception as e:
        error_msg = str(e)
        if "no element found" in error_msg:
            return {
                "error": "YouTube blocked the request. This is a known limitation. "
                "The API works but YouTube blocks transcript fetching from certain IPs. "
                "Try using proxies or cookies as documented in the README."
            }, 403
        return {"error": f"An error occurred: {error_msg}"}, 500


@ns_transcript.route("/list")
class ListTranscriptsResource(Resource):
    @limiter.limit("60 per minute")
    @ns_transcript.doc("list_transcripts")
    @ns_transcript.expect(list_transcripts_request_model, validate=True)
    @ns_transcript.marshal_with(list_transcripts_response_model, code=200)
    @ns_transcript.response(400, "Invalid request", error_model)
    @ns_transcript.response(500, "Internal server error", error_model)
    def post(self):
        """List all available transcripts for a YouTube video"""
        logger.info("List transcripts request received")
        return list_transcripts_logic()


def list_transcripts_logic():
    try:
        data = request.json
        url = data.get("url", "").strip()

        if not url:
            return {"error": "Please provide a YouTube URL"}, 400

        video_id = extract_video_id(url)
        if not video_id:
            return {"error": "Invalid YouTube URL"}, 400

        # Initialize cache for this video if not exists
        if video_id not in transcript_cache:
            transcript_cache[video_id] = {"transcript_list": None, "transcripts": {}, "metadata": None}

        # Check cache first
        if transcript_cache[video_id]["transcript_list"] is not None:
            return {"transcripts": transcript_cache[video_id]["transcript_list"]}

        # List available transcripts
        ytt_api = get_youtube_api()
        transcript_list = ytt_api.list(video_id)

        transcripts = []
        for transcript in transcript_list:
            transcripts.append(
                {
                    "language": transcript.language,
                    "language_code": transcript.language_code,
                    "is_generated": transcript.is_generated,
                    "is_translatable": transcript.is_translatable,
                }
            )

        # Cache the transcript list
        transcript_cache[video_id]["transcript_list"] = transcripts

        return {"transcripts": transcripts}

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}, 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 9585))
    app.run(debug=True, host="0.0.0.0", port=port)
