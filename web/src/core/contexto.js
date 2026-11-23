import { createContext, useContext } from 'react';

// Contexto global da tela atual: sessão, endpoint, tema, escola, CSRF e navegação.
export const AppContext = createContext(null);

export function useApp() {
    return useContext(AppContext);
}

export function useSessao() {
    return useApp().global.sessao;
}
