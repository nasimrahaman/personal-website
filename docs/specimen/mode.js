/*
 * Fig. 2 of the specimen: the smallest complete figure that responds.
 *
 * The page already holds the figure in its resting state. This script only
 * adds the response, marks the figure as live while it is being handled, and
 * puts it back afterwards.
 */
(() => {
  "use strict";

  const figure = document.getElementById("fig-2");
  const svg = figure && figure.querySelector("svg");
  const string = svg && svg.querySelector("polyline");
  const readout = figure && figure.querySelector(".readout");
  if (!string || !readout) return;

  const WIDTH = 600; // of the viewBox
  const MIDDLE = 60;
  const AMPLITUDE = 44;
  const MODES = 12;
  const REST = 3;

  function draw(n) {
    readout.textContent = `n = ${n}`;
    const points = [];
    for (let x = 0; x <= WIDTH; x += 2) {
      points.push(`${x} ${(MIDDLE - AMPLITUDE * Math.sin((n * Math.PI * x) / WIDTH)).toFixed(1)}`);
    }
    string.setAttribute("points", points.join(" "));
  }

  svg.addEventListener("pointermove", (event) => {
    const box = svg.getBoundingClientRect();
    const along = Math.min(Math.max((event.clientX - box.left) / box.width, 0), 0.999);
    figure.classList.add("live");
    draw(1 + Math.floor(along * MODES));
  });
  svg.addEventListener("pointerleave", () => {
    figure.classList.remove("live");
    draw(REST);
  });
})();
