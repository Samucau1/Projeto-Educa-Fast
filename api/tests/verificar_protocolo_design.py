"""Portão estático do protocolo; a inspeção visual continua obrigatória."""
from pathlib import Path
import re


def verificar(root):
    web = root / 'web'
    erros = []
    for path in sorted((web / 'src/pages').glob('escola_*.jsx')):
        text = path.read_text(encoding='utf-8')
        if '<GestaoBase' not in text:
            erros.append(f'{path.name}: não usa o layout compartilhado')
        if re.search(r'<style\b|\sstyle\s*=|dangerouslySetInnerHTML|https?://', text, re.I):
            erros.append(f'{path.name}: estilo, HTML inline ou recurso externo não permitido')
    css = (web / 'public/css/escola.css').read_text(encoding='utf-8')
    if not all(token in css for token in ('var(--text)', 'var(--surface)', 'var(--accent)', 'var(--school-radius)')):
        erros.append('escola.css: faltam tokens compartilhados')
    for path in sorted((web / 'src/pages').glob('*.jsx')):
        if re.search(r'<style\b', path.read_text(encoding='utf-8')):
            erros.append(f'{path.name}: estilos precisam estar centralizados nos arquivos CSS')
    for name in ('docs/PROTOCOLO_DESIGN.md', 'AGENTS.md'):
        if not (root / name).is_file():
            erros.append(f'Arquivo obrigatório ausente: {name}')
    return erros


if __name__ == '__main__':
    erros = verificar(Path(__file__).resolve().parents[2])
    print('\n'.join(erros) if erros else 'Protocolo estático de design aprovado. Inspeção visual exigida separadamente.')
    raise SystemExit(bool(erros))
