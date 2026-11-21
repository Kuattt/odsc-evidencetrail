"""Render a narrated 160-second demo from genuine app footage and screenshots."""
from __future__ import annotations

import re
import subprocess
import os
import sys
from pathlib import Path

import imageio_ffmpeg
import pyttsx3
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "media" / "demo"
ASSETS, AUDIO, RAW, FINAL = (MEDIA / name for name in ("assets", "audio", "raw", "final"))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

SCENES = [
    (18, "Research questions are easy to ask. Trustworthy answers are harder. EvidenceTrail follows every claim back to a real source, so the path from question to conclusion stays visible."),
    (24, "Here is a real question about heat pumps in cold climates. The application sends it to Nebius Token Factory, which plans two focused searches. The plan is shown as the run happens."),
    (30, "Tavily searches the live web for each query. The agent records the exact query, original URL, extracted content, and result count. Duplicate URLs are merged. If the evidence leaves a material gap, the agent searches again."),
    (30, "Nebius then evaluates the retrieved evidence and writes a concise report. It is instructed to distinguish supported facts from inference, identify disagreement, and describe uncertainty. This report is generated from the sources shown here, not a prepared answer."),
    (28, "A citation like S one maps to a retrieved source URL. Open the source to inspect its original page and the passage returned by Tavily. EvidenceTrail rejects any citation ID that was never retrieved, and keeps a downloadable JSON trace of the run."),
    (20, "The architecture is simple: Nebius plans. Tavily searches. EvidenceTrail evaluates and deduplicates. Nebius synthesizes. A final validator checks citations before the report appears."),
    (10, "EvidenceTrail. Research you can trace. Explore the public repository for code, setup, and limitations."),
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
    raw = sorted(RAW.glob("*.webm"), key=lambda p: p.stat().st_mtime)
    required = [ASSETS / name for name in ("02_report.png", "03_sources.png")]
    if not raw or any(not p.exists() for p in required):
        raise RuntimeError("Actual app recording and report/source screenshots are required before rendering")
    card(ASSETS / "intro.png", "EvidenceTrail", "AI research with a visible evidence trail")
    architecture_steps = ["Question", "Nebius plan", "Tavily search", "Evaluate", "Nebius report", "Validate citations"]
    architecture_video = architecture_animation(architecture_steps)
    card(ASSETS / "outro.png", "EvidenceTrail", "Research you can trace")
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
    visuals = [ASSETS / "intro.png", raw[-1], raw[-1], ASSETS / "02_report.png", ASSETS / "03_sources.png", architecture_video, ASSETS / "outro.png"]
    for i, ((seconds, narration), visual) in enumerate(zip(SCENES, visuals), 1):
        wav = AUDIO / f"scene_{i:02}.wav"
        spoken_text = narration.replace("Nebius", "Neh bee us").replace("Tavily", "Tah villy")
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
        spoken = seconds - 2
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
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(joined), "-vf", f"subtitles={ASSETS / 'captions.srt'}:force_style='FontName=DejaVu Sans,FontSize=26,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,MarginV=60'", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "copy", str(destination)])
    print(destination)
    print("Expected duration:", offset)


if __name__ == "__main__":
    main()
