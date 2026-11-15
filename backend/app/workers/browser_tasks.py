"""Browser automation tasks. MUST run only in the 'browser' Celery queue."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path

import redis
from celery import shared_task
from playwright.async_api import async_playwright

from app.config import settings
from app.database import SessionLocal
from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.services.browser_session import session_path
from app.services.quota import try_consume

SCREENSHOT_DIR = Path("/app/uploads/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

redis_client = redis.from_url(settings.REDIS_URL)


def _approval_key(user_id: int, job_id: int) -> str:
    return f"approval:{user_id}:{job_id}"


@shared_task(bind=True, name="app.workers.browser_tasks.fill_application", queue="browser")
def fill_application(self, user_id: int, job_id: int):
    """Fill the application form but do NOT submit. Screenshot and await approval."""
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        job = db.get(Job, job_id)
        if not user or not job:
            return {"error": "User or job not found"}
    finally:
        db.close()

    state_file = session_path(user_id, "naukri")
    if not state_file.exists():
        return {"error": "No Naukri session. Run scripts/connect_naukri.py first."}

    return asyncio.run(_fill_naukri(job, state_file, user_id, job_id))


async def _fill_naukri(job: Job, state_file: Path, user_id: int, job_id: int) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(storage_state=str(state_file))
        page = await context.new_page()
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        try:
            await page.goto(job.job_url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            apply_btn = page.locator('button:has-text("Apply"), a:has-text("Apply")').first
            if not await apply_btn.count():
                screenshot_path = SCREENSHOT_DIR / f"FAIL_{user_id}_{job_id}_{ts}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                return {"error": "Apply button not found.", "screenshot": screenshot_path.name}

            await apply_btn.click()
            await page.wait_for_timeout(3000)

            if "company" in page.url.lower():
                return {"error": "External company application. Manual review required."}

            screenshot_path = SCREENSHOT_DIR / f"{user_id}_{job_id}_{ts}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)

            redis_client.setex(_approval_key(user_id, job_id), 3600, "pending")

            db = SessionLocal()
            try:
                app = db.query(Application).filter_by(user_id=user_id, job_id=job_id).first()
                if app:
                    app.notes = f"Form filled. Screenshot: {screenshot_path.name}. Awaiting approval."
                    db.commit()
            finally:
                db.close()

            return {
                "status": "awaiting_approval",
                "screenshot": screenshot_path.name,
            }

        except Exception as exc:
            fail_path = SCREENSHOT_DIR / f"FAIL_{user_id}_{job_id}_{ts}.png"
            try:
                await page.screenshot(path=str(fail_path), full_page=True)
                html_path = SCREENSHOT_DIR / f"FAIL_{user_id}_{job_id}_{ts}.html"
                html_path.write_text(await page.content())
            except Exception:
                pass
            return {"error": str(exc), "screenshot": fail_path.name}

        finally:
            await context.close()
            await browser.close()


@shared_task(bind=True, name="app.workers.browser_tasks.submit_application", queue="browser")
def submit_application(self, user_id: int, job_id: int):
    """Submit a previously filled application after user approval."""
    approval = redis_client.get(_approval_key(user_id, job_id))
    if not approval or approval.decode() != "pending":
        return {"error": "No pending approval for this application"}

    allowed, remaining = try_consume(user_id, "naukri")
    if not allowed:
        return {"error": "Daily application limit reached. Try again tomorrow."}

    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
    finally:
        db.close()

    if not job:
        return {"error": "Job not found"}

    state_file = session_path(user_id, "naukri")
    if not state_file.exists():
        return {"error": "Session missing. Reconnect your Naukri account."}

    result = asyncio.run(_submit_naukri(job, state_file))

    if result.get("success"):
        db = SessionLocal()
        try:
            app = db.query(Application).filter_by(user_id=user_id, job_id=job_id).first()
            if app:
                app.status = "applied"
                app.notes = f"Auto-submitted. Remaining today: {remaining}."
                db.commit()
        finally:
            db.close()
        redis_client.delete(_approval_key(user_id, job_id))

    return result


async def _submit_naukri(job: Job, state_file: Path) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(storage_state=str(state_file))
        page = await context.new_page()

        try:
            await page.goto(job.job_url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            apply_btn = page.locator('button:has-text("Apply"), a:has-text("Apply")').first
            await apply_btn.click()
            await page.wait_for_timeout(3000)

            submit_btn = page.locator('button:has-text("Submit"), button:has-text("Send")').first
            if not await submit_btn.count():
                return {"error": "Submit button not found. Form may have changed."}

            await submit_btn.click()
            await page.wait_for_timeout(5000)

            return {"success": True, "url": page.url}

        except Exception as exc:
            return {"error": str(exc)}
        finally:
            await context.close()
            await browser.close()