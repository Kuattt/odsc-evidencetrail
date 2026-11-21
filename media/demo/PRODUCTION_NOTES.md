# Production notes

Status: planned. No live app footage or final video has been created yet.

- Required: actual Streamlit run, successful Nebius and Tavily calls, captured report and original source URLs.
- Output target: H.264 MP4, 1920 × 1080, 16:9, 120–180 seconds with narration and captions.
- Never record credentials or browser account pages. Capture only the application and public source pages.
- Use original graphics and local Piper neural TTS (`en_US-lessac-medium` from the official `rhasspy/piper-voices` repository) for narration; no copyrighted music. The model and generated audio stay out of Git.
- `scripts/record_app.py` captures actual Streamlit browser interaction through Chrome/Playwright. `scripts/render_video.py` assembles a 160-second draft after the integration succeeds.
- Video dependencies are listed in `requirements-video.txt`. The locally downloaded Piper voice model is `rhasspy/piper-voices/en/en_US/lessac/medium/en_US-lessac-medium.onnx` with its matching JSON configuration.
