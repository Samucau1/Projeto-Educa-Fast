import React, { createContext, useContext, useState } from 'react';

const TabsContext = createContext(null);
export function TabsProvider({ children }) {
    const [active, setActive] = useState({ aluno: new URLSearchParams(window.location.search).get('aba') === 'comunicados' ? 'comunicados' : 'disciplinas', professor: 'turmas', documento: 'solicitacoes', 'professor-section': 'atuacao' });
    return <TabsContext.Provider value={{ active, select: (group, value) => setActive((previous) => ({ ...previous, [group]: value })) }}>{children}</TabsContext.Provider>;
}

export function TabButton({ group, value, defaultValue, as: Tag = 'button', className = '', children, ...props }) {
    const { active, select } = useContext(TabsContext);
    const selected = (active[group] ?? defaultValue) === value;
    return <Tag {...props} type="button" role="tab" aria-selected={selected}
        aria-controls={`${group}-${value}-panel`} id={`${group}-${value}-tab`}
        className={`${className} ${selected ? 'bg-cyan-500/10 text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-300 hover:bg-white/5'}`}
        onClick={() => select(group, value)}>{children}</Tag>;
}

export function TabPanel({ group, value, defaultValue, as: Tag = 'div', children, className = '', ...props }) {
    const { active } = useContext(TabsContext);
    return <Tag {...props} className={className} role="tabpanel" hidden={(active[group] ?? defaultValue) !== value}
        id={`${group}-${value}-panel`} aria-labelledby={`${group}-${value}-tab`}>{children}</Tag>;
}
