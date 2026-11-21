#!/usr/bin/env python3
"""Set a line of text in the site's 5 x 7 pixel font.

    python3 tools/raster.py "NASIM RAHAMAN"          rows of the picture, as text
    python3 tools/raster.py "NO SIGNAL" --width 73   the same, centred in 73 columns
    python3 tools/raster.py "NASIM RAHAMAN" --path   the picture as an SVG path

The path is the picture in docs/name.svg, the name at the top of every page,
and in docs/404.html. If either text ever changes, its picture has to be made
again.
"""
import argparse

FONT = {
    "A": ["01110", "10001", "10001", "10001", "11111", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11100", "10010", "10001", "10001", "10001", "10010", "11100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["111", "010", "010", "010", "010", "010", "111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "10001", "11001", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "10001", "01010", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["010", "110", "010", "010", "010", "010", "111"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["000"] * 7,
}
HEIGHT = 7


def rows(text, width=None):
    """The picture as HEIGHT strings of 0 and 1. Letters are one column apart,
    so a space, three columns wide, puts words five columns apart."""
    picture = ["0".join(FONT[c][y] for c in text.upper()) for y in range(HEIGHT)]
    if width is not None:
        spare = width - len(picture[0])
        if spare < 0:
            raise SystemExit(f"{text!r} is {len(picture[0])} columns wide; it does not fit in {width}")
        left = spare // 2
        picture = ["0" * left + row + "0" * (spare - left) for row in picture]
    return picture


def path(picture, cell=0.86):
    """One square per lit cell, each centred in a unit cell."""
    inset = (1 - cell) / 2
    side = number(cell)
    squares = []
    for y, row in enumerate(picture):
        for x, bit in enumerate(row):
            if bit == "1":
                squares.append(f"M{number(x + inset)} {number(y + inset)}h{side}v{side}h-{side}z")
    return "".join(squares)


def number(value):
    """A coordinate to two decimals, without a leading or trailing zero."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text[1:] if text.startswith("0.") else text or "0"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("text")
    parser.add_argument("--width", type=int, help="centre the text in this many columns")
    parser.add_argument("--path", action="store_true", help="print an SVG path instead of rows")
    parser.add_argument("--cell", type=float, default=0.86, help="side of a lit square, in cells")
    args = parser.parse_args()
    picture = rows(args.text, args.width)
    if args.path:
        print(path(picture, args.cell))
    else:
        for row in picture:
            print(row.replace("0", ".").replace("1", "#"))
        print(f"{len(picture[0])} x {HEIGHT} = {len(picture[0]) * HEIGHT} bits")
