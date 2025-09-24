function SetupMealFormButtonState() {
    const form = document.getElementById('m_entry_form');
    if (!form) return;
    const inputs = form.querySelectorAll('input[type="number"]');
    const submitBtn = document.getElementById('sub');

    // Function to check if all inputs are empty
    function updateButtonState() {
    const allEmpty = [...inputs].every(input => input.value.trim() === "");
    console.log(allEmpty)
    submitBtn.innerHTML= allEmpty ? "Back" : "Submit";
    submitBtn.classList.toggle("back-btn", allEmpty)
    if (allEmpty && submitBtn.classList.contains("form_btn")) submitBtn.classList.remove("form_btn");
    if (!allEmpty && !(submitBtn.classList.contains("form_btn"))) submitBtn.classList.add("form_btn");

    }


    updateButtonState()
    // Watch inputs for changes
    inputs.forEach(input => {
    input.addEventListener('input', updateButtonState);
    });

    // Handle submission
    submitBtn.addEventListener('click', function(e) {
    const allEmpty = [...inputs].every(input => input.value.trim() === "");

    if (allEmpty) {
        e.preventDefault();
        htmx.ajax('GET', "/food/back/", {
          target: '#meal_entry__container',
          swap: 'outerHTML swap:0.5s'});
    }
    });
}

document.addEventListener("DOMContentLoaded", SetupMealFormButtonState);

document.body.addEventListener("htmx:afterSwap", function (e) {
  if (e.target.id === "meal_entry__container") {
    SetupMealFormButtonState();
  }
});
