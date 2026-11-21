/*
 * Fig. 1: my light cone.
 *
 * A map around the Sun, seen from above the plane of the Milky Way, with the
 * centre of the Galaxy to the right. A line runs from the Sun towards each
 * bright star, in the star's direction and as long as the star is far. The
 * circle is the light that left Earth in 1993: its radius is how far that
 * light has travelled. A line that ends inside the circle is a star the light
 * has passed. A dotted line is a star it reaches within the next ten years.
 *
 * The form is borrowed from the map of pulsars on the Pioneer plaques and on
 * the cover of the Voyager record (Sagan, Salzman Sagan and Drake, Science
 * 175, 881, 1972), which also puts the Sun in the middle and the centre of
 * the Galaxy to the right. Nothing else of that map is here: these are
 * stars, not pulsars, and every length and direction is from today's
 * catalogues.
 *
 * A line's direction is the star's galactic longitude. Its length is the
 * star's whole distance, not the part of it that lies along the plane, so a
 * line that ends inside the circle is always a star the light has passed.
 * The map does not show how far above or below the plane a star is.
 *
 * The Sun is the first star that light passed, eight minutes out. At this
 * scale it stands where Earth does: 1 au is about 0.000016 light-years. So
 * the distances are the catalogue ones, which are measured from the Sun.
 *
 * Everything is counted in whole years, from the year 1993 and nothing finer:
 * the light is (this year − 1993) light-years out, and steps forward at New
 * Year. A number that needed a month or a day to work out is not in the
 * figure.
 *
 * The page already contains the figure as it stood in the year in its
 * readout, put there by tools/lightcone.py. This script brings it up to this
 * year and lets a pointer read it. Nothing moves until the reader moves it.
 *
 * Which stars are drawn, and where their names sit, is decided in the page.
 * A star in the table below that has no line in the page is not drawn.
 */
(() => {
  "use strict";

  const figure = document.querySelector(".cone");
  const chart = figure && figure.querySelector(".chart");
  const svg = chart && chart.querySelector("svg");
  const readout = figure && figure.querySelector(".readout");
  if (!svg || !readout) return;

  const FROM = 1993;

  // A star the light has not reached is drawn, dotted, if the light reaches
  // it within this many years.
  const AHEAD = 10;

  // The first-magnitude stars, which are the ones brighter than V = 1.5, out
  // to 70 light-years, nearest first. There are ten, and the eleventh
  // (Regulus) is at 79. For each: its name, what SIMBAD calls it, its
  // parallax in milliarcseconds, its V magnitude and its galactic longitude
  // in degrees.
  //
  // Source: SIMBAD (simbad.cds.unistra.fr, read through its mirror at
  // simbad.harvard.edu), the parallax and the position it adopts for each
  // star. Retrieved 2026-11-21. All are from the 2007 reduction of Hipparcos
  // (van Leeuwen, 2007A&A...474..653V) except Alpha Centauri.
  // tools/lightcone.py --check compares this table with SIMBAD.
  //
  // The longitude is worked out from SIMBAD's position (ICRS right ascension
  // and declination) with the rotation to galactic coordinates of the
  // Hipparcos catalogue (ESA 1997, volume 1, section 1.5.3).
  //
  // Alpha Centauri is the pair A and B as one: 750.81 ± 0.38 mas (Akeson and
  // others, 2021AJ....162...14A), which is 4.34 light-years. SIMBAD's entry
  // for A alone still has the first Hipparcos value, 742.12 ± 1.40 mas, which
  // is 4.39. The figure uses the pair's, the newer and the tighter of the two,
  // so it says 4.3 where older tables say 4.4. Its position is from
  // 2001AJ....122.3466M.
  //
  // Sirius is given as 8.6 light-years here and as 8.7 elsewhere. Hipparcos
  // measured Sirius itself: 379.21 ± 1.58 mas, which is 8.60 light-years. Gaia
  // cannot, because the star is too bright for it, and has only the faint
  // companion Sirius B: 374.49 ± 0.23 mas (Gaia DR3), which is 8.71. The
  // figure uses Hipparcos, because that is a measurement of the star that is
  // marked, and it comes from the same catalogue as the stars either side.
  //
  // Procyon and Fomalhaut have been passed and are not drawn. At this size
  // there is no place for either name that is clearly its own: Procyon lies
  // beside Sirius, and Fomalhaut between Altair and the line to the centre.
  const STARS = [
    { name: "Alpha Centauri", id: "* alf Cen", plx: 750.81, v: -0.1, l: 315.734 },
    { name: "Sirius", id: "* alf CMa", plx: 379.21, v: -1.46, l: 227.23 },
    { name: "Procyon", id: "* alf CMi", plx: 284.56, v: 0.37, l: 213.702 },
    { name: "Altair", id: "* alf Aql", plx: 194.95, v: 0.76, l: 47.744 },
    { name: "Vega", id: "* alf Lyr", plx: 130.23, v: 0.03, l: 67.448 },
    { name: "Fomalhaut", id: "* alf PsA", plx: 129.81, v: 1.16, l: 20.488 },
    { name: "Pollux", id: "* bet Gem", plx: 96.54, v: 1.14, l: 192.229 },
    { name: "Arcturus", id: "* alf Boo", plx: 88.83, v: -0.05, l: 15.05 },
    { name: "Capella", id: "* alf Aur", plx: 76.2, v: 0.08, l: 162.588 },
    { name: "Aldebaran", id: "* alf Tau", plx: 48.94, v: 0.86, l: 180.972 },
  ];

  // A star's distance in light-years is this over its parallax in mas: a
  // parsec is 648 000 / π au, and a light-year is 63 241.077 au.
  const LY_MAS = 3261.5638;

  // The long line to the right points at the centre of the Galaxy, where
  // Sagittarius A* is: 8275 ± 9 (statistical) ± 33 (systematic) parsecs away
  // (GRAVITY Collaboration, 2021A&A...647A..59G). That is 27 000 light-years
  // to the nearest thousand. Sagittarius A* lies 0.06 degrees off the line,
  // which is nothing at this scale.
  const CENTRE_PC = 8275;

  const pick = (selector) => svg.querySelector(selector);
  const parts = { years: pick(".years"), tens: pick(".tens"), axis: pick(".axis"), light: pick(".light") };
  if (Object.values(parts).includes(null)) return;

  const named = (selector) => new Map([...chart.querySelectorAll(selector)].map((el) => [el.dataset.star, el]));
  const rays = named(".ray[data-star]");
  const marks = named(".star[data-star]");

  // Seen from above the north pole of the Galaxy: longitude runs
  // anticlockwise from the line to the centre, and y runs down the page.
  const stars = STARS.map((star) => {
    const ly = LY_MAS / star.plx;
    const a = (star.l * Math.PI) / 180;
    return { ...star, ly, x: ly * Math.cos(a), y: -ly * Math.sin(a) };
  }).filter((star) => rays.has(star.name) && marks.has(star.name));

  // A clock that says it is earlier than the year the page was made for is
  // wrong, and the page is kept as it is.
  const made = parseInt(readout.textContent, 10) || 0;
  const year = Math.max(new Date().getFullYear(), made);
  const front = year - FROM;
  if (front < 1) return;

  // The readout: a year, and how far out the light was in it. The number is
  // padded so that nothing shifts as it changes.
  function say(ly) {
    const far = String(ly).padStart(2, "\u00a0");
    readout.textContent = `${FROM + ly} · ${far} light-year${ly === 1 ? "\u00a0" : "s"}`;
  }

  const list = (things) => (things.length > 1 ? `${things.slice(0, -1).join(", ")} and ${things.at(-1)}` : things[0]);
  const at = (star) => `${star.name} at ${star.ly.toFixed(1)}`;
  const thousands = (n) => String(n).replace(/\B(?=(\d{3})+$)/g, "\u202f");

  // Bring the drawing up to this year.
  function update() {
    chart.style.setProperty("--front", front);
    svg.setAttribute("viewBox", `${-front} ${-front} ${2 * front} ${2 * front}`);

    let years = "";
    let tens = "";
    for (let ly = 1; ly <= front; ly++) {
      if (ly % 10) years += `M${ly} 0v0.6`;
      else tens += `M${ly} 0v1.2`;
    }
    parts.years.setAttribute("d", years);
    parts.tens.setAttribute("d", tens);
    parts.axis.setAttribute("x2", front);

    for (const star of stars) {
      const ray = rays.get(star.name);
      const mark = marks.get(star.name);
      for (const el of [ray, mark]) {
        el.classList.toggle("ahead", star.ly > front);
        el.toggleAttribute("hidden", star.ly > front + AHEAD);
      }
      ray.setAttribute("x2", star.x.toFixed(3));
      ray.setAttribute("y2", star.y.toFixed(3));
      mark.style.setProperty("--x", star.x.toFixed(3));
      mark.style.setProperty("--y", star.y.toFixed(3));
    }

    const passed = stars.filter((star) => star.ly <= front).map(at);
    const next = stars.filter((star) => star.ly > front && star.ly <= front + AHEAD).map(at);
    const centre = thousands(Math.round((CENTRE_PC * LY_MAS) / 1e6) * 1000);
    chart.setAttribute(
      "aria-label",
      "A map around the Sun, seen from above the plane of the Milky Way, with the centre of the Galaxy to the right. " +
        "A line runs from the Sun towards each star and is as long as the star is far, in light-years. " +
        `The circle is the light that left Earth in ${FROM}, ${front} light-years out in ${year}.` +
        (passed.length ? ` Inside it are ${list(passed)}.` : "") +
        (next.length ? ` Dotted lines run to the stars it reaches within ${AHEAD} years: ${list(next)}.` : "") +
        ` Sagittarius A*, at the centre of the Galaxy, is ${centre} light-years away.`
    );
  }

  // One thing moves: the circle. It rests on the light, and under a pointer
  // it shows where the light was in an earlier year.
  function point(ly) {
    parts.light.setAttribute("r", ly);
  }
  function rest() {
    point(front);
    say(front);
  }

  // A pointer on the map reads it a whole year at a time: the year in which
  // the light was as far out as the pointer is from the Sun.
  function read(event) {
    const box = svg.getBoundingClientRect();
    const half = box.width / 2;
    const away = Math.hypot(event.clientX - (box.left + half), event.clientY - (box.top + half));
    const ly = Math.min(Math.round((away / half) * front), front);
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
  figure.classList.add("readable");

  chart.addEventListener("pointerdown", (event) => {
    if (event.pointerType !== "mouse") chart.setPointerCapture(event.pointerId);
    read(event);
  });
  chart.addEventListener("pointermove", (event) => {
    if (event.pointerType === "mouse" || chart.hasPointerCapture(event.pointerId)) read(event);
  });
  chart.addEventListener("pointerup", (event) => {
    if (event.pointerType !== "mouse") release();
  });
  chart.addEventListener("pointerleave", release);
  chart.addEventListener("pointercancel", release);
})();
