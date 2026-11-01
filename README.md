## Engineering Mathematics Lecture Note

Kee-Youn Yoo

Department of Chemical and Biomolecular Engineering

Seoul National University of Science and Technology

### Maintenance

- The site is built by GitHub Actions (`.github/workflows/publish.yml`) from the frozen results in `_freeze/`; run `quarto render` locally after changing code so that `_freeze/` is updated.
- `notebooks/` holds the Colab versions of the appendices. They are generated, so after editing an appendix (`x_*.qmd`) run `python3 tools/make_notebooks.py`. The build stops if they are out of date.
- `tools/check_links.py` runs after rendering and stops the deployment if a page refers to a missing file.
