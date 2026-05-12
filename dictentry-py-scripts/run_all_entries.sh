#!/usr/bin/env bash
# Run from: /home/leonid/github/leonidmotz.github.io/suprasliensis-data
# Generates analogical_all.tex and per-stemclass files in dictentry-py-scripts/dictentry-per-stemclass/

SCRIPT="dictentry-py-scripts/make_latex_entry.py"
OUTDIR="dictentry-py-scripts/dictentry-per-stemclass"
mkdir -p "$OUTDIR"

# Map from output filename -> stem attribute value(s) in XML
declare -A STEMFILES
STEMFILES["o_stem_masc_dict.tex"]="o stem masc"
STEMFILES["ja_stem_masc_dict.tex"]="ja stem masc"
STEMFILES["o_stem_neutr_dict.tex"]="o stem neutr"
STEMFILES["jo_stem_masc_dict.tex"]="jo stem masc"
STEMFILES["jo_stem_neutr_dict.tex"]="jo stem neutr"
STEMFILES["i_stem_masc_dict.tex"]="i stem masc"
STEMFILES["i_stem_fem_dict.tex"]="i stem fem"
STEMFILES["short_u_stem_dict.tex"]="ŭ stem"
STEMFILES["long_u_stem_dict.tex"]="ū stem"
STEMFILES["n_stem_dict.tex"]="n stem"
STEMFILES["s_stem_dict.tex"]="s stem"
STEMFILES["r_stem_dict.tex"]="r stems"
STEMFILES["t_stem_dict.tex"]="t stem"
STEMFILES["tel_stem_dict.tex"]="tel stem"

# Get all lemmas with analogical tokens, with their stem class
# Format: lemma<TAB>stem
get_lemmas_for_stem() {
    local stemval="$1"
    grep 'stemtype="analogical"' suprasliensis.xml \
        | grep 'stem="'"$stemval"'"' \
        | grep -oP 'lemma="\K[^"]+' \
        | sort -u
}

# All analogical lemmas regardless of stem
ALL_LEMMAS=$(grep 'stemtype="analogical"' suprasliensis.xml \
    | grep -oP 'lemma="\K[^"]+' \
    | sort -u)

echo "Generating analogical_all.tex..."
echo "$ALL_LEMMAS" | while read lemma; do
    python3 "$SCRIPT" "$lemma"
done > analogical_all.tex
echo "Done: analogical_all.tex"

# Per-stemclass files
for filename in "${!STEMFILES[@]}"; do
    stemval="${STEMFILES[$filename]}"
    outpath="$OUTDIR/$filename"
    echo "Generating $filename (stem=\"$stemval\")..."
    get_lemmas_for_stem "$stemval" | while read lemma; do
        python3 "$SCRIPT" "$lemma"
    done > "$outpath"
    count=$(grep '^%---------' "$outpath" | wc -l)
    echo "  -> $count entries"
done

echo ""
echo "All done."
