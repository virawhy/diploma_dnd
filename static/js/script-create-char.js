const checkboxes = document.querySelectorAll('.test-column input[type="checkbox"]');
checkboxes.forEach(checkbox => {
  checkbox.addEventListener('click', () => {
    const checkedCount = document.querySelectorAll('.test-column input[type="checkbox"]:checked').length;
    if (checkedCount > 3) {
      checkbox.checked = false;
    }
  });
});

const checkboxes1 = document.querySelectorAll('.test-column-1 input[type="checkbox"]');
checkboxes1.forEach(checkbox => {
  checkbox.addEventListener('click', () => {
    const checkedCount = document.querySelectorAll('.test-column-1 input[type="checkbox"]:checked').length;
    if (checkedCount > 1) {
      checkbox.checked = false;
    }
  });
});

const checkboxes2 = document.querySelectorAll('.test-column-2 input[type="checkbox"]');
checkboxes2.forEach(checkbox => {
  checkbox.addEventListener('click', () => {
    const checkedCount = document.querySelectorAll('.test-column-2 input[type="checkbox"]:checked').length;
    if (checkedCount > 1) {
      checkbox.checked = false;
    }
  });
});

const checkboxes3 = document.querySelectorAll('.test-column-3 input[type="checkbox"]');
checkboxes3.forEach(checkbox => {
  checkbox.addEventListener('click', () => {
    const checkedCount = document.querySelectorAll('.test-column-3 input[type="checkbox"]:checked').length;
    if (checkedCount > 1) {
      checkbox.checked = false;
    }
  });
});