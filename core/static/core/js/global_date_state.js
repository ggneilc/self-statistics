function setSelectedDate(isoDate) {
    const hiddenInput = document.getElementById('hidden-date');
    const prev_edit = document.querySelector("#editing-date");

    // Update hidden input (used by HTMX)
    hiddenInput.value = isoDate;
    console.log("updated hiddenInput to " + hiddenInput.value);
    const d = isoDate.split("-");
    const month = d[1];
    const day = d[2];
	console.log(""+month+"/"+day);

    // User-facing display: MM/DD
    var today = new Date().toLocaleDateString("en-CA");
    if (isoDate !== today) {
	if (prev_edit) {prev_edit.textContent = `VIEWING: ${isoDate}`;}
    } else {
	if (prev_edit) {prev_edit.textContent = '';}
    }
    hiddenInput.dispatchEvent(new Event("change", { bubbles: true }));
}


(function initDatePicker() {
    const hiddenInput = document.getElementById('hidden-date');

    if (!hiddenInput.value) {
        // default to today
        const todayISO = new Date().toLocaleDateString("en-CA");
        setSelectedDate(todayISO);
    } else {
        setSelectedDate(hiddenInput.value);
    }
})();



document.body.addEventListener("htmx:configRequest", function (event) {
    const hiddenInput = document.getElementById("hidden-date");
    let selectedDate = hiddenInput?.value;
	console.log("sending request, found : "+ selectedDate);

    // If missing or invalid → default to today
    if (!selectedDate) {
        selectedDate = new Date().toLocaleDateString("en-CA"); // forced ISO
	console.log("missing date, set to : "+ selectedDate);
    }


    // Always send ISO date to backend
    event.detail.parameters["selected_date"] = selectedDate;
});
