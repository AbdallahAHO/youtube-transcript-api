from youtube_transcript_api import YouTubeTranscriptApi

# Test with a simple video
video_id = "dQw4w9WgXcQ"

try:
    print(f"Testing video: {video_id}")
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    print("\nAvailable transcripts:")
    for transcript in transcript_list:
        print(f"  - {transcript.language} ({transcript.language_code}) - Generated: {transcript.is_generated}")

    # Get first transcript
    transcript = next(iter(transcript_list))
    data = transcript.fetch()

    print(f"\nFetched {len(data)} segments from {transcript.language}")
    print(f"First segment: {data[0]}")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
