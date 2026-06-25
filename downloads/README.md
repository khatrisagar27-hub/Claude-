# Downloads — free tools & utilities

Put the files you want visitors to download **in this folder**, then point the
download buttons in `index.html` (the "Tools & Utilities" section) at them.

## How to add a tool

1. Drop the file here, e.g. `downloads/income-tax-calculator.xlsx`.
2. In `index.html`, find the matching `<article class="tool-card">` and update:
   - the **badge** (`XLSX` / `PDF` / `ZIP` / `DOCX`),
   - the **title** and **description**,
   - the **meta** line (format · version/date),
   - the **href** so it matches your filename, keeping the `download` attribute:
     ```html
     <a class="btn-download" href="downloads/your-file.xlsx" download>Download</a>
     ```
3. Add or remove `tool-card` blocks to match how many tools you have.
4. Commit & push — GitHub Pages serves the files directly.

## Notes
- GitHub Pages serves `.xlsx`, `.pdf`, `.zip`, `.docx` etc. fine. Keep individual
  files reasonably small (a few MB) — a git repo isn't ideal for very large files.
- The example filenames referenced in `index.html` are placeholders; replace them
  with your real ones (or the buttons will 404 until the files exist).
- Keep descriptions factual and free of promotional language (ICAI compliance).
