import { useEffect } from 'react';

// Rolagem horizontal das tabelas dentro do conteúdo principal.
export function TabelaRolagem({ children }) {
    return <div className="app-table-scroll" tabIndex={0} role="region" aria-label="Tabela com rolagem horizontal">{children}</div>;
}

// Rótulos das células (data-label) usados pelo layout de tabela em telas estreitas.
export function useRotulosTabelas(dependencia) {
    useEffect(() => {
        document.querySelectorAll('.app-content table').forEach((table) => {
            const headings = table.tHead ? Array.from(table.tHead.rows[0].cells).map((cell) => cell.textContent.trim()) : [];
            table.querySelectorAll('tbody tr').forEach((row) => {
                Array.from(row.cells).forEach((cell, index) => { if (cell.colSpan === 1) cell.dataset.label = headings[index] || ''; });
            });
        });
    }, [dependencia]);
}
