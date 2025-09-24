let restInterval;
let restStart = null;

function startRestTimer() {
  restStart = Date.now();
  clearInterval(restInterval);
  restInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - restStart) / 1000);
    const display = document.querySelector("#rest-display");
    if (display) {
      display.textContent = `- Rest: ${elapsed}s -`;
    }
  }, 1000);
}

function stopRestTimerAndPopulate() {
  clearInterval(restInterval);
  if (!restStart) return;
  const elapsedMs = Date.now() - restStart;
  const elapsedSec = Math.floor(elapsedMs / 1000);

  // ISO 8601 Duration format for Django DurationField
  const isoDuration = `PT${elapsedSec}S`;
  const restInput = document.querySelector("#id_rest");
  if (restInput) {
    restInput.value = isoDuration;
  }

  restStart = null;
}

// Reattach listeners every time HTMX swaps in the form
document.body.addEventListener("htmx:afterSwap", (e) => {
  // Only rebind if the swapped content contains your form
  if (e.target.querySelector && e.target.querySelector("#set-form")) {
    const repsInput = e.target.querySelector("#id_reps");
    const weightInput = e.target.querySelector("#id_weight");
    const form = e.target.querySelector("#set-form");

    if (repsInput) repsInput.addEventListener("focus", startRestTimer);
    if (weightInput) weightInput.addEventListener("focus", startRestTimer);
    if (form) form.addEventListener("submit", stopRestTimerAndPopulate);
  }
});
