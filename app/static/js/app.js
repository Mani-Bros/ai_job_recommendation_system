document.querySelectorAll('input[type=file]').forEach(input => {
  input.addEventListener('change', () => {
    const label = input.closest('.file-button');
    if (label && input.files[0]) label.childNodes[0].textContent = input.files[0].name + ' ';
  });
});
