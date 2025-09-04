document.body.addEventListener("htmx:configRequest", function (event) {
  const dateInput = document.querySelector("#date-picker");

  let selectedDate = dateInput?.value;

  // Fallback to today's date if no value is set
  if (!selectedDate) {
    const today = new Date();
    selectedDate = today.toISOString().split("T")[0]; // format: YYYY-MM-DD
  }

  event.detail.parameters["selected_date"] = selectedDate;
});