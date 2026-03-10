// === Workout Timer ===
// Counts up from when the workout started. Persists across HTMX swaps via localStorage.

let workoutInterval;

function startWorkoutTimer(workoutId) {
  // Reset if this is a different workout than what's stored
  if (workoutId && localStorage.getItem('workoutId') !== String(workoutId)) {
    localStorage.setItem('workoutStart', Date.now());
    localStorage.setItem('workoutId', workoutId);
  } else if (!localStorage.getItem('workoutStart')) {
    localStorage.setItem('workoutStart', Date.now());
  }
  clearInterval(workoutInterval);
  workoutInterval = setInterval(() => {
    const start = parseInt(localStorage.getItem('workoutStart'));
    const elapsed = Math.floor((Date.now() - start) / 1000);
    const mins = Math.floor(elapsed / 60).toString().padStart(2, '0');
    const secs = (elapsed % 60).toString().padStart(2, '0');
    const display = document.querySelector('#workout-time');
    if (display) display.textContent = `${mins}:${secs}`;
  }, 1000);
}

function stopWorkoutTimer() {
  clearInterval(workoutInterval);
  localStorage.removeItem('workoutStart');
  localStorage.removeItem('workoutId');
}

// === Rest Timer ===
// Starts after a set is submitted. Displays in #rest-display.

let restInterval;
let restStart = null;

function startRestTimer() {
  restStart = Date.now();
  clearInterval(restInterval);
  const bar = document.querySelector('#rest-display');
  if (bar) bar.classList.add('active');
  restInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - restStart) / 1000);
    const mins = Math.floor(elapsed / 60);
    const secs = (elapsed % 60).toString().padStart(2, '0');
    const value = document.querySelector('#rest-time-value');
    if (value) value.textContent = mins > 0 ? `${mins}:${secs}` : `${elapsed}s`;
  }, 1000);
}

function stopRestTimerAndPopulate() {
  clearInterval(restInterval);
  if (!restStart) return;
  const elapsedSec = Math.floor((Date.now() - restStart) / 1000);
  const isoDuration = `PT${elapsedSec}S`;
  const restInput = document.querySelector('#id_rest');
  if (restInput) restInput.value = isoDuration;
  restStart = null;
  const bar = document.querySelector('#rest-display');
  if (bar) bar.classList.remove('active');
  const value = document.querySelector('#rest-time-value');
  if (value) value.textContent = '—';
}

// On page reload: resume timer only if a workout was already in progress
document.addEventListener('DOMContentLoaded', () => {
  if (localStorage.getItem('workoutStart')) {
    startWorkoutTimer();
  }
});
