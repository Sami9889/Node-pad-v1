#!/usr/bin/env bash
# NodePad — end-to-end build pipeline
#
# Usage:
#   ./build.sh base    # base NodePad variant
#   ./build.sh net     # NodePad-Net (SFP + dual 2.5G) variant
#
# What it does:
#   1. Runs SKiDL to generate the netlist
#   2. Imports the netlist into KiCad PCB (places all footprints in a grid)
#   3. Exports Gerbers + drill files (ready for JLCPCB)
#   4. Exports the JLC PCBA-format BOM.csv + centroid (CPL.csv)
#   5. Exports 3D render + assembly drawings
#
# Prerequisites (one-time):
#   pip install skidl==2.2.3
#   git clone --depth 1 --branch 9.0.0 \
#       https://gitlab.com/kicad/libraries/kicad-symbols.git ~/kicad-symbols
#   git clone --depth 1 --branch 9.0.0 \
#       https://gitlab.com/kicad/libraries/kicad-footprints.git ~/kicad-footprints
#   Install KiCad 10 on the host (Debian: apt install kicad from backports,
#   Windows/Mac: download from kicad.org)

set -euo pipefail

VARIANT="${1:-base}"
case "$VARIANT" in
    base) MAIN="main.py";     OUT_BASE="nodepad" ;;
    net)  MAIN="main_net.py"; OUT_BASE="nodepad_net" ;;
    *) echo "usage: $0 {base|net}"; exit 1 ;;
esac

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
export KICAD_SYMBOL_DIR="${KICAD_SYMBOL_DIR:-$HOME/kicad-symbols}"
export KICAD9_SYMBOL_DIR="$KICAD_SYMBOL_DIR"

PROD_DIR="$REPO_ROOT/Production/$VARIANT"
mkdir -p "$PROD_DIR"

# ---- 1. Generate netlist ----------------------------------------------
echo "==> Generating netlist ($VARIANT variant)"
cd "$REPO_ROOT/PCB/skidl"
python3 "$MAIN"
NETLIST="$REPO_ROOT/PCB/skidl/netlists/${OUT_BASE}.net"
[ -f "$NETLIST" ] || { echo "ERROR: netlist not generated"; exit 1; }
echo "    OK: $NETLIST"

# ---- 2. Import netlist into PCB (auto-place in grid) -------------------
echo "==> Importing netlist into KiCad PCB"
PCB="$REPO_ROOT/PCB/NodePad.kicad_pcb"
if command -v kicad-cli >/dev/null 2>&1; then
    # KiCad 10 doesn't have a direct "import netlist to PCB" CLI subcommand,
    # so use the pcbnew Python API instead
    python3 "$REPO_ROOT/scripts/apply_netlist.py" "$PCB" "$NETLIST" || {
        echo "    WARNING: automated import failed — do this manually in KiCad:"
        echo "      File -> Import -> KiCad Netlist -> $NETLIST"
    }
else
    echo "    WARNING: kicad-cli not on PATH; skipping automated PCB import."
    echo "    Do this manually in KiCad's Pcbnew:"
    echo "      File -> Import -> KiCad Netlist -> $NETLIST"
fi

# ---- 3. DRC check ------------------------------------------------------
echo "==> Running DRC"
kicad-cli pcb drc --output "$PROD_DIR/drc-report.txt" --format report \
    --severity-error "$PCB" || echo "    (DRC violations found; see report)"

# ---- 4. Export Gerbers -------------------------------------------------
echo "==> Exporting Gerbers"
mkdir -p "$PROD_DIR/gerbers"
kicad-cli pcb export gerbers \
    --output "$PROD_DIR/gerbers/" \
    --layers "F.Cu,B.Cu,In1.Cu,In2.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts,F.Fab,B.Fab" \
    --subtract-soldermask --no-protel-ext \
    "$PCB"

kicad-cli pcb export drill \
    --output "$PROD_DIR/gerbers/" \
    --format excellon --drill-origin absolute \
    --excellon-zeros-format decimal --excellon-units mm \
    --excellon-separate-th --generate-map --map-format gerberx2 \
    "$PCB"

(cd "$PROD_DIR/gerbers" && zip -q "../${OUT_BASE}_gerbers.zip" *.gbr *.drl *.gm* *.gbrjob 2>/dev/null || true)
echo "    OK: $PROD_DIR/${OUT_BASE}_gerbers.zip"

# ---- 5. Export component-position file (CPL) for JLC PCBA -------------
echo "==> Exporting CPL (component placement)"
kicad-cli pcb export pos \
    --output "$PROD_DIR/${OUT_BASE}_cpl.csv" \
    --units mm --format csv --side both \
    --use-drill-file-origin "$PCB"

# ---- 6. Export BOM (JLC PCBA format: Comment / Designator / Footprint / LCSC) -----
echo "==> Exporting BOM (JLC PCBA format)"
kicad-cli sch export bom \
    --output "$PROD_DIR/${OUT_BASE}_bom.csv" \
    --fields 'Reference,Value,Footprint,LCSC Part #,${QUANTITY}' \
    --labels 'Designator,Comment,Footprint,LCSC Part #,Quantity' \
    --group-by 'Value,Footprint,LCSC Part #' \
    "$REPO_ROOT/PCB/NodePad.kicad_sch"

# ---- 7. 3D render (nice-to-have preview) ------------------------------
echo "==> Rendering 3D preview"
kicad-cli pcb render \
    --output "$PROD_DIR/${OUT_BASE}_3d_top.png" \
    --side top --background transparent \
    --width 1600 --height 1600 \
    "$PCB" || echo "    (3D render skipped)"

echo ""
echo "==> DONE. Artifacts in $PROD_DIR:"
ls -la "$PROD_DIR"
echo ""
echo "Upload to JLCPCB:"
echo "  1. https://cart.jlcpcb.com/quote  ->  drop $PROD_DIR/${OUT_BASE}_gerbers.zip"
echo "  2. Enable 'PCB Assembly'"
echo "  3. Upload BOM: $PROD_DIR/${OUT_BASE}_bom.csv"
echo "  4. Upload CPL: $PROD_DIR/${OUT_BASE}_cpl.csv"
echo "  5. Confirm parts, place order (~\$150 for 5 boards + assembly)"
