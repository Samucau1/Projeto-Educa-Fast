// Formatações que os templates faziam no servidor (strftime e afins).

// "2026-11-23" ou "2026-11-23 10:00:00" -> "23/11/2026"
export function dataBR(valor) {
    if (!valor) return '';
    const [a, m, d] = String(valor).slice(0, 10).split('-');
    return `${d}/${m}/${a}`;
}
