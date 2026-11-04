"""Optional browser smoke: run the app first; needs Playwright + Chromium."""
from pathlib import Path
import os, json
from playwright.sync_api import sync_playwright, expect

fixture = Path(__file__).parent / 'fixtures' / 'abyssal-lich-0.5.5.xml'
with sync_playwright() as p:
    engine = os.environ.get('BROWSER_ENGINE','chromium')
    browser_type = getattr(p,engine)
    launch_options = {'headless':True}
    if engine == 'chromium' and Path('/usr/bin/chromium').exists():
        launch_options.update(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    browser = browser_type.launch(**launch_options)
    page = browser.new_page(viewport={'width': 1280, 'height': 1000})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(os.environ.get('BROWSER_BASE_URL','http://127.0.0.1:8001'))
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
    page.locator('#calculate').click()
    expect(page.locator('#calculated')).to_be_visible(timeout=65000)
    assert page.locator('#calculated-life').inner_text() == '1,892'
    assert page.locator('#calculated-es').inner_text() == '6,091'
    assert 'Both calculated totals match' in page.locator('#calc-comparison').inner_text()
    assert page.locator('#es-breakdown tr').count() == 6
    assert page.locator('#ledger tr').count() > 100
    assert "Nature's Archon" in page.locator('#calc-warnings').inner_text()
    page.locator('#jewel').select_option('2')
    page.locator('#scenario-button').click()
    expect(page.locator('#scenario-results')).to_be_visible(timeout=125000)
    assert '6,129' in page.locator('#scenario-totals').inner_text()
    assert '+38' in page.locator('#scenario-totals').inner_text()
    assert '16 → 20%' in page.locator('#scenario-changes').inner_text()
    page.locator('#jewel-mode').select_option('all')
    assert page.locator('#scenario-results').is_hidden()
    assert page.locator('#jewel').is_disabled()
    page.locator('#scenario-button').click()
    expect(page.locator('#scenario-results')).to_be_visible(timeout=125000)
    assert '6,234' in page.locator('#scenario-totals').inner_text()
    page.locator('#edit-chest').check()
    page.locator('#chest-es').fill('400')
    page.locator('#scenario-button').click()
    expect(page.locator('#scenario-results')).to_be_visible(timeout=125000)
    assert '7,433' in page.locator('#scenario-totals').inner_text()
    assert '215 → 400 final local ES' in page.locator('#scenario-changes').inner_text()
    assert "Nature's Archon" in page.locator('#scenario-warnings').inner_text()
    page.locator('#edit-chest').uncheck()
    page.locator('#edit-jewels').uncheck()
    page.locator('#scenario-button').click()
    expect(page.locator('#scenario-results')).to_be_visible(timeout=125000)
    assert 'No changes requested' in page.locator('#scenario-changes').inner_text()
    assert '6,091' in page.locator('#scenario-totals').inner_text()
    page.locator('#belt-mode').select_option('rune')
    assert page.locator('#scenario-results').is_hidden()
    page.locator('#scenario-button').click()
    expect(page.locator('#scenario-results')).to_be_visible(timeout=125000)
    assert '6,386' in page.locator('#scenario-totals').inner_text()
    assert 'Fox Idol → Iron Rune' in page.locator('#scenario-changes').inner_text()
    page.locator('#belt-mode').select_option('ingenuity')
    page.locator('#scenario-button').click()
    expect(page.locator('#scenario-results')).to_be_visible(timeout=125000)
    assert '1,919' in page.locator('#scenario-totals').inner_text()
    assert '6,122' in page.locator('#scenario-totals').inner_text()
    assert 'insufficient Spirit' in page.locator('#scenario-warnings').inner_text()
    assert 'diagnostic and not reconciled' in page.locator('#scenario-warnings').inner_text()
    assert '→ -9' in page.locator('#scenario-resources').inner_text()
    assert 'Darkness Enthroned → Ingenuity' in page.locator('#scenario-changes').inner_text()
    page.set_viewport_size({'width':390, 'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path='/tmp/poe2-build-lab-mobile.png', full_page=True)
    page.locator('#build-name').fill('Safari saved test')
    page.locator('#save-build').click()
    expect(page.locator('#library-status')).to_contain_text('Saved on this device')
    with page.expect_download() as download_info:
        page.locator('#export-backup').click()
    backup_path = download_info.value.path()
    backup = json.loads(Path(backup_path).read_text())
    assert backup['format'] == 'poe2-build-lab'
    assert any(record['name']=='Safari saved test' for record in backup['builds'])
    page.reload()
    expect(page.locator('#saved-builds option')).to_have_count(1)
    page.locator('#load-build').click()
    expect(page.locator('#results')).to_be_visible()
    assert page.locator('#build-name').input_value()=='Safari saved test'
    assert page.locator('#belt-mode').input_value()=='ingenuity'
    page.locator('#delete-build').click()
    expect(page.locator('#saved-builds option')).to_have_count(0)
    page.locator('#backup-file').set_input_files({'name':'backup.json','mimeType':'application/json','buffer':Path(backup_path).read_bytes()})
    expect(page.locator('#library-status')).to_contain_text('Restored 1 build')
    expect(page.locator('#saved-builds option')).to_have_count(1)
    page.locator('#load-build').click()
    expect(page.locator('#results')).to_be_visible()
    page.wait_for_function('() => !!navigator.serviceWorker.controller')
    page.context.set_offline(True)
    page.reload()
    expect(page.locator('#saved-builds option')).to_have_count(1)
    page.locator('#load-build').click()
    expect(page.locator('#results')).to_be_visible()
    page.locator('#calculate').click()
    expect(page.locator('#calculated')).to_be_visible(timeout=125000)
    assert page.locator('#calculated-es').inner_text()=='6,091'
    page.context.set_offline(False)
    page.locator('#export').fill('invalid export')
    page.get_by_role('button', name='Import build').click()
    expect(page.locator("#message")).to_contain_text("Paste a PoB2")
    assert page.locator('#results').is_hidden()
    assert not errors, errors
    browser.close()
print('Browser smoke passed: import, equipment, game comparison, independent recalculation, ledger, engine-backed jewel/chest/rune/Ingenuity/no-op scenarios, Spirit coverage, mobile, local saves, backup restore, offline recalculation, invalid import.')
