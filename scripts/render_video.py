"""Render a narrated 160-second demo from genuine app footage and screenshots."""
from __future__ import annotations

import re
import subprocess
import os
import sys
import wave
from pathlib import Path

import imageio_ffmpeg
import pyttsx3
import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "media" / "demo"
ASSETS, AUDIO, RAW, FINAL = (MEDIA / name for name in ("assets", "audio", "raw", "final"))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

SCENES = [
    (18, "A useful research answer needs more than confident writing. It needs a path back to the original evidence. EvidenceTrail is an AI research agent designed to make that path visible, from the first question to every cited source and every uncertainty in the final report."),
    (24, "We start with a practical question: what do recent studies say about heat pumps in cold climates? The question is entered in the real EvidenceTrail interface. Nebius Token Factory turns it into two focused searches, so the agent can examine different parts of the problem instead of relying on one broad query."),
    (30, "Tavily runs those queries against the live web. The research trace shows each search and how many usable results came back. For every result, the agent keeps the original URL and extracted content. It merges repeated URLs without losing their query history. Nebius then checks whether a material evidence gap calls for one more search. If it does, Tavily searches again."),
    (30, "Now the source material goes to Nebius for synthesis. The model receives only the retrieved titles, URLs, and snippets, with source IDs assigned by EvidenceTrail. Retrieved pages are treated as untrusted data. The model is asked to separate supported facts from inference, describe conflicting findings, and state what remains uncertain. This report comes from this live run, not a stored answer."),
    (14, "The report uses short citation IDs, such as S one. Each ID resolves to an original source URL you can open and inspect. Here we expand a real result and compare it with the passage Tavily returned."),
    (14, "This is the original public page behind the citation. EvidenceTrail rejects unknown IDs and unverified links before displaying a report. Downloadable JSON preserves the question, sources, model, and timestamped trace."),
    (20, "Behind the interface, the flow is explicit. The user asks a question. Nebius plans focused searches. Tavily retrieves evidence. EvidenceTrail deduplicates and checks for gaps. Nebius writes the synthesis. Citation validation runs before the answer reaches the user. Each step is visible in the trace."),
    (10, "EvidenceTrail. Research you can trace. The public repository includes the code, setup, tests, and honest limitations."),
]


def card(path: Path, title: str, subtitle: str, steps: list[str] | None = None, highlight: int = -1) -> None:
    im = Image.new("RGB", (1920, 1080), "#081120")
    d = ImageDraw.Draw(im)
    for y in range(1080):
        glow = int(23 * (1 - abs(y - 420) / 900))
        if glow > 0:
            d.line((0, y, 1920, y), fill=(8, 17 + glow // 3, 32 + glow))
    d.rounded_rectangle((124, 132, 140, 933), radius=8, fill="#4FE3C1")
    d.text((190, 195), title, font=ImageFont.truetype(FONT_BOLD, 85), fill="#F0F5FA")
    d.text((194, 340), subtitle, font=ImageFont.truetype(FONT, 39), fill="#AEC3D7")
    if steps:
        x, y = 190, 555
        for i, step in enumerate(steps):
            width = 210 if len(step) < 14 else 290
            active = i == highlight
            d.rounded_rectangle((x, y, x + width, y + 90), radius=20, fill="#4FE3C1" if active else "#172B43", outline="#4FE3C1", width=2)
            d.text((x + 18, y + 30), step, font=ImageFont.truetype(FONT_BOLD, 23), fill="#081120" if active else "#F0F5FA")
            x += width + 24
            if i == 2:
                x, y = 190, 700
    d.text((194, 940), "EVIDENCETRAIL  /  ODSC × NEBIUS", font=ImageFont.truetype(FONT_BOLD, 22), fill="#4FE3C1")
    im.save(path)


def architecture_animation(steps: list[str]) -> Path:
    frames = []
    for index in range(len(steps)):
        frame = ASSETS / f"architecture_{index + 1}.png"
        card(frame, "The research flow", "From live search to validated citations", steps, highlight=index)
        frames.append(frame)
    listing = RAW / "architecture_frames.txt"
    seconds = 20 / len(frames)
    listing.write_text("".join(f"file '{frame}'\nduration {seconds}\n" for frame in frames) + f"file '{frames[-1]}'\n")
    video = RAW / "architecture_animation.mp4"
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-t", "20", "-vf", "scale=1920:1080,format=yuv420p", "-r", "30", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", str(video)])
    return video


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int(seconds % 3600 // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def main() -> None:
    FINAL.mkdir(parents=True, exist_ok=True)
    raw = RAW / "app_run.webm"
    required = [ASSETS / name for name in ("02_report.png", "03_sources.png", "04_source_detail.png", "06_original_page.png")]
    if not raw.exists() or any(not p.exists() for p in required):
        raise RuntimeError("Actual app recording and report/source screenshots are required before rendering")
    card(ASSETS / "intro.png", "EvidenceTrail", "AI research with a visible evidence trail")
    architecture_steps = ["Question", "Nebius plan", "Tavily search", "Evaluate", "Nebius report", "Validate citations"]
    architecture_video = architecture_animation(architecture_steps)
    repo_url = os.getenv("REPO_URL", "").strip()
    if repo_url:
        response = requests.get(repo_url, timeout=15)
        if response.status_code != 200:
            raise RuntimeError("Repository URL is not publicly readable; cannot display it in video")
    card(ASSETS / "outro.png", "EvidenceTrail", repo_url or "Research you can trace")
    voice_model = AUDIO / "voices" / "en_US-lessac-medium.onnx"
    voice = None
    if not voice_model.exists():
        voice = pyttsx3.init()
        english = [v for v in voice.getProperty("voices") if "en-us" in v.id]
        if english:
            voice.setProperty("voice", english[0].id)
        voice.setProperty("rate", 155)
    srt = []
    parts = []
    offset = 0
    visuals = [ASSETS / "intro.png", raw, raw, ASSETS / "02_report.png", ASSETS / "04_source_detail.png", ASSETS / "06_original_page.png", architecture_video, ASSETS / "outro.png"]
    for i, ((seconds, narration), visual) in enumerate(zip(SCENES, visuals), 1):
        wav = AUDIO / f"scene_{i:02}.wav"
        spoken_text = narration.replace("Nebius", "Neh bee us").replace("Tavily", "Tah villy")
        if not wav.exists():
            if voice_model.exists():
                env = os.environ.copy()
                env["PYTHONPATH"] = str(ROOT / ".ttsdeps")
                subprocess.run([sys.executable, "-m", "piper", "-m", str(voice_model), "-f", str(wav)], input=spoken_text, text=True, check=True, env=env, capture_output=True)
            else:
                voice.save_to_file(spoken_text, str(wav))
                voice.runAndWait()
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", narration) if s.strip()]
        weights = [len(s.split()) for s in sentences]
        cursor = offset + 0.5
        with wave.open(str(wav)) as sample:
            spoken = min(sample.getnframes() / sample.getframerate(), seconds - 1)
        for sentence, weight in zip(sentences, weights):
            length = spoken * weight / sum(weights)
            srt.append(f"{len(srt)+1}\n{timestamp(cursor)} --> {timestamp(cursor+length)}\n{sentence}\n")
            cursor += length
        part = RAW / f"scene_{i:02}.mp4"
        if visual.suffix in {".webm", ".mp4"}:
            source_args = ["-stream_loop", "-1", "-i", str(visual)]
        else:
            source_args = ["-loop", "1", "-framerate", "30", "-i", str(visual)]
        run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *source_args, "-i", str(wav), "-t", str(seconds), "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p,fade=t=in:st=0:d=0.35,fade=t=out:st=" + str(seconds - .35) + ":d=0.35", "-af", "apad", "-r", "30", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", "-c:a", "aac", "-b:a", "160k", str(part)])
        parts.append(part)
        offset += seconds
    (ASSETS / "captions.srt").write_text("\n".join(srt))
    listing = RAW / "concat.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in parts))
    joined = RAW / "joined.mp4"
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(joined)])
    destination = FINAL / "EvidenceTrail_ODSC_Demo.mp4"
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(joined), "-vf", f"subtitles={ASSETS / 'captions.srt'}:force_style='FontName=DejaVu Sans,FontSize=17,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,MarginV=45'", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "copy", str(destination)])
    print(destination)
    print("Expected duration:", offset)


if __name__ == "__main__":
    main()
