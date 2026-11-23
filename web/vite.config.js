import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// O build é servido pela API Flask em /static/dist/ (mesma origem: sessão e CSRF funcionam sem CORS).
// Em desenvolvimento (npm run dev), o Vite encaminha as requisições de dados para a API.
const API = process.env.EDUCAFAST_API || 'http://127.0.0.1:5000';

export default defineConfig({
    base: '/static/dist/',
    plugins: [react()],
    build: {
        outDir: '../api/app/static/dist',
        emptyOutDir: true,
    },
    server: {
        port: 5173,
        proxy: {
            '^/(?!static/dist/|@vite|@react-refresh|@id/|@fs/|src/|node_modules/)': {
                target: API,
                changeOrigin: false,
                bypass(req) {
                    const html = (req.headers.accept || '').includes('text/html');
                    if (req.method === 'GET' && html && req.headers['x-educafast-spa'] !== '1') return '/static/dist/index.html';
                    return undefined;
                },
            },
        },
    },
});
