function attachDragHandlers() {
  const lifts = document.querySelectorAll('.lift');
  const dropzone = document.querySelector('#lift_entry__container');

  lifts.forEach(lift => {
    lift.addEventListener('dragstart', e => {
      e.dataTransfer.setData('text/plain', lift.dataset.liftId);
      lift.classList.add('dragging');
dropzone.classList.add('dropzone');
    });

    lift.addEventListener('dragend', () => {
      lift.classList.remove('dragging');
dropzone.classList.remove('dropzone');
    });
  });

  dropzone.addEventListener('dragover', e => {
    e.preventDefault(); // Needed to allow dropping
    dropzone.classList.add('drag-over');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('drag-over');
  });

  dropzone.addEventListener('drop', e => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');

    const liftId = e.dataTransfer.getData('text/plain');
    console.log(`Dropped lift ${liftId}`);
    htmx.ajax('GET', `/workouts/edit/active/lift/${liftId}`, '#lift_entry__container');

  });
};

// Run once on initial page load
document.addEventListener('DOMContentLoaded', attachDragHandlers);

// Run again every time HTMX swaps in new content
document.body.addEventListener('htmx:afterSwap', attachDragHandlers);
