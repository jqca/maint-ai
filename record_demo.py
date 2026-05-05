"""
MaintAI Demo Video Recorder
Records a 30-second demo showing all 4 pages of the MaintAI app.
Uses the live Railway URL for reliability.
"""
import asyncio
import subprocess
import sys
import os
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "video_output"
OUTPUT_DIR.mkdir(exist_ok=True)
WEBM_PATH = OUTPUT_DIR / "maint_ai_demo.webm"
MP4_PATH = OUTPUT_DIR / "maint_ai_x_post_30s.mp4"

# Use Railway URL for reliable recording
URL = "https://maint-ai-production.up.railway.app"

async def record():
    from playwright.async_api import async_playwright

    print(f"Recording demo from {URL}")
    print(f"Output: {MP4_PATH}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(OUTPUT_DIR),
            record_video_size={"width": 1280, "height": 720},
            device_scale_factor=1,
        )
        page = await context.new_page()

        # ── Page 1: OEEダッシュボード ───────────────────────────────
        print("→ Page 1: OEEダッシュボード")
        await page.goto(URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_selector(".kpi-card", timeout=10000)
        # 75%ズームで画面下部を見切れなくする
        await page.evaluate("document.body.style.zoom = '0.75'")
        await asyncio.sleep(2.5)  # Show KPI counters animate

        # Slow scroll to show charts
        await page.evaluate("window.scrollTo({top: 200, behavior: 'smooth'})")
        await asyncio.sleep(1.5)
        await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        await asyncio.sleep(0.5)

        # ── Page 2: AI故障予測 ──────────────────────────────────────
        print("→ Page 2: AI故障予測")
        await page.click("text=AI故障予測")
        await asyncio.sleep(0.8)

        # Click critical machine HP-800 (class: mach-btn critical)
        await page.click(".mach-btn.critical")
        await asyncio.sleep(0.5)

        # Run AI prediction
        await page.click("#pred-btn")
        await asyncio.sleep(5.5)  # Full animation sequence (~4.6s + buffer)

        # ── Page 3: 設備監視 ───────────────────────────────────────
        print("→ Page 3: 設備監視")
        await page.click("text=設備監視")
        await asyncio.sleep(1.0)
        # Scroll to show machine grid
        await page.evaluate("window.scrollTo({top: 150, behavior: 'smooth'})")
        await asyncio.sleep(1.5)
        await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        await asyncio.sleep(0.5)

        # ── Page 4: 保全カレンダー ─────────────────────────────────
        print("→ Page 4: 保全カレンダー")
        await page.click("text=保全カレンダー")
        await asyncio.sleep(1.5)
        # Hover over an event for effect
        try:
            urgent = page.locator(".cal-event.urgent").first
            await urgent.hover()
            await asyncio.sleep(1.0)
        except Exception:
            pass
        await asyncio.sleep(2.0)

        # Return to dashboard for finale
        await page.click("text=OEEダッシュボード")
        await asyncio.sleep(2.0)

        print("Recording complete. Closing browser...")
        await context.close()
        await browser.close()

    # Rename the generated .webm to known path
    webm_files = sorted(OUTPUT_DIR.glob("*.webm"), key=lambda f: f.stat().st_mtime, reverse=True)
    if webm_files:
        latest = webm_files[0]
        if latest != WEBM_PATH:
            WEBM_PATH.unlink(missing_ok=True)  # 既存ファイルを先に削除（Windows対応）
            latest.rename(WEBM_PATH)
        print(f"WebM saved: {WEBM_PATH} ({WEBM_PATH.stat().st_size // 1024}KB)")
    else:
        print("ERROR: No WebM file generated!")
        return False
    return True

def convert_to_mp4():
    """Convert WebM to MP4 using imageio-ffmpeg."""
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        print("imageio-ffmpeg not installed. Trying system ffmpeg...")
        ffmpeg = "ffmpeg"

    cmd = [
        ffmpeg, "-y",
        "-i", str(WEBM_PATH),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1280:720",
        "-r", "30",
        "-an",  # no audio
        str(MP4_PATH)
    ]
    print(f"Converting: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        size_kb = MP4_PATH.stat().st_size // 1024
        print(f"OK MP4 saved: {MP4_PATH} ({size_kb}KB)")
        return True
    else:
        print(f"Conversion failed: {result.stderr[-500:]}")
        return False

def main():
    # Run recording
    ok = asyncio.run(record())
    if not ok:
        sys.exit(1)

    # Convert to MP4
    ok = convert_to_mp4()
    if not ok:
        print("MP4 conversion failed — WebM file is available as fallback.")

    print("\n=== Done ===")
    print(f"WebM: {WEBM_PATH}")
    if MP4_PATH.exists():
        print(f"MP4:  {MP4_PATH}")
        print(f"Size: {MP4_PATH.stat().st_size // 1024}KB")

if __name__ == "__main__":
    main()
