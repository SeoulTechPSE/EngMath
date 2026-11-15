"""Find text, equations and images that run into the right margin of the PDF edition.

The PDF uses A4 paper with 2.3 cm margins (_quarto-pdf.yml), so the text block
ends 2.3 cm from the right edge of the page. Anything that extends more than
TOLERANCE points beyond that edge is reported with its page number and a few
words of its text.

Usage:  python3 tools/check_pdf.py [_pdf/Engineering-Mathematics.pdf]
Needs:  python -m pip install pymupdf

Known harmless hit: page 4, the table-of-contents line of Part II, whose
bold page number ends 2.8 pt past the edge.
"""
import sys

import pymupdf

MARGIN = 2.3 / 2.54 * 72          # 2.3 cm in points
TOLERANCE = 2.5                   # points


def main(path='_pdf/Engineering-Mathematics.pdf'):
    doc = pymupdf.open(path)
    found = 0
    for page in doc:
        edge = page.rect.width - MARGIN
        for block in page.get_text('dict')['blocks']:
            x1 = block['bbox'][2]
            if x1 > edge + TOLERANCE:
                if block['type'] == 0:
                    text = ' '.join(s['text'] for l in block['lines'] for s in l['spans'])
                else:
                    text = '[image]'
                print(f'page {page.number + 1}: {x1 - edge:+.1f} pt  {text[:60]}')
                found += 1
    print(f'check_pdf: {found} block(s) beyond the right margin ({len(doc)} pages checked)')


if __name__ == '__main__':
    main(*sys.argv[1:])
