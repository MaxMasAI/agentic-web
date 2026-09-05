"""
downloader.py - Auto-download handler for multi-agent browser pipeline.
Intercepts Playwright browser downloads and saves them into
task-named subfolders inside the local 'downloads/' directory.
Also contains helpers to detect and trigger image/file downloads
from agent responses (e.g. DALL-E images in ChatGPT).
"""

import os
import re
import asyncio
import shutil

def make_task_folder(task: str) -> str:
    """
    Creates and returns a sanitized, task-named folder under downloads/.
    E.g. task='Create a logo for TechCorp' -> 'downloads/create_a_logo_for_techcorp/'
    """
    slug = re.sub(r"[^\w\s-]", "", task).strip().lower()
    slug = re.sub(r"[\s-]+", "_", slug)[:50]
    if not slug:
        slug = "task"
    folder = os.path.join("downloads", slug)
    os.makedirs(folder, exist_ok=True)
    return folder


def setup_download_handler(context, download_folder: str):
    """
    Attaches a global download event listener to the browser context.
    Every browser-initiated download (images, files, code) is
    automatically saved to the specified task download folder.
    """
    async def on_download(download):
        suggested = download.suggested_filename or "downloaded_file"
        dest_path = os.path.join(download_folder, suggested)

        # Avoid overwriting — append index if file already exists
        base, ext = os.path.splitext(dest_path)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = f"{base}_{counter}{ext}"
            counter += 1

        await download.save_as(dest_path)
        print(f"[↓] Download saved: {dest_path}")

    context.on("download", lambda d: asyncio.ensure_future(on_download(d)))
    print(f"[*] Download handler active → {download_folder}")


async def try_download_images(page, download_folder: str, agent_id: str):
    """
    Scans the current page for downloadable images (e.g. DALL-E generated images
    in ChatGPT) and clicks each available download button.
    Falls back to right-click saving if no button is found.
    """
    downloaded = 0

    # --- ChatGPT / DALL-E: look for download buttons on generated images ---
    if agent_id in ("chatgpt", "dalle"):
        # Hover over the generated image first to reveal the download button
        img_locators = page.locator("img[alt*='Generated'], img[src*='oaiusercontent'], .dalle-image img")
        count = await img_locators.count()
        for i in range(count):
            img = img_locators.nth(i)
            try:
                await img.hover(timeout=3000)
                await asyncio.sleep(0.5)
            except Exception:
                pass

        # Now look for download buttons (aria-label or title="Download")
        dl_buttons = page.locator(
            "button[aria-label*='Download'], button[title*='Download'], "
            "[data-testid*='download'], a[download]"
        )
        btn_count = await dl_buttons.count()
        for i in range(btn_count):
            try:
                async with page.expect_download(timeout=10000) as dl_info:
                    await dl_buttons.nth(i).click()
                dl = await dl_info.value
                suggested = dl.suggested_filename or f"image_{i}.png"
                dest = os.path.join(download_folder, suggested)
                base, ext = os.path.splitext(dest)
                c = 1
                while os.path.exists(dest):
                    dest = f"{base}_{c}{ext}"
                    c += 1
                await dl.save_as(dest)
                print(f"[↓] Image downloaded: {dest}")
                downloaded += 1
            except Exception:
                pass

        # Fallback: grab image src directly and save via JS fetch
        if downloaded == 0:
            img_srcs = await page.evaluate("""() => {
                const imgs = document.querySelectorAll(
                    'img[src*="oaiusercontent"], img[alt*="Generated"]'
                );
                return Array.from(imgs).map(img => img.src).filter(Boolean);
            }""")
            for idx, src in enumerate(img_srcs):
                try:
                    b64 = await page.evaluate(f"""async () => {{
                        const res = await fetch('{src}');
                        const buf = await res.arrayBuffer();
                        const b = btoa(String.fromCharCode(...new Uint8Array(buf)));
                        return b;
                    }}""")
                    import base64
                    img_bytes = base64.b64decode(b64)
                    fname = f"dalle_image_{idx+1}.png"
                    dest = os.path.join(download_folder, fname)
                    with open(dest, "wb") as f:
                        f.write(img_bytes)
                    print(f"[↓] Image saved via fetch fallback: {dest}")
                    downloaded += 1
                except Exception as e:
                    print(f"[!] Fetch fallback failed for image {idx}: {e}")

    # --- DeepSeek: code block copy/download ---
    elif agent_id == "deepseek":
        code_blocks = page.locator("pre code, div.ds-markdown code")
        count = await code_blocks.count()
        if count > 0:
            for i in range(count):
                try:
                    code_text = await code_blocks.nth(i).inner_text()
                    if code_text.strip():
                        fname = f"deepseek_code_{i+1}.txt"
                        dest = os.path.join(download_folder, fname)
                        with open(dest, "w", encoding="utf-8") as f:
                            f.write(code_text)
                        print(f"[↓] Code block saved: {dest}")
                        downloaded += 1
                except Exception:
                    pass

    return downloaded
