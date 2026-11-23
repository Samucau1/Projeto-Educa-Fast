// Registro das telas: o nome do arquivo é o nome da tela devolvido pela API (render_page).
const modulos = import.meta.glob('./*.jsx', { eager: true });

export const paginas = Object.fromEntries(
    Object.entries(modulos).map(([arquivo, modulo]) => [arquivo.replace(/^\.\/|\.jsx$/g, ''), modulo]),
);
