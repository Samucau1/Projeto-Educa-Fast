// Arrays vazios representam listas sem registros nas condições da interface.
export const truthy = (value) => Array.isArray(value) ? value.length > 0 : Boolean(value);

export const homeForRole = (role) => ({
    admin: '/gestao', secretaria: '/admin/dashboard', aluno: '/aluno', professor: '/professor',
}[role] || '/login');
