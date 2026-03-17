function closestWithClass(el, className) {
  while (el && el !== document.body) {
    if (el.classList && el.classList.contains(className)) return el;
    el = el.parentElement;
  }
  return null;
}

function clearResults(container) {
  if (!container) return;
  container.innerHTML = '';
}

document.body.addEventListener('click', function (e) {
  const btn = e.target.closest && e.target.closest('.typeahead-option');
  if (!btn) return;

  const foodId = btn.dataset.foodId;
  const foodLabel = btn.dataset.foodLabel || btn.textContent || '';
  const hiddenId = btn.dataset.targetHiddenId;
  const inputId = btn.dataset.targetInputId;
  const unitId = btn.dataset.targetUnitId;

  const hidden = hiddenId ? document.getElementById(hiddenId) : null;
  const input = inputId ? document.getElementById(inputId) : null;

  if (hidden) hidden.value = foodId;
  if (input) input.value = foodLabel;

  const typeahead = closestWithClass(btn, 'typeahead');
  if (typeahead) {
    const results = typeahead.querySelector('.typeahead-results-container');
    clearResults(results);
  }

  // Trigger unit refresh (same behavior as Tom Select did)
  if (unitId && foodId && window.htmx) {
    const unitSelect = document.getElementById(unitId);
    if (unitSelect) {
      htmx.ajax('GET', `/food/units-ingred?food_id=${encodeURIComponent(foodId)}`, {
        target: unitSelect,
        swap: 'innerHTML'
      });
    }
  }
});

// If user edits the query manually, clear the hidden id so we don't submit stale IDs
document.body.addEventListener('input', function (e) {
  const input = e.target;
  if (!input || !input.classList || !input.classList.contains('food-typeahead-input')) return;
  const typeahead = closestWithClass(input, 'typeahead');
  if (!typeahead) return;
  const hidden = typeahead.querySelector('input.food-typeahead-hidden');
  if (hidden) hidden.value = '';

   // If the query is cleared, also clear any visible results
   if (!input.value.trim()) {
     const results = typeahead.querySelector('.typeahead-results-container');
     clearResults(results);
   }
});

// When the input loses focus (and focus isn't moving into the dropdown), hide results
document.body.addEventListener('focusout', function (e) {
  const input = e.target;
  if (!input || !input.classList || !input.classList.contains('food-typeahead-input')) return;
  const typeahead = closestWithClass(input, 'typeahead');
  if (!typeahead) return;

  // Delay slightly so clicks on options still register before we clear
  setTimeout(() => {
    if (!typeahead.contains(document.activeElement)) {
      const results = typeahead.querySelector('.typeahead-results-container');
      clearResults(results);
    }
  }, 150);
});


document.body.addEventListener('htmx:afterRequest', function(evt) {
    // Only run if the request came from the "Add Row" button
    if (evt.detail.target.id === "consumption-list" || evt.detail.target.classList.contains("consumption-row")) {
        const list = document.getElementById('consumption-list');
        const rows = list.querySelectorAll('.consumption-row');
        const count = rows.length;
        // Find the management form input for this formset by suffix, regardless of prefix
        const form = list.closest('form');
        const totalFormsInput = form && form.querySelector('input[name$="-TOTAL_FORMS"]');
        // 1. Update the TOTAL_FORMS count
        if (totalFormsInput) {
            totalFormsInput.value = count;
        }

        // 2. Fix the prefix only for the NEWEST row (the last one)
        const latestRow = list.lastElementChild;
        if (latestRow.innerHTML.includes('__prefix__')) {
            // We use count - 1 because Django indexes are 0-based
            latestRow.innerHTML = latestRow.innerHTML.replace(/__prefix__/g, count - 1);
        }

        // Tom Select replaced by HTMX typeahead for meal rows
    }
    else if (evt.detail.target.id === "ingredient-list") {
        const list = document.getElementById('ingredient-list');
        const rows = list.querySelectorAll('.ingredient-row');
        const count = rows.length;
        const form = list.closest('form');
        const totalFormsInput = form && form.querySelector('input[name$="-TOTAL_FORMS"]');
        // 1. Update the TOTAL_FORMS count
        if (totalFormsInput) {
            totalFormsInput.value = count;
        }

        // 2. Fix the prefix only for the NEWEST row (the last one)
        const latestRow = list.lastElementChild;
        if (latestRow.innerHTML.includes('__prefix__')) {
            // We use count - 1 because Django indexes are 0-based
            latestRow.innerHTML = latestRow.innerHTML.replace(/__prefix__/g, count - 1);
        }

        // Tom Select replaced by HTMX typeahead for ingredient rows
    }
});