#!/usr/bin/env python3
"""Keep Fig. 1 on the home page true: the line of light that left Earth in 1993.

    python3 tools/lightcone.py          set the figure in docs/index.html to this year
    python3 tools/lightcone.py 2031     the same, for another year
    python3 tools/lightcone.py --check  compare the stars' distances with SIMBAD

The numbers live in docs/lightcone.js: the year the light left, and a table of
the bright stars with their parallaxes. In a browser that script redraws the
figure for the year it is opened in. The copy of the figure in docs/index.html
is what a reader without scripts sees. It carries its year, so it is never
wrong, only old, and the first form brings it up to date. It changes numbers,
and which stars are shown, and nothing else: the names, the rows they sit on
and the caption are edited in the page.

Everything is counted in whole years from the year 1993 and nothing finer. The
light is (year - 1993) light-years out. Do not add a month or a day, or any
number that would need one.

--check asks SIMBAD for the parallax and the V magnitude of each star in the
table, by the star's name, and sends it nothing else.
"""
import argparse
import csv
import datetime
import io
import pathlib
import re
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "index.html"
SCRIPT = ROOT / "docs" / "lightcone.js"
SIMBAD = ("https://simbad.cds.unistra.fr/simbad/sim-tap/sync", "https://simbad.harvard.edu/simbad/sim-tap/sync")


def numbers():
    """What docs/lightcone.js knows: the year, the stars, and the two constants it lays them out with."""
    text = SCRIPT.read_text(encoding="utf-8")
    year = re.search(r"const FROM = (\d{4});", text)
    unit = re.search(r"const LY_MAS = ([\d.]+);", text)
    flip = re.search(r"const FLIP = ([\d.]+);", text)
    table = re.search(r"const STARS = \[(.*?)\n  \];", text, re.S)
    if not (year and unit and flip and table):
        sys.exit("docs/lightcone.js: cannot find FROM, LY_MAS, FLIP or STARS")
    row = r'\{ name: "([^"]+)", id: "([^"]+)", plx: ([\d.]+), v: (-?[\d.]+)(?:, on: "([^"]+)")? \}'
    stars = [
        {"name": name, "id": star, "plx": float(plx), "v": float(v), "on": on or None, "ly": float(unit[1]) / float(plx)}
        for name, star, plx, v, on in re.findall(row, table[1])
    ]
    if len(stars) != table[1].count("{"):
        sys.exit("docs/lightcone.js: a row of STARS is not written like the others")
    return int(year[1]), stars, float(flip[1])


# The figure in the page


def put(figure, pattern, value, what):
    """Replace what sits between the two groups of a pattern, which has to match once."""
    figure, count = re.subn(pattern, lambda match: match[1] + value + match[2], figure, flags=re.S)
    if count != 1:
        sys.exit(f"docs/index.html: Fig. 1 should have one {what}, and has {count}")
    return figure


def listed(things):
    return things[0] if len(things) == 1 else ", ".join(things[:-1]) + " and " + things[-1]


def refresh(year):
    """Set every number in the figure to what it is in a year."""
    start, stars, flip = numbers()
    front = year - start
    if front < 0:
        sys.exit(f"the light left in {start}; {year} is before that")
    marks = [star for star in stars if not star["on"]]
    ahead = [i for i, star in enumerate(marks) if star["ly"] > front]
    nearest = ahead[0] if ahead else None
    end = f"{marks[nearest]['ly'] if ahead else front:.3f}"

    page = PAGE.read_text(encoding="utf-8")
    found = re.search(r'<figure class="reach">.*?</figure>', page, re.S)
    if not found:
        sys.exit('docs/index.html: no <figure class="reach"> to bring up to date')
    figure = found[0]

    figure = put(figure, r'(style="--end: )[\d.]+(")', end, "--end")
    figure = put(figure, r'(viewBox="0 0 )[\d.]+( )', end, "viewBox")
    line = re.search(r'<line class="line"[^>]*\by1="([\d.]+)"', figure)
    if not line:
        sys.exit("docs/index.html: Fig. 1 has no line to hang the divisions from")
    for name, length, wanted in (("years", "0.33", lambda n: n % 10), ("tens", "0.67", lambda n: not n % 10)):
        d = "".join(f"M{n} {line[1]}v{length}" for n in range(1, front + 1) if wanted(n))
        figure = put(figure, rf'(<path class="{name}" d=")[^"]*(")', d, f"path of {name}")
    figure = put(figure, r'(<line class="line"[^>]*\bx2=")[\d.]+(")', str(front), "x2 on the line")
    figure = put(figure, r'(<line class="beyond"[^>]*\bx1=")[\d.]+(")', str(front), "x1 on the line beyond")
    figure = put(figure, r'(<line class="beyond"[^>]*\bx2=")[\d.]+(")', end, "x2 on the line beyond")
    for x in ("x1", "x2"):
        figure = put(figure, rf'(<line class="needle"[^>]*\b{x}=")[\d.]+(")', str(front), f"{x} on the needle")

    # The stars: where each is, what it says under the line, and whether the
    # light has passed it, is about to, or has a star still to pass first.
    for i, star in enumerate(marks):
        name = re.escape(star["name"])
        tag = rf'<span class="star\b[^"]*" style="--at: [\d.]+;([^"]*)"(?: hidden)?>(?=<span class="name">{name}\b)'
        opened = re.search(tag, figure)
        if not opened or len(re.findall(tag, figure)) != 1:
            sys.exit(f"docs/index.html: Fig. 1 should have one star named {star['name']}")
        passed = nearest is None or i < nearest
        kinds = ["star"]
        kinds += ["next"] if i == nearest else []
        kinds += ["flip"] if passed and (float(end) - star["ly"]) / float(end) < flip else []
        kinds += ["if-room"] if "if-room" in opened[0].split('"')[1].split() else []
        hidden = "" if passed or i == nearest else " hidden"
        new = f'<span class="{" ".join(kinds)}" style="--at: {star["ly"]:.3f};{opened[1]}"{hidden}>'
        figure = figure[: opened.start()] + new + figure[opened.end() :]
        figure = put(figure, rf'(<span class="name">{name}\b.*?<span class="at">)[\d.]+()', f"{star['ly']:.1f}", f"number for {star['name']}")
    for star in stars:
        if star["on"]:
            host = re.escape(star["on"])
            pattern = rf'(<span class="name">{host}\b.*?<span class="at">[\d.]+<span class="if-room">, )[\d.]+(</span>)'
            figure = put(figure, pattern, f"{star['ly']:.1f}", f"number for {star['name']}")

    passed = [f"{star['name']} at {star['ly']:.1f}" for star in stars if star["ly"] <= front]
    spoken = "A scale of distance from Earth in light-years, with the Sun at the start of the line. "
    spoken += f"Light that left Earth in {start} is {front} light-years out in {year}."
    spoken += f" It has passed {listed(passed)}." if passed else ""
    spoken += f" The next bright star is {marks[nearest]['name']}, at {marks[nearest]['ly']:.1f}." if ahead else ""
    reading = f"{year} · {front} light-year{'' if front == 1 else 's'}"
    figure = put(figure, r'(<div\b[^>]*?aria-label=")[^"]*(")', spoken, "aria-label")
    figure = put(figure, r'(<span class="readout"[^>]*>)[^<]*(</span>)', reading, "readout")

    PAGE.write_text(page[: found.start()] + figure + page[found.end() :], encoding="utf-8")
    print(reading + (f"; the next star is {marks[nearest]['name']}, at {marks[nearest]['ly']:.1f}" if ahead else ""))


# SIMBAD


def simbad(stars):
    """The parallax in mas and the V magnitude SIMBAD holds for each star, by what SIMBAD calls it."""
    names = ", ".join("'" + star["id"].replace("'", "''") + "'" for star in stars)
    ask = "SELECT i.id, b.plx_value, b.plx_err, b.plx_bibcode, f.V FROM ident AS i JOIN basic AS b ON b.oid = i.oidref "
    ask += f"LEFT JOIN allfluxes AS f ON f.oidref = b.oid WHERE i.id IN ({names})"
    form = urllib.parse.urlencode({"request": "doQuery", "lang": "adql", "format": "csv", "query": ask}).encode()
    for address in SIMBAD:
        try:
            with urllib.request.urlopen(address, form, timeout=60) as reply:
                rows = list(csv.DictReader(io.StringIO(reply.read().decode("utf-8"))))
        except OSError as error:
            print(f"{address} did not answer: {error}", file=sys.stderr)
            continue
        if rows and "plx_value" in rows[0]:
            return {row["id"]: row for row in rows}
        print(f"{address} answered without a table", file=sys.stderr)
    sys.exit("SIMBAD could not be asked")


def check():
    """Print the numbers in docs/lightcone.js beside what SIMBAD says."""
    _, stars, _ = numbers()
    said = simbad(stars)
    unit = stars[0]["ly"] * stars[0]["plx"]
    wrong = 0
    for star in stars:
        row = said.get(star["id"])
        if not row or not row["plx_value"]:
            print(f"{star['name']:<15} SIMBAD has nothing under {star['id']!r}")
            wrong += 1
            continue
        plx, v = float(row["plx_value"]), float(row["V"]) if row["V"] else None
        same = abs(plx - star["plx"]) < 0.005 and (v is None or abs(v - star["v"]) < 0.005)
        wrong += not same
        print(
            f"{star['name']:<15} here {star['plx']:7.2f} mas, V {star['v']:5.2f}, {star['ly']:6.2f} ly   "
            f"SIMBAD {plx:7.2f} ± {float(row['plx_err'] or 0):.2f} mas, V {v if v is not None else float('nan'):5.2f}, "
            f"{unit / plx:6.2f} ly  {row['plx_bibcode']}  {'same' if same else 'DIFFERENT'}"
        )
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("year", nargs="?", type=int, help="YYYY; this year if left out")
    parser.add_argument("--check", action="store_true", help="compare docs/lightcone.js with SIMBAD")
    args = parser.parse_args()
    if args.check:
        check()
    else:
        refresh(args.year or datetime.date.today().year)
