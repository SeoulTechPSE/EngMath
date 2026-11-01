"""Check the rendered book for references to missing local files.

Scans every HTML page in the output directory for src= and href= attributes
(images, figures, videos, iframes, stylesheets, scripts, links to other pages
and to PDFs) and reports those that point to a file that does not exist.
External links (http, https, mailto, ...) are not checked.

Usage:  python3 tools/check_links.py [output_dir]      (default: docs)
Exit status 1 if any broken reference is found, so CI stops before deploying.
"""
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ATTR = re.compile(r'''\b(?:src|href)\s*=\s*["']([^"'#?]*)''', re.IGNORECASE)
EXTERNAL = re.compile(r'^(?:[a-z][a-z0-9+.-]*:|//)', re.IGNORECASE)   # http:, mailto:, data:, //host
SKIP_DIRS = {'site_libs'}            # Quarto's own libraries
SKIP_FILES_ABOVE = 2_000_000         # large generated plots (plotly HTML) contain no site links


def broken_refs(root: Path):
    for page in sorted(root.rglob('*.html')):
        if SKIP_DIRS & set(page.relative_to(root).parts) or page.stat().st_size > SKIP_FILES_ABOVE:
            continue
        for url in set(ATTR.findall(page.read_text(encoding='utf-8', errors='replace'))):
            url = url.strip()
            if not url or EXTERNAL.match(url):
                continue
            target = (root / unquote(url).lstrip('/')) if url.startswith('/') \
                else (page.parent / unquote(url))
            if not target.exists():
                yield page.relative_to(root), url


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else 'docs')
    if not root.is_dir():
        sys.exit(f'output directory not found: {root}')
    pages = {}
    for page, url in broken_refs(root):
        pages.setdefault(page, []).append(url)
    n_pages = sum(1 for p in root.rglob('*.html') if 'site_libs' not in p.parts)
    if not pages:
        print(f'check_links: no broken local references ({n_pages} pages checked)')
        return
    for page, urls in pages.items():
        print(f'{page}:')
        for url in sorted(urls):
            print(f'    missing: {url}')
    sys.exit(f'check_links: {sum(map(len, pages.values()))} broken reference(s) in {len(pages)} page(s)')


if __name__ == '__main__':
    main()
