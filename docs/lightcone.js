/*
 * Fig. 1: how far the light has got.
 *
 * One line out from Earth, to scale, in light-years. Its solid part is as
 * long as the light that left Earth in 1993 has travelled. The marks are the
 * bright stars, each at its distance, so the ones on the solid part are the
 * ones that light has passed. The faint part runs on to the next one.
 *
 * The line starts at the Sun, the first star that light passed, eight minutes
 * out. At this scale it stands where Earth does: 1 au is about 0.000016
 * light-years. So the distances are the catalogue ones, which are measured
 * from the Sun.
 *
 * Everything is counted in whole years, from the year 1993 and nothing finer:
 * the light is (this year − 1993) light-years out, and steps forward at New
 * Year. A number that needed a month or a day to work out is not in the figure.
 *
 * The page already contains the figure as it stood in the year in its
 * readout, put there by tools/lightcone.py. This script brings it up to this
 * year and lets a pointer read the line. Nothing moves until the reader
 * moves it.
 */
(() => {
  "use strict";

  const figure = document.querySelector(".reach");
  const scale = figure && figure.querySelector(".scale");
  const svg = scale && scale.querySelector("svg");
  const readout = figure && figure.querySelector(".readout");
  if (!svg || !readout) return;

  const FROM = 1993;

  // The first-magnitude stars, which are the ones brighter than V = 1.5, out
  // to 70 light-years, nearest first. There are ten, and the eleventh
  // (Regulus) is at 79. For each: its name, what SIMBAD calls it, its
  // parallax in milliarcseconds and its V magnitude.
  //
  // Source: SIMBAD (simbad.cds.unistra.fr, read through its mirror at
  // simbad.harvard.edu), the parallax it adopts for each star. Retrieved
  // 2026-11-21. All are from the 2007 reduction of Hipparcos (van Leeuwen,
  // 2007A&A...474..653V) except Alpha Centauri.
  // tools/lightcone.py --check compares this table with SIMBAD.
  //
  // Alpha Centauri is the pair A and B as one: 750.81 ± 0.38 mas (Akeson and
  // others, 2021AJ....162...14A), which is 4.34 light-years. SIMBAD's entry
  // for A alone still has the first Hipparcos value, 742.12 ± 1.40 mas, which
  // is 4.39. The figure uses the pair's, the newer and the tighter of the two,
  // so it says 4.3 where older tables say 4.4.
  //
  // Sirius is given as 8.6 light-years here and as 8.7 elsewhere. Hipparcos
  // measured Sirius itself: 379.21 ± 1.58 mas, which is 8.60 light-years. Gaia
  // cannot, because the star is too bright for it, and has only the faint
  // companion Sirius B: 374.49 ± 0.23 mas (Gaia DR3), which is 8.71. The
  // figure uses Hipparcos, because that is a measurement of the star that is
  // marked, and it comes from the same catalogue as the stars either side.
  //
  // Fomalhaut is 0.08 light-years farther than Vega, which is less than three
  // pixels on the widest page. It is drawn on Vega's mark.
  const STARS = [
    { name: "Alpha Centauri", id: "* alf Cen", plx: 750.81, v: -0.1 },
    { name: "Sirius", id: "* alf CMa", plx: 379.21, v: -1.46 },
    { name: "Procyon", id: "* alf CMi", plx: 284.56, v: 0.37 },
    { name: "Altair", id: "* alf Aql", plx: 194.95, v: 0.76 },
    { name: "Vega", id: "* alf Lyr", plx: 130.23, v: 0.03 },
    { name: "Fomalhaut", id: "* alf PsA", plx: 129.81, v: 1.16, on: "Vega" },
    { name: "Pollux", id: "* bet Gem", plx: 96.54, v: 1.14 },
    { name: "Arcturus", id: "* alf Boo", plx: 88.83, v: -0.05 },
    { name: "Capella", id: "* alf Aur", plx: 76.2, v: 0.08 },
    { name: "Aldebaran", id: "* alf Tau", plx: 48.94, v: 0.86 },
  ];

  // A star's distance in light-years is this over its parallax in mas: a
  // parsec is 648 000 / π au, and a light-year is 63 241.077 au.
  const LY_MAS = 3261.5638;

  // A name within this share of the line from its right-hand end is set to
  // end at its mark, where the others begin at theirs.
  const FLIP = 0.22;

  const pick = (selector) => svg.querySelector(selector);
  const parts = {
    years: pick(".years"),
    tens: pick(".tens"),
    line: pick(".line"),
    beyond: pick(".beyond"),
    needle: pick(".needle"),
  };
  const sun = scale.querySelector(".sun");
  const marks = [...scale.querySelectorAll(".star:not(.sun)")];
  const stars = STARS.filter((star) => !star.on).map((star) => ({ ...star, ly: LY_MAS / star.plx }));
  if (Object.values(parts).includes(null) || marks.length !== stars.length) return;

  // Down the page the drawing is the markup's business. All this needs to
  // know is where the line is.
  const LINE = parts.line.getAttribute("y1");
  const TALL = svg.viewBox.baseVal.height;

  const year = new Date().getFullYear();
  const front = year - FROM;
  // The next star is the nearest one the light has not reached, and the
  // drawing is as wide as that star is far. After the last star in the
  // table, it is as wide as the light has gone.
  const next = stars.findIndex((star) => star.ly > front);
  const end = next < 0 ? front : stars[next].ly;

  // The readout: a year, and how far out the light was in it. The number is
  // padded so that nothing shifts as it changes.
  function say(ly) {
    const far = String(ly).padStart(2, "\u00a0");
    readout.textContent = `${FROM + ly} · ${far} light-year${ly === 1 ? "\u00a0" : "s"}`;
  }

  const list = (names) => (names.length > 1 ? `${names.slice(0, -1).join(", ")} and ${names.at(-1)}` : names[0]);

  // Bring the drawing up to this year.
  function update() {
    const x = end.toFixed(3);
    svg.setAttribute("viewBox", `0 0 ${x} ${TALL}`);
    scale.style.setProperty("--end", x);

    let years = "";
    let tens = "";
    for (let ly = 1; ly <= front; ly++) {
      if (ly % 10) years += `M${ly} ${LINE}v0.33`;
      else tens += `M${ly} ${LINE}v0.67`;
    }
    parts.years.setAttribute("d", years);
    parts.tens.setAttribute("d", tens);
    parts.beyond.setAttribute("x1", front);
    parts.beyond.setAttribute("x2", x);
    parts.line.setAttribute("x2", front);

    marks.forEach((mark, i) => {
      const passed = next < 0 || i < next;
      mark.hidden = !passed && i !== next;
      mark.classList.toggle("next", i === next);
      mark.classList.toggle("flip", passed && (end - stars[i].ly) / end < FLIP);
    });

    const passed = STARS.filter((star) => LY_MAS / star.plx <= front);
    const at = (star) => `${star.name} at ${(LY_MAS / star.plx).toFixed(1)}`;
    scale.setAttribute(
      "aria-label",
      "A scale of distance from Earth in light-years, with the Sun at the start of the line. " +
        `Light that left Earth in ${FROM} is ${front} light-years out in ${year}.` +
        (passed.length ? ` It has passed ${list(passed.map(at))}.` : "") +
        (next < 0 ? "" : ` The next bright star is ${stars[next].name}, at ${stars[next].ly.toFixed(1)}.`)
    );
  }

  // Where there is no room, the fainter star gives way: first whole stars
  // whose names would touch another name or stand in the way of a post, then
  // the numbers of the ones that are left. The page is set by hand for the
  // stars of the 2020s, and this changes nothing there. It is for later, when
  // there are more of them on the same line.
  const GAP = 6; // px
  const order = marks.map((mark, i) => ({ mark, rank: i === next ? -Infinity : stars[i].v }));
  order.sort((a, b) => a.rank - b.rank);
  const near = (a, b) =>
    a.left < b.right + GAP && b.left < a.right + GAP && a.top < b.bottom - 1 && b.top < a.bottom - 1;
  function declutter() {
    const bounds = scale.getBoundingClientRect();
    const line = bounds.top + (LINE / TALL) * bounds.height;
    for (const { mark } of order) mark.classList.remove("crowded", "numberless");

    const names = [];
    const posts = [];
    const numbers = [];
    for (const { mark, rank } of [{ mark: sun, rank: -Infinity }, ...order]) {
      const name = mark.querySelector(".name").getBoundingClientRect();
      if (!name.width) continue;
      const x = mark.getBoundingClientRect().left;
      const post = { left: x, right: x + 1, top: name.bottom, bottom: line };
      const crowded =
        name.right > bounds.right + 3 ||
        names.some((other) => near(name, other) || near(post, other)) ||
        posts.some((other) => near(name, other));
      if (crowded && rank > -Infinity) {
        mark.classList.add("crowded");
        continue;
      }
      names.push(name);
      posts.push(post);
    }
    for (const { mark, rank } of order) {
      const text = mark.querySelector(".at");
      const number = text && text.getBoundingClientRect();
      if (!number || !number.width) continue;
      if (rank > -Infinity && (number.right > bounds.right + 3 || numbers.some((other) => near(number, other)))) {
        mark.classList.add("numberless");
      } else numbers.push(number);
    }
  }

  // One thing moves: the needle that reads the line. It rests on the front
  // of the light.
  function point(ly) {
    parts.needle.setAttribute("x1", ly.toFixed(3));
    parts.needle.setAttribute("x2", ly.toFixed(3));
  }
  function rest() {
    point(front);
    say(front);
  }

  // A pointer on the line reads it, a whole year at a time: the year in which
  // the light was, or will be, that far out.
  function read(event) {
    const box = scale.getBoundingClientRect();
    const reach = box.width - 1;
    const x = Math.min(Math.max(event.clientX - box.left - 0.5, 0), reach);
    const ly = Math.min(Math.round((x / reach) * end), Math.floor(end));

    figure.classList.add("live");
    point(ly);
    say(ly);
  }
  function release() {
    figure.classList.remove("live");
    rest();
  }

  update();
  rest();
  declutter();
  figure.classList.add("readable");

  scale.addEventListener("pointerdown", (event) => {
    if (event.pointerType !== "mouse") scale.setPointerCapture(event.pointerId);
    read(event);
  });
  scale.addEventListener("pointermove", (event) => {
    if (event.pointerType === "mouse" || scale.hasPointerCapture(event.pointerId)) read(event);
  });
  scale.addEventListener("pointerup", (event) => {
    if (event.pointerType !== "mouse") release();
  });
  scale.addEventListener("pointerleave", release);
  scale.addEventListener("pointercancel", release);
  addEventListener("resize", declutter);
  if (document.fonts) document.fonts.ready.then(declutter);
})();
