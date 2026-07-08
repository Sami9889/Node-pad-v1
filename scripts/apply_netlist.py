#!/usr/bin/env python3
"""
apply_netlist.py — Parse KiCad netlist, drop every footprint onto the
board in a grid, save the PCB file so kicad-cli can then export gerbers.

This is a lightweight standalone implementation (no pcbnew binding
required) — we operate directly on the .kicad_pcb S-expr format that
we know from having built the empty board scaffold ourselves.
"""
import re, os, sys, glob, uuid

def read_sexpr_block(text, token):
    """Return the first top-level (token ...) block in text and its span."""
    idx = text.find(f"({token}")
    if idx == -1:
        return None, -1, -1
    depth = 0; j = idx
    in_str = False; esc = False
    while j < len(text):
        c = text[j]
        if esc:
            esc = False
        elif c == "\\":
            esc = True
        elif c == '"':
            in_str = not in_str
        elif not in_str:
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    return text[idx:j+1], idx, j+1
        j += 1
    return None, -1, -1


def load_footprint(fp_ref, libs_root):
    """
    fp_ref e.g. 'Capacitor_SMD:C_0402_1005Metric'
    Return the raw .kicad_mod S-expression as a string (or None if missing).
    """
    lib, name = fp_ref.split(":", 1)
    path = os.path.join(libs_root, f"{lib}.pretty", f"{name}.kicad_mod")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return f.read()


def instantiate_footprint(mod_text, ref, value, at_x, at_y, uid):
    """
    Turn a .kicad_mod file's contents (a (footprint ...) block) into a
    PCB-level (footprint ...) instance, positioned at (at_x, at_y).
    """
    # KiCad 10 .kicad_mod is a top-level (footprint "NAME" ... ) block.
    # We change:
    #   * the top-level name string stays (it's the lib id)
    #   * add (layer "F.Cu")
    #   * add (at X Y)
    #   * add (uuid "...") if missing
    #   * update the fp_text "reference" property value
    txt = mod_text.strip()
    if not txt.startswith("(footprint"):
        return None

    # Add layer + at inside the footprint block right after the name
    m = re.match(r'\((footprint\s+"[^"]+")', txt)
    if m:
        insertion = f'\n\t(layer "F.Cu")\n\t(at {at_x:.3f} {at_y:.3f})\n\t(uuid "{uid}")'
        txt = txt[:m.end()] + insertion + txt[m.end():]

    # Update reference designator inside the first (property "Reference" ...) block
    def sub_ref(match):
        prop = match.group(0)
        # replace the value string after "Reference"
        prop = re.sub(r'(\(property "Reference"\s+)"[^"]*"', rf'\1"{ref}"', prop, count=1)
        return prop
    txt = re.sub(r'\(property\s+"Reference"[^)]*\)(\s*\([^)]*\))*', sub_ref, txt, count=1)

    # Update value string similarly
    def sub_val(match):
        prop = match.group(0)
        prop = re.sub(r'(\(property "Value"\s+)"[^"]*"', rf'\1"{value}"', prop, count=1)
        return prop
    txt = re.sub(r'\(property\s+"Value"[^)]*\)(\s*\([^)]*\))*', sub_val, txt, count=1)

    return txt


def parse_netlist(netlist_path):
    """Return [(ref, value, footprint), ...]"""
    with open(netlist_path) as f:
        txt = f.read()
    comps = []
    for m in re.finditer(
        r'\(comp\s+\(ref\s+"([^"]+)"\)\s+\(value\s+"([^"]+)"\)(?:.*?)\(footprint\s+"([^"]+)"\)',
        txt, re.DOTALL):
        comps.append((m.group(1), m.group(2), m.group(3)))
    return comps


def main():
    if len(sys.argv) != 3:
        print("usage: apply_netlist.py <pcb> <netlist>"); sys.exit(1)
    pcb_path, netlist_path = sys.argv[1], sys.argv[2]
    libs = os.environ.get("KICAD_FOOTPRINT_DIR", "/opt/kicad-libs/footprints")

    comps = parse_netlist(netlist_path)
    print(f"Netlist has {len(comps)} components")

    with open(pcb_path) as f:
        pcb = f.read()

    # Cache footprint templates
    cache = {}
    missing = []

    # Grid layout: 100x100 board, place components on a 10x10 mm grid
    # starting at (10,45) so we don't collide with header text.
    footprints = []
    x0, y0 = 10.0, 45.0
    dx, dy = 5.5, 5.5
    per_row = 16
    for i, (ref, value, fp) in enumerate(comps):
        row = i // per_row
        col = i % per_row
        px = x0 + col * dx
        py = y0 + row * dy
        if fp not in cache:
            cache[fp] = load_footprint(fp, libs)
            if cache[fp] is None:
                missing.append(fp)
        template = cache[fp]
        if template is None:
            continue
        uid = str(uuid.uuid4())
        inst = instantiate_footprint(template, ref, value, px, py, uid)
        if inst:
            footprints.append(inst)

    print(f"Placed {len(footprints)} footprints; {len(missing)} unique footprints missing:")
    for m in sorted(set(missing))[:20]:
        print(f"   MISSING: {m}")

    # Insert footprints before the final closing paren of (kicad_pcb ... )
    # Find the last ')' and insert before it
    joined = "\n" + "\n".join(footprints) + "\n"
    # Insert just before the trailing ")"
    end = pcb.rstrip().rfind(")")
    new_pcb = pcb[:end] + joined + pcb[end:]

    out = pcb_path + ".placed"
    with open(out, "w") as f:
        f.write(new_pcb)
    # Replace original
    os.replace(out, pcb_path)
    print(f"Wrote {pcb_path}")


if __name__ == "__main__":
    main()
