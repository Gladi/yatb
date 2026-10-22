// YATB-Dashboard: Seite aktuell halten, ohne Eingaben zu verlieren.
// Lädt neu, wenn man zum Tab zurückkehrt oder die Seite eine Minute offen ist - aber nie, solange in einem
// Formular etwas eingegeben wurde oder ein Feld den Fokus hat. Ohne JavaScript funktioniert alles wie bisher.
(() => {
  let dirty = false;
  let hiddenAt = 0;
  document.addEventListener("input", () => { dirty = true; });
  const reload = () => {
    if (dirty || document.querySelector("form :focus")) return;
    const url = new URL(window.location.href);
    url.searchParams.delete("saved");          // Hinweis "Gespeichert" nicht erneut zeigen
    window.location.replace(url.toString());
  };
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) hiddenAt = Date.now();
    else if (hiddenAt && Date.now() - hiddenAt > 2000) reload();
  });
  setInterval(() => { if (!document.hidden) reload(); }, 60000);
})();
