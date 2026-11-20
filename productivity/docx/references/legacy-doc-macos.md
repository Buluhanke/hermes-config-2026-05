# Legacy .doc fill-in on macOS (textutil round-trip)

Legacy binary `.doc` (Composite Document, WPS or Word 97-2003) cannot be
opened by python-docx and the scripts disclaim it. On macOS `textutil`
converts in both directions, giving a round-trip that preserves tables,
styles, and page layout well enough for form filling.

## Procedure

1. **Read the template.** `textutil -convert html file.doc -output
   work.html`, then strip `<style>...</style>` and `<head>...</head>`
   blocks before extracting text. WPS-converted HTML dumps hundreds of
   CSS class definitions first — without stripping, the first 200+
   extracted lines are noise that buries the real content.
2. **Inventory every fill-in position before editing.** Scan the FULL
   extracted text for: `____` blanks, `XX` / `XXX` / `***` placeholder
   company names, `【A/B】` choice brackets, empty `：` / `：____`
   labels, and underline-only runs. WPS templates scatter placeholders
   across 30+ pages (contract body PLUS attached emergency-plan /
   training-record chapters), not just the visible first pages.
3. **Convert for editing.** `textutil -convert docx file.doc -output
   work.docx`, then edit the docx — prefer python-docx run-level
   replacement; if patching `word/document.xml` directly, match
   COMPLETE `<w:t xml:space="preserve">` elements (whole run text),
   never loose substrings (see the unzip-and-sed pitfall in SKILL.md).
4. **Repackage and convert back.** Zip the edited package back to
   `.docx`, then `textutil -convert doc work.docx -output out.doc`.
5. **Verify.** Convert the OUTPUT back to html and count strings:
   every placeholder pattern (`XX公司`, `___`, `***`) must read zero,
   and each new filled value must be present. Never trust the edit
   step alone — confirm through the round-trip output.

## Underline the filled values

Underscore blanks ARE the visual underline — replacing a `____` run
with the value erases it. When the user wants 下划线 on filled content
(or the template's blanks are underscore runs), re-apply formatting by
injecting `<w:u w:val="single"/>` into the filled run's `<w:rPr>`
(insert before `</w:rPr>`; create the `<w:rPr>` element if the run has
none). Apply to every filled run, including cover-page company names.

Verify rendering, don't trust the XML: convert to PDF with LibreOffice
and check a short horizontal line sits within ~5pt below each filled
value's baseline (`page.search_for` gives the text bbox;
`page.get_drawings` yields the lines). Counting horizontal lines per
page also catches an underline applied to the WRONG run.

## Truncating to the first N pages

Cut from the RENDERED page boundary, not paragraph markers — the count
of explicit `<w:br w:type="page"/>` in the XML does not equal rendered
pages, because content flow creates extra boundaries.

1. Convert the package to PDF with LibreOffice; per-page first lines
   (pymupdf `fitz`) identify which section starts each rendered page.
2. Locate the paragraph containing the explicit page break that
   precedes the section to drop; delete everything from that
   paragraph's start (`<w:p` or `<w:p>`) through the end of
   `<w:body>`, KEEPING the trailing `<w:sectPr>`.
3. Repackage, re-render, and confirm the page count equals N and the
   kept content ends where expected.

## Pitfalls

- **`textutil -output` does not expand `~`.** Passing a quoted
  `'~/Desktop/out.doc'` fails with "folder doesn't exist". Always pass
  an absolute path (`/Users/<name>/Desktop/out.doc`).
- **Cover-page split runs.** A placeholder like an underline-blank run
  followed by a separate `公司` run needs BOTH runs handled (fill the
  blank run, empty the suffix run), or the name comes out wrong. On
  lease packets the attached emergency-plan cover's `公司` is the
  TENANT (乙方) — the plan governs the lessee's operations, not the
  landlord's.
- **Duplicate label lines need positional replace.** Party blocks
  repeat identical labels (`地址：____` appears for BOTH parties); a
  global `str.replace` fills every duplicate with the same value.
  Replace by position — find the first occurrence, then search for the
  next from the first match's end, or anchor on the preceding line's
  text (the credit-code line distinguishes the parties).
- **`.*?` spans runs under `re.S`.** A run-matching regex like
  `(<w:r>)(<w:rPr>.*?</w:rPr>)?(<w:t...>text</w:t>)` under DOTALL lets
  `.*?` cross `</w:r><w:r>` boundaries, so the edit lands on an
  unrelated run (the document title got underlined instead of the
  target). Stay inside one run with a tempered greedy token:
  `<w:r(?:\s[^>]*)?>(?:(?!</w:r>).)*?</w:r>`.
- **Check what's already filled.** Templates often arrive with the
  header party block already completed — re-read before duplicating
  fills. Fill only the positions still holding placeholder patterns.
- **Party-info blocks in contract templates follow a fixed shape:**
  name line, then 统一社会信用代码, then 地址, then 法定代表人/负责人 —
  map the user's supplied fields onto that order instead of guessing
  positions from prose alone.
