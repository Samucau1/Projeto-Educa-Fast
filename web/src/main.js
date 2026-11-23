import 'vite/modulepreload-polyfill';
import React from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import './styles/painel.css';
import App from './App';

class RenderErrorBoundary extends React.Component {
    state = { failed: false };
    static getDerivedStateFromError() { return { failed: true }; }
    render() {
        if (this.state.failed) return React.createElement('main', { className: 'p-10', role: 'alert' },
            'Não foi possível abrir esta tela. ',
            React.createElement('button', { onClick: () => window.location.reload() }, 'Recarregar'));
        return this.props.children;
    }
}

createRoot(document.getElementById('root')).render(
    React.createElement(RenderErrorBoundary, null, React.createElement(App))
);
