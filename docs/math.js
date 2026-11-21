/* Sets the TeX in a piece of writing: \( … \) inline, \[ … \] on its own line. */
renderMathInElement(document.querySelector(".prose"), {
  delimiters: [
    { left: "\\[", right: "\\]", display: true },
    { left: "\\(", right: "\\)", display: false },
  ],
  fleqn: true,
  throwOnError: false,
});
