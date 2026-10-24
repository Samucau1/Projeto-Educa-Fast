"""Portão estático do protocolo; a inspeção visual continua obrigatória."""
from pathlib import Path
import re


def verificar(root):
    app = root / 'Códigos/app'
    erros = []
    for path in sorted((app / 'templates').glob('escola_*.html')):
        text = path.read_text(encoding='utf-8')
        if "extends 'gestao_base.html'" not in text:
            erros.append(f'{path.name}: não usa o layout compartilhado')
        if re.search(r'<style\b|\sstyle\s*=|\son\w+\s*=|https?://', text, re.I):
            erros.append(f'{path.name}: estilo, evento inline ou recurso externo não permitido')
    css = (app / 'static/css/escola.css').read_text(encoding='utf-8')
    if not all(token in css for token in ('var(--text)', 'var(--surface)', 'var(--accent)', 'var(--school-radius)')):
        erros.append('escola.css: faltam tokens compartilhados')
    if '<style' in (app / 'templates/partials/curso_estilo.html').read_text(encoding='utf-8'):
        erros.append('curso_estilo: estilos precisam estar centralizados')
    for name in ('Documentos/PROTOCOLO_DESIGN.md', 'AGENTS.md'):
        if not (root / name).is_file():
            erros.append(f'Arquivo obrigatório ausente: {name}')
    return erros


if __name__ == '__main__':
    erros = verificar(Path(__file__).resolve().parents[2])
    print('\n'.join(erros) if erros else 'Protocolo estático de design aprovado. Inspeção visual exigida separadamente.')
    raise SystemExit(bool(erros))
