export class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
    }
}

export async function api(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        credentials: 'same-origin',
        headers: { Accept: 'application/json', ...options.headers },
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        if (response.status === 401) window.dispatchEvent(new Event('session:expired'));
        throw new ApiError(data.erro || 'Não foi possível concluir a operação.', response.status);
    }
    return data;
}
