# Supplement PDFs

Derivations that would interrupt the lecture notes live here as stand-alone
Quarto documents. Each one is published as a PDF under `files/derivations/`
and linked from the chapter.

This folder is its own Quarto project (`_quarto.yml`), so the book build
(`quarto render`, GitHub Actions) skips it.

| Source | Published PDF | Linked from |
|--------|---------------|-------------|
| `parabolic_inverse_transforms.qmd` | `files/derivations/parabolic_inverse_transforms.pdf` | `ch_x1_Parabolic_PDEs.qmd` (4 links) |

## After editing a source

Run from the repository root:

```sh
cd derivations
quarto render parabolic_inverse_transforms.qmd --to pdf
cd ..
cp derivations/parabolic_inverse_transforms.pdf files/derivations/
git add derivations/parabolic_inverse_transforms.qmd files/derivations/parabolic_inverse_transforms.pdf
```

The PDF in `derivations/` itself is ignored by git; only the copy in
`files/derivations/` is published.

If the section numbers change, update the link texts in the chapter
("Derivation (Section 5 of the supplement)").
