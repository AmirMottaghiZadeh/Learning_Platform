(() => {
  const entry = document.querySelector('[data-otp]');
  if (!entry) return;

  const input = entry.querySelector('input');
  const group = entry.querySelector('.otp-cells');
  const cells = [...group.children];
  const persian = '۰۱۲۳۴۵۶۷۸۹';
  const arabic = '٠١٢٣٤٥٦٧٨٩';
  const normalize = value => value.replace(/[۰-۹٠-٩]/g, char => {
    const index = persian.indexOf(char);
    return index >= 0 ? index : arabic.indexOf(char);
  }).replace(/\D/g, '');

  function render() {
    const position = input.selectionStart ?? input.value.length;
    const code = normalize(input.value).slice(0, cells.length);
    if (input.value !== code) {
      const cursor = normalize(input.value.slice(0, position)).length;
      input.value = code;
      input.setSelectionRange(cursor, cursor);
    }

    const focused = document.activeElement === input;
    const cursor = Math.min(input.selectionStart ?? code.length, cells.length - 1);
    cells.forEach((cell, index) => {
      cell.textContent = code[index] ? persian[Number(code[index])] : '';
      cell.toggleAttribute('data-filled', !!code[index]);
      cell.toggleAttribute('data-current', focused && index === cursor);
    });
  }

  function paste(event) {
    const raw = event.clipboardData?.getData('text');
    if (raw === undefined) return;

    event.preventDefault();
    const code = normalize(raw).slice(0, cells.length);
    if (code.length === cells.length) {
      input.value = code;
    } else {
      const start = input.selectionStart ?? input.value.length;
      const end = input.selectionEnd ?? start;
      input.setRangeText(code, start, end, 'end');
    }
    render();
  }

  for (const event of ['input', 'focus', 'blur', 'keyup', 'click', 'select']) input.addEventListener(event, render);
  input.addEventListener('paste', paste);
  group.hidden = false;
  entry.classList.add('otp-enhanced');
  render();
})();
