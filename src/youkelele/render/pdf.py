"""Print the sheet page to an A4 PDF with headless Chromium."""

from __future__ import annotations

from pathlib import Path


def html_to_pdf(
    html_path: Path,
    pdf_path: Path,
    timeout_ms: int = 60000,
    *,
    console: list[str] | None = None,
) -> None:
    """Load ``html_path`` from disk, wait for its fonts, print to ``pdf_path``.

    ``console``, when given, collects the page's console errors and uncaught exceptions.
    """
    # Imported here so that importing the chain does not pay for Playwright.
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.set_default_timeout(timeout_ms)
            if console is not None:
                page.on(
                    "console",
                    lambda msg: console.append(msg.text) if msg.type == "error" else None,
                )
                page.on("pageerror", lambda exc: console.append(str(exc)))
            page.goto(Path(html_path).resolve().as_uri())
            page.evaluate("document.fonts.ready.then(() => true)")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
            )
        finally:
            browser.close()
