function setupTomSelectIngredient(element) {
    if (element && !element.tomselect) {
        const ts = new TomSelect(element, {
            onChange: function(value) {
                if (!value) return;
                
                // Find the unit dropdown in the same row
                const row = element.closest('.ingredient-row');
                const unitSelect = row.querySelector('.unit-selector');

                // Manually trigger an HTMX request
                htmx.ajax('GET', `/food/units-ingred?food_id=${value}`, {
                    target: unitSelect,
                    swap: 'innerHTML'
                });
            }
        });
    }
}


function setupTomSelectMeal(element) {
    if (element && !element.tomselect) {
        const ts = new TomSelect(element, {
            onChange: function(value) {
                if (!value) return;
                
                // Find the unit dropdown in the same row
                const row = element.closest('.consumption-row');
                const unitSelect = row.querySelector('.unit-selector');

                // Manually trigger an HTMX request
                htmx.ajax('GET', `/food/units-ingred?food_id=${value}`, {
                    target: unitSelect,
                    swap: 'innerHTML'
                });
            }
        });
    }
}


document.body.addEventListener('htmx:afterRequest', function(evt) {
    // Only run if the request came from the "Add Row" button
    if (evt.detail.target.id === "consumption-list" || evt.detail.target.classList.contains("consumption-row")) {
        const list = document.getElementById('consumption-list');
        const rows = list.querySelectorAll('.consumption-row');
        const count = rows.length;
        const totalFormsInput = document.getElementById('id_items-TOTAL_FORMS');
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

        // 3. Initialize TomSelect ONLY on selects that don't have it yet
        latestRow.querySelectorAll('.tom-select-meal').forEach(el => {
            if (!el.tomselect) {
                setupTomSelectMeal(el); // Your existing setup function
            }
        });
    }
    else if (evt.detail.target.id === "ingredient-list") {
        const list = document.getElementById('ingredient-list');
        const rows = list.querySelectorAll('.ingredient-row');
        const count = rows.length;
        const totalFormsInput = document.getElementById('id_ingredient_set-TOTAL_FORMS');
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

        // 3. Initialize TomSelect ONLY on selects that don't have it yet
        latestRow.querySelectorAll('.tom-select-ingredient').forEach(el => {
            if (!el.tomselect) {
                setupTomSelectIngredient(el); // Your existing setup function
            }
        });
    }
});