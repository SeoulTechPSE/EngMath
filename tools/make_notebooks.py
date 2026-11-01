"""Generate Colab-ready Jupyter notebooks from the appendix chapters.

Each appendix x_*.qmd listed in the Appendices part of _quarto.yml becomes notebooks/<name>.ipynb:
python cells become code cells (Quarto cell options removed, {{< include >}}
files inlined), and the Quarto-only markdown is rewritten so that it works
outside the book (images and links point to the published site, @sec
references become links, callout fences are dropped). A first code cell
installs what Colab lacks.

Usage:  python3 tools/make_notebooks.py           write notebooks/
        python3 tools/make_notebooks.py --check   exit 1 if notebooks/ is stale (CI)
"""
import json
import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'notebooks'
SITE = 'https://seoultechpse.github.io/EngMath/'
REPO = 'https://github.com/SeoulTechPSE/EngMath/blob/main/'
COLAB = 'https://colab.research.google.com/github/SeoulTechPSE/EngMath/blob/main/notebooks/'

# What a fresh Colab runtime needs beyond its preinstalled packages
SETUP = {
    'x_sympy_Laplace_transform': ['%pip install -q "sympy>=1.14"'],
    'x_ordinary_differential_equations': ['%pip install -q "sympy>=1.14"'],
    'x_optimization': ['%pip install -q cvxopt'],
    'x_hydrogen_orbital': ['%pip install -q "scipy>=1.15"'],
    'x_matplotlib': [
        '!apt-get -qq install -y fonts-nanum > /dev/null   # Korean font for the Hangul example',
        'import glob, matplotlib.font_manager as fm',
        "for f in glob.glob('/usr/share/fonts/truetype/nanum/*.ttf'):",
        '    fm.fontManager.addfont(f)',
    ],
}

HEADING_ID = re.compile(r'^(#{1,6})\s+(.*?)\s*\{#(sec-[\w-]+)[^}]*\}\s*$')
ATTRS = re.compile(r'\s*\{[^{}]*\}\s*$')
IMAGE = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)(\{[^}]*\})?')
LINK = re.compile(r'(?<!!)\[([^\]]+)\]\(([^)\s]+)\)')
INCLUDE = re.compile(r'\{\{<\s*include\s+(\S+)\s*>\}\}')
IFRAME = re.compile(r'<iframe\s+src="([^"]+)"', re.S)


def appendices():
    text = (ROOT / '_quarto.yml').read_text(encoding='utf-8')
    block = text.split('"**Appendices**"')[1]
    return re.findall(r'^\s+-\s+(x_[\w-]+)\.qmd', block, re.M)   # commented-out entries do not match


def section_index():
    """sec id -> (url, title) for every heading id in the book."""
    index = {}
    for qmd in ROOT.glob('*.qmd'):
        for line in qmd.read_text(encoding='utf-8').split('\n'):
            m = HEADING_ID.match(line)
            if m:
                title = re.sub(r'^\$[~\\,]+\$', '', m[2]).strip()
                anchor = '' if len(m[1]) == 1 else '#' + m[3]
                index[m[3]] = (SITE + qmd.stem + '.html' + anchor, title)
    return index


def absolute(url):
    if re.match(r'^(?:[a-z][a-z0-9+.-]*:|#|//)', url):
        return url
    path = posixpath.normpath(url)
    if path.endswith('.qmd'):
        return SITE + path[:-4] + '.html'
    if path.endswith('.py'):
        return REPO + path
    return SITE + path


def markdown(lines, sections):
    out = []
    for line in lines:
        if 'colab-badge.svg' in line:
            continue
        if re.match(r'^:{3,}', line):                       # fenced div (callout, columns)
            title = re.search(r'title="([^"]*)"', line)
            if title:
                out.append(f'**{title[1]}**')
            continue
        if re.match(r'^#{1,6}\s', line):
            line = ATTRS.sub('', line)

        def image(m):
            alt, url, attrs = m[1], absolute(m[2]), m[3] or ''
            width = re.search(r'width="?([\w.%]+)"?', attrs)
            if width:
                return f'<img src="{url}" alt="{alt}" width="{width[1]}">'
            return f'![{alt}]({url})'

        line = IMAGE.sub(image, line)
        line = LINK.sub(lambda m: f'[{m[1]}]({absolute(m[2])})', line)
        for sid in re.findall(r'@(sec-[\w-]*\w)', line):
            if sid in sections:
                url, title = sections[sid]
                # "@sec-x (Title)" reads "Section 2.6 (Title)" in the book; here the link text is the title
                line = re.sub(rf'@{sid}(?![\w-])( \({re.escape(title)}\))?', f'[{title}]({url})', line)
        line = re.sub(r'(\d)\^(st|nd|rd|th)\^', r'\1<sup>\2</sup>', line)   # Pandoc superscript 2^nd^
        out.append(line)
    return out


def cell(kind, lines):
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    if not lines:
        return None
    src = [l + '\n' for l in lines[:-1]] + [lines[-1]]
    c = {'cell_type': kind, 'metadata': {}, 'source': src}
    if kind == 'code':
        c.update(execution_count=None, outputs=[])
    return c


def convert(name, sections):
    text = (ROOT / f'{name}.qmd').read_text(encoding='utf-8')
    text = re.sub(r'\A---\n.*?\n---\n', '', text, flags=re.S)      # YAML front matter
    lines = text.split('\n')
    title_line = next(l for l in lines if l.startswith('# '))
    title = ATTRS.sub('', title_line[2:]).strip()

    cells = [cell('markdown', [
        f'# {title}', '',
        f'*Notebook version of the appendix [{title}]({SITE}{name}.html) in the '
        f'[Engineering Mathematics]({SITE}) notes. It is generated from `{name}.qmd`; '
        'edits to this file are overwritten.*'])]
    setup = SETUP.get(name, [])
    if setup:
        cells.append(cell('code', ['# Colab setup: install what the runtime does not provide',
                                   'import sys', "if 'google.colab' in sys.modules:",
                                   *['    ' + s for s in setup]]))

    md, i = [], 0
    while i < len(lines):
        line = lines[i]
        if line is title_line:
            i += 1
            continue
        fence = re.match(r'^```+\s*\{(python|=html)\}', line)
        if fence:
            j = next(k for k in range(i + 1, len(lines)) if lines[k].startswith('```'))
            body = lines[i + 1:j]
            if fence[1] == 'python':
                cells.append(cell('markdown', markdown(md, sections))); md = []
                code = []
                for l in body:
                    if re.match(r'^#\s?\|', l):
                        continue
                    inc = INCLUDE.search(l)
                    code += (ROOT / inc[1]).read_text(encoding='utf-8').rstrip('\n').split('\n') if inc else [l]
                if any(re.match(r'^#\s?\|\s*error:\s*true', l) for l in body):
                    # a cell that fails on purpose must not stop "Run all"
                    code = ['# This cell raises an error on purpose; try/except prints it and lets the notebook go on',
                            'try:', *['    ' + l for l in code],
                            'except Exception as e:', "    print(f'{type(e).__name__}: {e}')"]
                cells.append(cell('code', code))
            else:                                               # raw HTML: iframes become links
                src = IFRAME.search('\n'.join(body))
                if src:
                    url = absolute(src[1])
                    md.append(f'Interactive figure: [{posixpath.basename(src[1])}]({url})')
                else:
                    md += body
            i = j + 1
            continue
        if line.startswith('```'):                              # other code blocks stay in markdown
            j = next(k for k in range(i + 1, len(lines)) if lines[k].startswith('```'))
            md += lines[i:j + 1]
            i = j + 1
            continue
        md.append(line)
        i += 1
    cells.append(cell('markdown', markdown(md, sections)))

    nb = {'cells': [c for c in cells if c],
          'metadata': {'colab': {'provenance': []},
                       'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                       'language_info': {'name': 'python'}},
          'nbformat': 4, 'nbformat_minor': 4}
    return json.dumps(nb, ensure_ascii=False, indent=1) + '\n'


def main():
    check = '--check' in sys.argv
    sections = section_index()
    stale = []
    OUT.mkdir(exist_ok=True)
    for name in appendices():
        text = convert(name, sections)
        path = OUT / f'{name}.ipynb'
        if path.exists() and path.read_text(encoding='utf-8') == text:
            continue
        stale.append(path.name)
        if not check:
            path.write_text(text, encoding='utf-8')
    if check and stale:
        sys.exit('make_notebooks: notebooks/ is out of date, run python3 tools/make_notebooks.py: '
                 + ', '.join(stale))
    print(f'make_notebooks: {len(appendices())} notebooks' +
          (' up to date' if check else f', {len(stale)} written'))


if __name__ == '__main__':
    main()
