# wlachtype

On-screen keyboard for Wallachian Cyrillic: superscript letters, diacritics and the extra letters, with Alt + letter and number-key shortcuts.

```
index.html                           page markup only
css/style.css                        styles (Noto Sans comes from Google Fonts)
js/app.js                            keyboard logic; builds the keys from the CSV
data/keys.csv                        the keys: edit this to add, remove or reorder keys
fonts/noto-sans-dotted-circle.woff2  the ◌ shown under combining marks on the keys
```

The tiny local font exists because Google's Noto Sans does not include the dotted circle (U+25CC).

## Editing the keys

Each line of `data/keys.csv` is one key; keys appear in file order within their row. Columns:

| column   | meaning |
|----------|---------|
| row      | `sup` (superscripts), `dia` (diacritics) or `let` (letters) |
| char     | the character, or its code point such as `U+2DE0` |
| capital  | `let` only: the uppercase form (typed when Shift is on) |
| name     | shown in the bar above the keys. For `let`, just the short name (`zemlya`); "cyrillic small/capital letter" is added automatically |
| shortcut | `sup`: the letter that types it with Alt (e.g. `б`). `dia`: a digit 0–9. Leave empty for no shortcut |

Examples:

```
let,ꙁ,Ꙁ,zemlya,
dia,U+A67D,,combining cyrillic kavyka,9
sup,U+2DF5,,combining cyrillic letter es-te,
```

- Write combining marks as code points (`U+0483`). Typed directly, they fuse with the comma before them and are hard to see in an editor. A sequence also works: `U+0430 U+0301`.
- Combining marks are detected automatically and shown on a dotted circle.
- A field containing a comma needs double quotes. Save as UTF-8.
- Each shortcut should be used once; if two keys share one, the later line wins.

## Running it

Push the folder to the GitHub Pages repository. Opening `index.html` by double-click won't load the keys, because browsers block a page on disk from reading files. To preview locally, run this inside the folder:

```
python3 -m http.server
```

then open http://localhost:8000.
