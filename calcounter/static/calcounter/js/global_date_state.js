document.body.addEventListener("htmx:configRequest", function (event) {
  const dateInput = document.querySelector("#hidden-date");

  let selectedDate = dateInput?.value;

  // Fallback to today's date if no value is set
  if (!selectedDate) {
    const today = new Date();
    selectedDate = today.toISOString().split("T")[0]; // format: YYYY-MM-DD
  }

  event.detail.parameters["selected_date"] = selectedDate;
});


const container = document.getElementById('date-container');
const dateDisplay = document.getElementById('current-date');
const hiddenInput = document.getElementById('hidden-date');

let displayDate = hiddenInput?.value;
if (!displayDate) {
  const today = new Date();
  displayDate = today.toISOString().split("T")[0]; // format: YYYY-MM-DD
}
dateDisplay.textContent = displayDate

container.addEventListener('click', () => hiddenInput.showPicker?.()); // Chrome supports .showPicker()

hiddenInput.addEventListener('input', () => {
  dateDisplay.textContent = hiddenInput.value;
  // You could also trigger HTMX here to update your backend

});

