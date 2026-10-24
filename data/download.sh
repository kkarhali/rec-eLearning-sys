#!/usr/bin/env bash
# Acquire the thesis datasets from GitHub mirrors and verify their integrity.
#
# The official hosts (analyse.kmi.open.ac.uk, UCI, Harvard Dataverse) are not
# reachable from the research sandbox, so the data is cloned from public GitHub
# mirrors and then checked against published MD5 sums / row counts.
# Official sources to cite:
#   OULAD : Kuzilek, Hlosta & Zdrahal (2017), Sci. Data 4:170171 — CC BY 4.0
#           https://analyse.kmi.open.ac.uk/open-dataset
set -euo pipefail
cd "$(dirname "$0")/.."
TMP=$(mktemp -d)
mkdir -p data/raw/oulad

echo "== OULAD studentVle shards (mirror: LuongAnh1/oulad-data-warehouse, raw_data/)"
GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 https://github.com/LuongAnh1/oulad-data-warehouse "$TMP/oulad-dw"
cp "$TMP/oulad-dw/raw_data/"studentVle_*.csv data/raw/oulad/

echo "== OULAD six small tables, byte-identical originals (mirror: reyquiroz/OULAD_CourseAware, data/raw/)"
GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 https://github.com/reyquiroz/OULAD_CourseAware "$TMP/oulad-ca"
for t in assessments courses studentAssessment studentInfo studentRegistration vle; do
  cp "$TMP/oulad-ca/data/raw/$t.csv" data/raw/oulad/
done

# MARS (Mandarine Academy) is NOT downloaded: its official page requires a request
# form and permits non-commercial research only, so GitHub mirrors do not satisfy
# the licence gate (ADR-001, D-02/D-03). See docs/decisions/ADR-001 addendum.

rm -rf "$TMP"
echo "== verifying OULAD"
python3 data/verify_oulad.py
