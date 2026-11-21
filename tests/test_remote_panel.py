import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(not shutil.which('node'), reason='Node.js is required to test the remote JavaScript')
def test_settings_panel_remains_interactive_in_inline_and_sheet_modes():
    source = (Path(__file__).resolve().parents[1] / 'static' / 'classic-remote.js').read_text(encoding='utf-8')
    start = source.index(' function syncSheet(){')
    end = source.index('\n function showLcd()', start)
    script = '''
const assert = require('node:assert/strict');
let theme = 'default', tabName = 'book', classes = new Set(), sheet = {};
const classic = () => theme === 'classic', tab = () => tabName, $ = () => sheet;
const document = {body: {classList: {remove: name => classes.delete(name)},
  matches: selector => selector.split(',').some(s => classes.has(s.slice(1)))}};
''' + source[start:end] + '''
syncSheet(); assert.equal(sheet.inert, true);
classes.add('sheet-open'); syncSheet(); assert.equal(sheet.inert, false);
classes.clear(); classes.add('sheet-inline'); syncSheet(); assert.equal(sheet.inert, false);
theme = 'classic'; syncSheet(); assert.equal(sheet.inert, true);
tabName = 'settings'; syncSheet(); assert.equal(sheet.inert, false);
'''
    subprocess.run(['node', '-e', script], check=True)
