"""Optional browser smoke: run the app first; needs Playwright + Chromium."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

fixture = Path(__file__).parent / 'fixtures' / 'abyssal-lich-0.5.5.xml'
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1280, 'height': 1000})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto('http://127.0.0.1:8000')
    page.locator('#export').fill(fixture.read_text())
    page.get_by_role('button', name='Import build').click()
    page.locator('#results').wait_for(state='visible')
    assert page.locator('#life').inner_text() == '1,892'
    assert page.locator('#es').inner_text() == '6,091'
    assert page.locator('#items details').count() == 19
    page.locator('#game-life').fill('1892')
    page.locator('#game-es').fill('6091')
    assert page.locator('#comparison').inner_text().count('reported values match') == 2
    page.locator('#game-es').fill('6100')
    assert 'differs by 9' in page.locator('#comparison').inner_text()
    page.locator('#pool').fill('500')
    page.locator('#jewel').select_option('2')
    assert '6,131.61' in page.locator('#estimate').inner_text()
    page.locator('#all').check()
    assert '6,243.28' in page.locator('#estimate').inner_text()
    assert '15 percentage points across 5 jewel(s)' in page.locator('#estimate').inner_text()
    page.set_viewport_size({'width':390, 'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path='/tmp/poe2-build-lab-mobile.png', full_page=True)
    page.locator('#export').fill('invalid export')
    page.get_by_role('button', name='Import build').click()
    expect(page.locator("#message")).to_contain_text("Paste a PoB2")
    assert page.locator('#results').is_hidden()
    assert not errors, errors
    browser.close()
print('Browser smoke passed: import, equipment, game comparison, jewel scenarios, mobile, invalid import.')
