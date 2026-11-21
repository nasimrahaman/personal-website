#!/usr/bin/env python3
"""Keep Fig. 1 on the home page true: the light that left Earth in 1993, on a map of the bright stars around the Sun.

    python3 tools/lightcone.py          set the figure in docs/index.html to this year
    python3 tools/lightcone.py 2031     the same, for another year
    python3 tools/lightcone.py --check  compare the stars' numbers with SIMBAD

The numbers live in docs/lightcone.js: the year the light left, and a table of
the bright stars with their parallaxes and galactic longitudes. In a browser
that script redraws the figure for the year it is opened in. The copy of the
figure in docs/index.html is what a reader without scripts sees. It carries
its year, so it is never wrong, only old, and the first form brings it up to
date. It changes numbers, and which lines are dotted or hidden, and nothing
else: which stars are drawn, where their names sit and the caption are edited
in the page.

Everything is counted in whole years from the year 1993 and nothing finer. The
light is (year - 1993) light-years out. Do not add a month or a day, or any
number that would need one.

--check asks SIMBAD for the position, the parallax and the V magnitude of each
star in the table, by the star's name, and sends it nothing else.
"""
import argparse
import csv
import datetime
import io
import math
import pathlib
import re
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "index.html"
SCRIPT = ROOT / "docs" / "lightcone.js"
SIMBAD = ("https://simbad.cds.unistra.fr/simbad/sim-tap/sync", "https://simbad.harvard.edu/simbad/sim-tap/sync")
THIN = "\N{NARROW NO-BREAK SPACE}"


def numbers():
    """What docs/lightcone.js knows: its constants and its table of stars."""
    text = SCRIPT.read_text(encoding="utf-8")
    found = {name: re.search(rf"const {name} = ([\d.]+);", text) for name in ("FROM", "AHEAD", "LY_MAS", "CENTRE_PC")}
    table = re.search(r"const STARS = \[(.*?)\n  \];", text, re.S)
    if not (all(found.values()) and table):
        sys.exit("docs/lightcone.js: cannot find FROM, AHEAD, LY_MAS, CENTRE_PC or STARS")
    known = {name: float(match[1]) for name, match in found.items()}
    row = r'\{ name: "([^"]+)", id: "([^"]+)", plx: ([\d.]+), v: (-?[\d.]+), l: ([\d.]+) \}'
    stars = []
    for name, star, plx, v, l in re.findall(row, table[1]):
        ly = known["LY_MAS"] / float(plx)
        a = math.radians(float(l))
        # Seen from above the north pole of the Galaxy, y down the page: as in the script.
        stars.append({"name": name, "id": star, "plx": float(plx), "v": float(v), "l": float(l), "ly": ly, "x": ly * math.cos(a), "y": -ly * math.sin(a)})
    if len(stars) != table[1].count("{"):
        sys.exit("docs/lightcone.js: a row of STARS is not written like the others")
    return int(known["FROM"]), int(known["AHEAD"]), known["LY_MAS"], known["CENTRE_PC"], stars


# The figure in the page


def put(figure, pattern, value, what):
    """Replace what sits between the two groups of a pattern, which has to match once."""
    figure, count = re.subn(pattern, lambda match: match[1] + value + match[2], figure, flags=re.S)
    if count != 1:
        sys.exit(f"docs/index.html: Fig. 1 should have one {what}, and has {count}")
    return figure


def listed(things):
    return things[0] if len(things) == 1 else ", ".join(things[:-1]) + " and " + things[-1]


def thousands(n):
    """27000 as it is set on the site: 27 000, with a narrow space that does not break."""
    return f"{n:,}".replace(",", THIN)


def kinds(first, others, ahead):
    """A class list: what the thing is, whether the light has yet to reach it, and whatever else the page gave it."""
    return " ".join([first] + (["ahead"] if ahead else []) + [kind for kind in others.split() if kind != "ahead"])


def refresh(year):
    """Set every number in the figure to what it is in a year."""
    start, reach, unit, centre, stars = numbers()
    front = year - start
    if front < 1:
        sys.exit(f"the light left in {start}; {year} is not after that")
    table = {star["name"]: star for star in stars}

    page = PAGE.read_text(encoding="utf-8")
    found = re.search(r'<figure class="cone".*?</figure>', page, re.S)
    if not found:
        sys.exit('docs/index.html: no <figure class="cone"> to bring up to date')
    figure = found[0]

    figure = put(figure, r'(<div class="chart" style="--front: )[\d.]+(")', str(front), "--front")
    figure = put(figure, r'(<svg viewBox=")[^"]*(")', f"{-front} {-front} {2 * front} {2 * front}", "viewBox")
    for name, length, wanted in (("years", "0.6", lambda n: n % 10), ("tens", "1.2", lambda n: not n % 10)):
        d = "".join(f"M{n} 0v{length}" for n in range(1, front + 1) if wanted(n))
        figure = put(figure, rf'(<path class="{name}" d=")[^"]*(")', d, f"path of {name}")
    figure = put(figure, r'(<line class="axis" x2=")[\d.]+(")', str(front), "line to the centre")
    figure = put(figure, r'(<circle class="light" r=")[\d.]+(")', str(front), "circle")

    # The stars the page draws: each has a line in the drawing and, on a line
    # of its own in the page, the point where that line ends, with its name.
    ray = re.compile(r'<line class="ray([^"]*)" data-star="([^"]+)" x2="[^"]*" y2="[^"]*"(?: hidden)? />')
    mark = re.compile(r'<span class="star([^"]*)" data-star="([^"]+)" style="--x: [^;"]+; --y: [^;"]+"(?: hidden)?>')
    drawn = {"line": [], "name": []}
    lines = figure.split("\n")
    for i, line in enumerate(lines):
        for what, pattern in (("line", ray), ("name", mark)):
            match = pattern.search(line)
            if not match:
                continue
            star = table.get(match[2])
            if not star:
                sys.exit(f"docs/index.html: Fig. 1 draws {match[2]}, which is not in docs/lightcone.js")
            drawn[what].append(star["name"])
            ahead = star["ly"] > front
            hidden = " hidden" if star["ly"] > front + reach else ""
            if what == "line":
                new = f'<line class="{kinds("ray", match[1], ahead)}" data-star="{star["name"]}" x2="{star["x"]:.3f}" y2="{star["y"]:.3f}"{hidden} />'
            else:
                new = f'<span class="{kinds("star", match[1], ahead)}" data-star="{star["name"]}" style="--x: {star["x"]:.3f}; --y: {star["y"]:.3f}"{hidden}>'
                line, count = re.subn(r'(<span class="at">)[\d.]+(</span>)', lambda at: at[1] + f"{star['ly']:.1f}" + at[2], line)
                if not count:
                    sys.exit(f"docs/index.html: Fig. 1 has no number for {star['name']}")
                match = pattern.search(line)
            lines[i] = line[: match.start()] + new + line[match.end() :]
    if sorted(drawn["line"]) != sorted(drawn["name"]) or len(set(drawn["line"])) != len(drawn["line"]) or not drawn["line"]:
        sys.exit("docs/index.html: every star in Fig. 1 needs one line and one name")
    figure = "\n".join(lines)

    shown = [star for star in stars if star["name"] in drawn["line"]]
    at = lambda star: f"{star['name']} at {star['ly']:.1f}"
    passed = [at(star) for star in shown if star["ly"] <= front]
    coming = [at(star) for star in shown if front < star["ly"] <= front + reach]
    far = thousands(round(centre * unit / 1e6) * 1000)
    spoken = "A map around the Sun, seen from above the plane of the Milky Way, with the centre of the Galaxy to the right. "
    spoken += "A line runs from the Sun towards each star and is as long as the star is far, in light-years. "
    spoken += f"The circle is the light that left Earth in {start}, {front} light-years out in {year}."
    spoken += f" Inside it are {listed(passed)}." if passed else ""
    spoken += f" Dotted lines run to the stars it reaches within {reach} years: {listed(coming)}." if coming else ""
    spoken += f" Sagittarius A*, at the centre of the Galaxy, is {far} light-years away."
    reading = f"{year} · {front} light-year{'' if front == 1 else 's'}"
    figure = put(figure, r'(<div class="chart"[^>]*?aria-label=")[^"]*(")', spoken, "aria-label")
    figure = put(figure, r'(<span class="place">.*?<span class="at">)[^<]*(</span>)', far, "distance to the centre")
    figure = put(figure, r'(<span class="readout"[^>]*>)[^<]*(</span>)', reading, "readout")

    PAGE.write_text(page[: found.start()] + figure + page[found.end() :], encoding="utf-8")
    print(reading + (f"; dotted: {listed(coming)}" if coming else ""))
    print("Names are placed by hand. If the year or the stars changed, look at the page, wide and narrow, before it is pushed.")


# SIMBAD

# From equatorial (ICRS) to galactic coordinates: the rotation in the
# Hipparcos catalogue (ESA 1997, volume 1, section 1.5.3).
GALACTIC = (
    (-0.0548755604162154, -0.8734370902348850, -0.4838350155487132),
    (+0.4941094278755837, -0.4448296299600112, +0.7469822444972189),
    (-0.8676661490190047, -0.1980763734312015, +0.4559837761750669),
)


def longitude(ra, dec):
    """Galactic longitude in degrees of a position given in degrees."""
    ra, dec = math.radians(ra), math.radians(dec)
    v = (math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec))
    x, y = (sum(row[i] * v[i] for i in range(3)) for row in GALACTIC[:2])
    return math.degrees(math.atan2(y, x)) % 360


def simbad(stars):
    """What SIMBAD holds for each star, by what SIMBAD calls it: position, parallax in mas and V magnitude."""
    names = ", ".join("'" + star["id"].replace("'", "''") + "'" for star in stars)
    ask = "SELECT i.id, b.ra, b.dec, b.plx_value, b.plx_err, b.plx_bibcode, f.V FROM ident AS i JOIN basic AS b ON b.oid = i.oidref "
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
    _, _, unit, _, stars = numbers()
    said = simbad(stars)
    wrong = 0
    for star in stars:
        row = said.get(star["id"])
        if not row or not row["plx_value"] or not row["ra"]:
            print(f"{star['name']:<15} SIMBAD has nothing under {star['id']!r}")
            wrong += 1
            continue
        plx, v = float(row["plx_value"]), float(row["V"]) if row["V"] else None
        l = longitude(float(row["ra"]), float(row["dec"]))
        turn = abs((l - star["l"] + 180) % 360 - 180)
        same = abs(plx - star["plx"]) < 0.005 and (v is None or abs(v - star["v"]) < 0.005) and turn < 0.002
        wrong += not same
        print(
            f"{star['name']:<15} here {star['plx']:7.2f} mas, V {star['v']:5.2f}, {star['ly']:6.2f} ly, l {star['l']:7.3f}   "
            f"SIMBAD {plx:7.2f} ± {float(row['plx_err'] or 0):.2f} mas, V {v if v is not None else float('nan'):5.2f}, "
            f"{unit / plx:6.2f} ly, l {l:7.3f}  {row['plx_bibcode']}  {'same' if same else 'DIFFERENT'}"
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
