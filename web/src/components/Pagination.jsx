import React from 'react';

export function Pagination({ pagination, onPage, onSize, busy = false, label = 'Paginação de usuários' }) {
    if (!pagination) return null;
    const { page, page_size: size, total, pages } = pagination;
    return <nav aria-label={label} className="pagination">
        <p aria-live="polite">{total ? `${(page - 1) * size + 1}–${Math.min(page * size, total)} de ${total} registros` : 'Nenhum registro encontrado'}</p>
        <label>Por página <select value={size} disabled={busy} onChange={e => onSize(Number(e.target.value))}>{[10, 20, 50, 100].map(n => <option key={n} value={n}>{n}</option>)}</select></label>
        <div className="button-actions">
            <button className="ui-button" disabled={busy || page <= 1} onClick={() => onPage(page - 1)}>Anterior</button>
            <span>Página {page} de {pages}</span>
            <button className="ui-button" disabled={busy || page >= pages} onClick={() => onPage(page + 1)}>Próxima</button>
        </div>
    </nav>;
}
