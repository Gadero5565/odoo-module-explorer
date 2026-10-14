"""Guard against shipping development checklists and example project paths in public guidance."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_public_docs_are_product_focused():
    public_files = [ROOT / 'README.md', ROOT / 'CHANGELOG.md',
                    ROOT / 'docs' / 'RELEASING.md', ROOT / 'docs' / 'CONTRIBUTING.md']
    for path in public_files:
        content = path.read_text(encoding='utf-8')
        assert 'Odoo Module Explorer' in content or path.name == 'CONTRIBUTING.md'
        assert not re.search(r'\bphase\s+\d+\b', content, re.IGNORECASE)
    assert not (ROOT / 'docs' / 'ROADMAP.md').exists()
    assert not (ROOT / 'docs' / 'RELEASE_CHECKLIST.md').exists()


def test_ui_uses_only_generic_path_examples_and_release_labels():
    source = (ROOT / 'frontend' / 'src' / 'App.tsx').read_text(encoding='utf-8')
    assert 'custom_addons' in source
    assert 'my_addon' in source
    assert not re.search(r'\bphase\s*\d+\b', source, re.IGNORECASE)
