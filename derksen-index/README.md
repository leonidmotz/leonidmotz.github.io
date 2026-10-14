# Derksen Index

Lemma index to Derksen, *Etymological Dictionary of the Slavic Inherited Lexicon* (Brill, Leiden 2008).

```
index.html          page markup only
css/style.css       styles (Noto Sans comes from Google Fonts)
js/app.js           search, rhyme search, full index; loads the CSV
data/lemmata.csv    the index itself: lemma, gloss, page
```

## Editing the index

Open `data/lemmata.csv`, fix the spelling, save, reload the page. Nothing else needs touching.

- Columns: `lemma,gloss,page`, one lemma per row. Column order doesn't matter, but the header names do.
- Several forms in one entry stay in one cell, separated by `; ` (e.g. `*àblo; *àblъ`).
- A gloss containing a comma must be in double quotes: `"big, great"`. Spreadsheet programs do this automatically.
- Save as **UTF-8**. The file starts with a byte-order mark so Excel recognises the encoding. In LibreOffice choose *Unicode (UTF-8)*, separator *comma*, when opening and saving.
- Accented letters may be precomposed (`ě`) or decomposed (`e` + combining mark). Both work, because the page normalises them on load.
- Rows are shown in file order inside each letter of the full index, so keep the file in dictionary order.

## Running it

After pushing the folger to GitHub Pages, `index.html` is served at the root. Opening `index.html` locally by double-click won't work, because browsers block a page on disk from reading the CSV. To preview locally, run this inside the folder:

```
python3 -m http.server
```

then open http://localhost:8000.
