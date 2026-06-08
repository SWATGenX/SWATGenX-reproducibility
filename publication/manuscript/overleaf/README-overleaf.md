# Overleaf upload

1. Overleaf -> New Project -> **Upload Project** -> drop this ZIP.
2. Menu -> **Main document = main.tex**; **Compiler = pdfLaTeX**.
3. Compile. The supplement is a separate document: open `supplement.tex` and compile it
   once if you change it (its cross-references to the main text use the shipped
   `supplement.aux` until then).

Self-contained: figures in `final/`, generated tables in `tables/`, bib `references.bib`.
Regenerate this bundle from the monorepo with `publication/manuscript/build_overleaf_bundle.sh`.
