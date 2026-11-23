document.addEventListener('DOMContentLoaded', () => {
  const policy = document.querySelector('[data-school-policy]');
  if (policy) {
    const refresh = () => {
      const division = policy.elements.divisao.value;
      const count = { semestres: 2, trimestres: 3, bimestres: 4 }[division] || Number(policy.elements.quantidade.value);
      policy.querySelectorAll('[data-school-slot]').forEach(slot => {
        const hidden = Number(slot.dataset.schoolSlot) > count;
        slot.hidden = hidden;
        slot.querySelectorAll('input').forEach(input => { input.disabled = hidden; });
      });
    };
    policy.addEventListener('change', refresh);
    refresh();
  }
  document.querySelectorAll('[data-school-preset]').forEach(button => button.addEventListener('click', () => {
    const form = document.querySelector('#school-identity');
    if (!form) return;
    const light = button.dataset.schoolPreset === 'claro';
    const values = light ? { modo: 'claro', fundo: '#f3f6fb', destaque: '#1d4ed8', superficie: '#ffffff', texto: '#18283b', muted: '#475569' }
      : { modo: 'escuro', fundo: '#06385d', destaque: '#22d3ee', superficie: '#111c2b', texto: '#ecf1f8', muted: '#a4bdce' };
    Object.entries(values).forEach(([name, value]) => { form.elements[name].value = value; });
    form.querySelector('[data-school-status]').textContent = 'Paleta preenchida no formulário. Salve para aplicar à escola.';
  }));
});
