"""Minimal .xlsx reader (standard library only).

Returns each sheet as a list of rows; each row is a list of cell values
(str, float or None). Formula cells yield their cached value, if any.
"""
import re
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "pr": "http://schemas.openxmlformats.org/package/2006/relationships"}


def _col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def _text(node):
    if node is None:
        return ""
    return "".join(t.text or "" for t in node.iter("{%s}t" % NS["m"]))


def _fills(z):
    """cellXfs index -> solid fill RGB (e.g. 'FFF2F2F2') or None."""
    try:
        st = ET.fromstring(z.read("xl/styles.xml"))
    except KeyError:
        return []
    fills = []
    for f in st.findall("m:fills/m:fill", NS):
        fg = f.find("m:patternFill/m:fgColor", NS)
        fills.append(fg.get("rgb") if fg is not None else None)
    out = []
    for xf in st.findall("m:cellXfs/m:xf", NS):
        i = int(xf.get("fillId", 0))
        out.append(fills[i] if i < len(fills) else None)
    return out


def read_workbook(path, fills=None):
    """Return {sheet_name: [[value, ...], ...]}.

    If a dict is passed as `fills`, it is filled with
    {sheet_name: {(row, col): 'AARRGGBB'}} for cells with a solid fill.
    """
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = [_text(si) for si in root.findall("m:si", NS)]
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = {r.get("Id"): r.get("Target") for r in rels.findall("pr:Relationship", NS)}
        styles = _fills(z) if fills is not None else []
        out = {}
        for sh in wb.findall("m:sheets/m:sheet", NS):
            rid = sh.get("{%s}id" % NS["r"])
            t = target[rid].lstrip("/")
            part = t if t.startswith("xl/") else "xl/" + t
            sheet_fill = {}
            out[sh.get("name")] = _read_sheet(z.read(part), shared, styles, sheet_fill)
            if fills is not None:
                fills[sh.get("name")] = sheet_fill
        return out


def _read_sheet(data, shared, styles=(), fill=None):
    root = ET.fromstring(data)
    rows = []
    for row in root.iter("{%s}row" % NS["m"]):
        idx = int(row.get("r")) - 1
        while len(rows) < idx:
            rows.append([])
        cells = []
        for c in row.findall("m:c", NS):
            col = _col_index(c.get("r"))
            si = c.get("s")
            if styles and si is not None and int(si) < len(styles) and styles[int(si)]:
                fill[(idx, col)] = styles[int(si)]
            while len(cells) < col:
                cells.append(None)
            t = c.get("t")
            v = c.find("m:v", NS)
            if t == "inlineStr":
                val = _text(c.find("m:is", NS))
            elif v is None:
                val = None
            elif t == "s":
                val = shared[int(v.text)]
            elif t in ("str", "e"):
                val = v.text
            elif t == "b":
                val = v.text == "1"
            else:
                try:
                    val = float(v.text)
                except (TypeError, ValueError):
                    val = v.text
            cells.append(val)
        rows.append(cells)
    return rows
