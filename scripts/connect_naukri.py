#!/usr/bin/env python3
"""
One-time Naukri login helper.

It opens a visible Chromium window. Log in manually. When you're done,
press Enter in the terminal. The saved storage state is written to
./browser_sessions/<user_id>_naukri.json, which is already mounted into
the browser-worker container.
"""
import asyncio
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


SESSION_DIR = Path(__file__).resolve().parent.parent / "browser_sessions"
NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"


async def main() -> None:
    user_id_raw = input("User ID (from your database users.id): ").strip()
    if not user_id_raw.isdigit():
        print("User ID must be a number.")
        sys.exit(1)
    user_id = int(user_id_raw)

    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SESSION_DIR / f"{user_id}_naukri.json"

    if out_path.exists():
        overwrite = input(f"{out_path} already exists. Overwrite? [y/N]: ").strip().lower()
        if overwrite != "y":
            print("Aborted.")
            return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"Opening {NAUKRI_LOGIN_URL}")
        print("Log in manually. If a CAPTCHA or OTP appears, solve it in the browser.")
        await page.goto(NAUKRI_LOGIN_URL)

        input("\nWhen you are fully logged in and see the Naukri homepage, press Enter here... ")

        # Sanity check: confirm we're actually on naukri.com
        current_url = page.url
        if "naukri.com" not in current_url:
            print(f"Warning: current URL is {current_url}. Saving anyway.")

        await context.storage_state(path=str(out_path))
        await browser.close()

    print(f"\n✅ Saved session to: {out_path}")
    print(f"   Size: {out_path.stat().st_size} bytes")
    print("\nThe browser-worker container can now use this session.")
    print("If your session expires, re-run this script.")


if __name__ == "__main__":
    asyncio.run(main())