from playwright.sync_api import sync_playwright
import time


def test_radio_text_color():
    """Basic headless check: open the Streamlit app and verify the radio label color.

    This test expects the Streamlit app to be available at http://127.0.0.1:8501.
    In CI the workflow will start Streamlit in the background before running pytest.
    """
    url = "http://127.0.0.1:8501/"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # Give the app a little time to start; pytest/CI will also wait for readiness
        page.goto(url, timeout=60000)

        # Wait for text nodes we expect to exist (adjust selectors if your app differs)
        page.wait_for_selector('text="Descending"', timeout=20000)

        # Evaluate computed style color for the visible label element
        color = page.eval_on_selector('text="Descending"', 'el => window.getComputedStyle(el).color')

        # Accept rgb(242, 242, 242) which corresponds to #f2f2f2
        assert 'rgb(242, 242, 242)' in color or '#f2f2f2' in color.lower()

        browser.close()
