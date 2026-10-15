"""Guard against shipping development checklists and example project paths in public guidance."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_public_docs_are_product_focused():
    public_files = [ROOT / 'README.md', ROOT / 'CHANGELOG.md',
                    ROOT / 'docs' / 'INSTALLATION.md', ROOT / 'docs' / 'CONTRIBUTING.md',
                    ROOT / 'docs' / 'USAGE.md', ROOT / 'docs' / 'TROUBLESHOOTING.md']
    for path in public_files:
        content = path.read_text(encoding='utf-8')
        assert 'Odoo Module Explorer' in content or path.name == 'CONTRIBUTING.md'
        assert not re.search(r'\bphase\s+\d+\b', content, re.IGNORECASE)
    assert not (ROOT / 'docs' / 'ROADMAP.md').exists()
    assert not (ROOT / 'docs' / 'RELEASE_CHECKLIST.md').exists()
    assert not (ROOT / 'docs' / 'RELEASING.md').exists()
    assert (ROOT / 'LICENSE').is_file()


def test_ui_uses_only_generic_path_examples_and_release_labels():
    source = (ROOT / 'frontend' / 'src' / 'App.tsx').read_text(encoding='utf-8')
    assert 'custom_addons' in source
    assert 'my_addon' in source
    assert not re.search(r'\bphase\s*\d+\b', source, re.IGNORECASE)


def test_public_documentation_relative_links_resolve():
    """All local Markdown file links must point to real tracked files and headings."""
    files = [ROOT / 'README.md', ROOT / 'docs' / 'INSTALLATION.md',
             ROOT / 'docs' / 'USAGE.md', ROOT / 'docs' / 'CONTRIBUTING.md',
             ROOT / 'docs' / 'TROUBLESHOOTING.md']
    for source in files:
        body = source.read_text(encoding='utf-8')
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', body):
            if target.startswith(('http:', 'https:', 'mailto:')):
                continue
            relative, _, fragment = target.partition('#')
            resolved = (source.parent / relative).resolve() if relative else source
            assert resolved.is_file(), f'{source.name}: broken link to {target}'
            if fragment:
                headings = re.findall(r'^#{1,6} +(.+)$', resolved.read_text(encoding='utf-8'), re.M)
                anchors = [re.sub(r'[^\w\- ]', '', h.lower()).replace(' ', '-') for h in headings]
                assert fragment in anchors, f'{source.name}: missing heading {target}'
