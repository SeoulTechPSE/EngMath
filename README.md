## Engineering Mathematics Lecture Note

Kee-Youn Yoo

Department of Chemical and Biomolecular Engineering

Seoul National University of Science and Technology

### Maintenance

- The site is built by GitHub Actions (`.github/workflows/publish.yml`) from the frozen results in `_freeze/`; run `quarto render` locally after changing code so that `_freeze/` is updated.
- `notebooks/` holds the Colab versions of the appendices. They are generated, so after editing an appendix (`x_*.qmd`) run `python3 tools/make_notebooks.py`. The build stops if they are out of date.
- `tools/check_links.py` runs after rendering and stops the deployment if a page refers to a missing file.
- PDF edition (main chapters only): `quarto render --profile pdf --to pdf` writes `_pdf/Engineering-Mathematics.pdf`; copy it to `files/` to publish it. It runs the code (about 3 minutes) and uses `tools/pdf.lua`. After changing an animation, run `python3 tools/make_filmstrips.py` first to refresh its still frames in `figures/pdf/`.
- `tools/check_pdf.py` (needs `pymupdf`) lists text, equations and images of the PDF that run into the right margin; run it after rebuilding the PDF. Page 4 (the table of contents) is a known harmless hit.
- Figure sources: the SVG figures are drawn by the scripts in `figures/src/` of the slides repository (EngMath-slides) and copied to `figures/`.
- Main chapters: cells that draw figures or animations carry `#| code-fold: true`. On the web their code is folded, and `tools/pdf.lua` leaves it out of the PDF, so only the figure is printed. Code meant to be read (SymPy and NumPy examples) stays unfolded.
- Each chapter's learning-objectives box ends with a **Builds on** line that links to the earlier sections the chapter uses. Keep it up to date when sections move.
