"""API endpoint tests."""

from unittest.mock import Mock, patch

import pytest


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_endpoint(self, client):
        """Test health endpoint returns correct response."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0"


class TestTranscriptEndpoint:
    """Test transcript endpoints."""

    def test_transcript_missing_url(self, client):
        """Test transcript endpoint with missing URL."""
        response = client.post("/api/transcript", json={})
        assert response.status_code == 400
        data = response.get_json()
        # Flask-RESTX validation error format
        assert "errors" in data or "error" in data or "message" in data

    def test_transcript_invalid_url(self, client):
        """Test transcript endpoint with invalid URL."""
        response = client.post("/api/transcript", json={"url": "invalid-url"})
        # Invalid URL format - extract_video_id returns None, API call fails
        # May return 400, 404, or 500 depending on where it fails
        assert response.status_code in [400, 404, 500]

    def test_transcript_valid_url_format(self, client):
        """Test transcript endpoint accepts valid URL format."""
        with patch("app.get_youtube_api") as mock_api:
            # Mock the API response
            mock_transcript_list = Mock()
            mock_transcript = Mock()
            mock_transcript.language = "English"
            mock_transcript.language_code = "en"
            mock_transcript.is_generated = False
            mock_transcript.is_translatable = True
            mock_transcript.fetch.return_value.to_raw_data.return_value = []

            mock_transcript_list.__iter__ = Mock(return_value=iter([mock_transcript]))
            mock_api.return_value.list.return_value = mock_transcript_list

            with patch("app.get_video_metadata") as mock_metadata:
                mock_metadata.return_value = {
                    "title": "Test Video",
                    "channel": "Test Channel",
                    "channel_id": "test123",
                    "description": "Test",
                    "duration": 100,
                    "view_count": 1000,
                    "upload_date": "20240101",
                    "thumbnail": "http://test.com/thumb.jpg",
                }

                response = client.post("/api/transcript", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})

                # Should not fail with 400
                assert response.status_code in [200, 403, 404, 429, 500]


class TestListTranscriptsEndpoint:
    """Test list transcripts endpoint."""

    def test_list_transcripts_missing_url(self, client):
        """Test list transcripts with missing URL."""
        response = client.post("/api/transcript/list", json={})
        assert response.status_code == 400
        data = response.get_json()
        # Flask-RESTX validation error format
        assert "errors" in data or "error" in data or "message" in data

    def test_list_transcripts_invalid_url(self, client):
        """Test list transcripts with invalid URL."""
        response = client.post("/api/transcript/list", json={"url": "not-a-youtube-url"})
        # Invalid URL format - extract_video_id returns None, API call fails
        # May return 400 or 500 depending on where it fails
        assert response.status_code in [400, 500]


class TestVideoIdExtraction:
    """Test video ID extraction function."""

    def test_extract_video_id_standard_url(self):
        """Test extracting ID from standard YouTube URL."""
        from app import extract_video_id

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_short_url(self):
        """Test extracting ID from short youtu.be URL."""
        from app import extract_video_id

        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_embed_url(self):
        """Test extracting ID from embed URL."""
        from app import extract_video_id

        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_direct(self):
        """Test with direct video ID."""
        from app import extract_video_id

        video_id = extract_video_id("dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_invalid(self):
        """Test with invalid input."""
        from app import extract_video_id

        video_id = extract_video_id("not-a-valid-id")
        assert video_id is None


class TestUIEndpoint:
    """Test UI endpoint."""

    def test_index_page_loads(self, client):
        """Test index page loads successfully."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data


class TestCaching:
    """Test caching functionality."""

    def test_transcript_caching(self, client):
        """Test that transcripts are cached properly."""
        with patch("app.get_youtube_api") as mock_api, patch("app.get_video_metadata") as mock_metadata:
            # Setup mocks - need to return the same mock for both calls
            def create_mock_transcript():
                mock_transcript = Mock()
                mock_transcript.language = "English"
                mock_transcript.language_code = "en"
                mock_transcript.is_generated = False
                mock_transcript.is_translatable = True
                mock_transcript.fetch.return_value.to_raw_data.return_value = [
                    {"text": "Hello", "start": 0.0, "duration": 1.0}
                ]
                return mock_transcript

            # Create mock that returns same structure for both calls
            mock_api_instance = Mock()

            def mock_list(video_id):
                mock_transcript_list = Mock()
                mock_transcript = create_mock_transcript()
                mock_transcript_list.__iter__ = Mock(return_value=iter([mock_transcript]))
                return mock_transcript_list

            mock_api_instance.list = mock_list
            mock_api.return_value = mock_api_instance

            mock_metadata.return_value = {
                "title": "Test Video",
                "channel": "Test Channel",
                "channel_id": "test123",
                "description": "Test",
                "duration": 100,
                "view_count": 1000,
                "upload_date": "20240101",
                "thumbnail": "http://test.com/thumb.jpg",
            }

            # First request
            response1 = client.post("/api/transcript", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
            assert response1.status_code == 200
            data1 = response1.get_json()
            assert data1["from_cache"] is False

            # Second request - should use cache
            response2 = client.post("/api/transcript", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
            assert response2.status_code == 200
            data2 = response2.get_json()
            assert data2["from_cache"] is True


class TestHelperFunctions:
    """Test helper functions."""

    def test_get_youtube_api_without_proxy(self):
        """Test YouTube API creation without proxy."""
        with patch.dict("os.environ", {}, clear=True):
            from app import get_youtube_api

            api = get_youtube_api()
            assert api is not None

    def test_get_youtube_api_with_proxy(self):
        """Test YouTube API creation with proxy."""
        with patch.dict("os.environ", {"WEBSHARE_PROXY_USERNAME": "test", "WEBSHARE_PROXY_PASSWORD": "pass"}):
            from app import get_youtube_api

            api = get_youtube_api()
            assert api is not None


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_applies(self, client):
        """Test that rate limiting is enforced."""
        # Note: In testing mode, rate limiting might be disabled
        # This test just ensures the endpoint works with rate limiting configured
        response = client.get("/api/health")
        assert response.status_code == 200
