import { useApp } from '../core/contexto';

// Campo oculto de proteção CSRF exigido pelos formulários da API.
export default function Token() {
    return <input type="hidden" name="csrf_token" value={useApp().global.csrf_token} />;
}
