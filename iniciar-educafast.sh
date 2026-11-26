#!/usr/bin/env bash
# EducaFast: ambiente de teste manual + tutorial guiado (macOS e Linux).
# Equivalente ao iniciar-educafast.ps1 do Windows. Compatível com o bash 3.2 do macOS.
#
# Uso:
#   ./iniciar-educafast.sh              sobe o ambiente, faz o tutorial e abre o menu de logins
#   ./iniciar-educafast.sh iniciar --sem-tutorial   sobe o ambiente e vai direto ao menu
#   ./iniciar-educafast.sh iniciar --sem-navegador  não abre o navegador sozinho
#   ./iniciar-educafast.sh status       mostra os containers
#   ./iniciar-educafast.sh logins       mostra os logins de teste
#   ./iniciar-educafast.sh parar        encerra o ambiente e DESCARTA os dados de demonstração

set -u

URL='http://127.0.0.1:5050'
SENHA='Teste-local-2026!'
RAIZ="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="$RAIZ/api/docker-compose.test.yml"
FOLHA="$RAIZ/LOGINS-EDUCAFAST.txt"
ROTEIRO="$RAIZ/docs/testes/TESTE_MANUAL.md"
LOG="${TMPDIR:-/tmp}/educafast-iniciar.log"

# Perfis criados automaticamente no primeiro uso do banco (api/tests/fixtures.py).
PERFIS=('Superperfil (direção / dono da plataforma)' 'Administrador (secretaria)' 'Professor' 'Aluno' 'Outro aluno (sem vínculo com a turma)')
EMAILS=('superadmin@teste.local' 'admin@teste.local' 'professor@teste.local' 'aluno@teste.local' 'outro_aluno@teste.local')

ACAO='iniciar'
SEM_TUTORIAL=0
SEM_NAVEGADOR=0
for arg in "$@"; do
    case "$arg" in
        iniciar|status|parar|logins) ACAO="$arg" ;;
        --sem-tutorial) SEM_TUTORIAL=1 ;;
        --sem-navegador) SEM_NAVEGADOR=1 ;;
        -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
        *) echo "Opção desconhecida: $arg (use --help)"; exit 2 ;;
    esac
done

if [ -t 1 ]; then
    AZUL=$'\033[36m'; VERDE=$'\033[32m'; AMARELO=$'\033[33m'; VERMELHO=$'\033[31m'; NEGRITO=$'\033[1m'; FIM=$'\033[0m'
else
    AZUL=''; VERDE=''; AMARELO=''; VERMELHO=''; NEGRITO=''; FIM=''
fi

log() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG"; }
info() { printf '%s%s%s\n' "$AZUL" "$*" "$FIM"; log "INFO $*"; }
ok() { printf '%s%s%s\n' "$VERDE" "$*" "$FIM"; log "OK $*"; }
aviso() { printf '%s%s%s\n' "$AMARELO" "$*" "$FIM"; log "AVISO $*"; }
falhar() {
    printf '\n%sNão foi possível concluir: %s%s\n' "$VERMELHO" "$*" "$FIM" >&2
    printf 'Detalhes técnicos em: %s\n' "$LOG" >&2
    log "ERRO $*"
    exit 1
}

pausar() {
    # Sem terminal interativo (ex.: CI), segue sem esperar.
    [ -t 0 ] || return 0
    printf '%s' "${1:-Pressione Enter para continuar...}"
    read -r _ || true
}

abrir() {
    [ "$SEM_NAVEGADOR" -eq 1 ] && { echo "   Abra no navegador: $1"; return 0; }
    if command -v open >/dev/null 2>&1; then open "$1" >/dev/null 2>&1 && return 0
    elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$1" >/dev/null 2>&1 && return 0
    fi
    echo "   Abra no navegador: $1"
}

copiar() {
    if command -v pbcopy >/dev/null 2>&1; then printf '%s' "$1" | pbcopy && return 0; fi
    return 1
}

# ---------- Docker ----------

achar_docker() {
    if command -v docker >/dev/null 2>&1; then DOCKER="$(command -v docker)"; return 0; fi
    for c in /usr/local/bin/docker /opt/homebrew/bin/docker /Applications/Docker.app/Contents/Resources/bin/docker "$HOME/.docker/bin/docker"; do
        if [ -x "$c" ]; then DOCKER="$c"; return 0; fi
    done
    falhar 'Docker Desktop não encontrado. Instale em https://www.docker.com/products/docker-desktop/ e rode de novo.'
}

docker_ligado() { "$DOCKER" info --format '{{.ServerVersion}}' >/dev/null 2>&1; }

garantir_docker() {
    docker_ligado && return 0
    if [ "$ACAO" != 'iniciar' ]; then
        echo 'O Docker está desligado. Nenhuma ação foi executada.'
        exit 0
    fi
    if [ -d /Applications/Docker.app ] && command -v open >/dev/null 2>&1; then
        info 'Abrindo o Docker Desktop (pode levar até 3 minutos)...'
        open -a Docker >>"$LOG" 2>&1 || falhar 'Não consegui abrir o Docker Desktop. Abra manualmente e rode de novo.'
    else
        falhar 'O Docker está desligado. Abra o Docker Desktop e rode de novo.'
    fi
    local limite=$(( $(date +%s) + 180 ))
    until docker_ligado; do
        [ "$(date +%s)" -ge "$limite" ] && falhar 'O Docker não ficou pronto em 3 minutos. Confira o Docker Desktop e tente de novo.'
        sleep 2
    done
    ok 'Docker pronto.'
}

compose() {
    log "docker compose $*"
    "$DOCKER" compose -p educafast-manual -f "$COMPOSE" --profile manual "$@"
}

aplicacao_respondendo() {
    command -v curl >/dev/null 2>&1 || return 0
    curl -fsS --max-time 15 "$URL/" 2>>"$LOG" | grep -Eq "<form[^>]*id=[\"']login-form[\"']"
}

# ---------- Folha de logins ----------

escrever_folha() {
    {
        echo 'EDUCAFAST - LOGINS DE TESTE'
        echo '==========================='
        echo
        echo "Endereço: $URL"
        echo "Senha de TODOS os usuários: $SENHA"
        echo
        local i=0
        while [ $i -lt ${#EMAILS[@]} ]; do
            printf '%-26s %s\n' "${EMAILS[$i]}" "${PERFIS[$i]}"
            i=$((i + 1))
        done
        echo
        echo 'Dicas'
        echo '- Para trocar de perfil, clique em "Sair do sistema" antes de entrar com outro login.'
        echo '- Para usar dois perfis ao mesmo tempo, abra o segundo numa janela anônima.'
        echo '- Os dados são fictícios e ficam só no Docker desta máquina.'
        echo '- Roteiro completo de testes: docs/testes/TESTE_MANUAL.md'
        echo
        echo 'Comandos (Terminal, na pasta do projeto)'
        echo '  ./iniciar-educafast.sh                  sobe o ambiente e mostra o tutorial'
        echo '  ./iniciar-educafast.sh iniciar --sem-tutorial   vai direto ao menu de logins'
        echo '  ./iniciar-educafast.sh logins           mostra esta folha no terminal'
        echo '  ./iniciar-educafast.sh parar            encerra e apaga os dados de demonstração'
    } > "$FOLHA" || aviso "Não consegui salvar $FOLHA."
}

mostrar_logins() {
    echo
    printf '%sLOGINS DE TESTE%s  (endereço: %s)\n' "$NEGRITO" "$FIM" "$URL"
    printf 'Senha de todos: %s%s%s\n\n' "$NEGRITO" "$SENHA" "$FIM"
    local i=0
    while [ $i -lt ${#EMAILS[@]} ]; do
        printf '  %d) %-26s %s\n' $((i + 1)) "${EMAILS[$i]}" "${PERFIS[$i]}"
        i=$((i + 1))
    done
    echo
    echo "Folha salva em: $FOLHA"
}

entrar_como() {
    # $1 = índice do perfil
    local email="${EMAILS[$1]}"
    echo
    printf 'Perfil: %s%s%s\n' "$NEGRITO" "${PERFIS[$1]}" "$FIM"
    printf '  E-mail: %s\n  Senha:  %s\n' "$email" "$SENHA"
    if copiar "$email"; then
        echo '  (o e-mail já está copiado; cole com Cmd+V)'
    fi
    abrir "$URL/"
    if [ -t 0 ] && command -v pbcopy >/dev/null 2>&1; then
        pausar '  Depois de colar o e-mail, pressione Enter para copiar a senha...'
        copiar "$SENHA" && echo '  Senha copiada. Cole com Cmd+V.'
    fi
}

# ---------- Tutorial ----------

passo() {
    # $1 número, $2 índice do perfil, $3.. linhas do que fazer
    local numero="$1" perfil="$2"
    shift 2
    echo
    printf '%s━━━ Passo %s de 4 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%s\n' "$AZUL" "$numero" "$FIM"
    printf '%s%s%s\n' "$NEGRITO" "${PERFIS[$perfil]}" "$FIM"
    local linha
    for linha in "$@"; do echo "  • $linha"; done
    echo
    pausar 'Pressione Enter para abrir o login deste perfil...'
    entrar_como "$perfil"
    echo
    pausar 'Quando terminar de explorar, clique em "Sair do sistema" e pressione Enter aqui...'
}

tutorial() {
    echo
    printf '%sTUTORIAL GUIADO DO EDUCAFAST%s\n' "$NEGRITO" "$FIM"
    echo 'Vamos passar pelos 4 perfis do sistema. Em cada passo o navegador abre no login'
    echo 'e o e-mail já vai copiado. Digite "p" e Enter para pular o tutorial.'
    if [ -t 0 ]; then
        printf 'Começar? [Enter = sim / p = pular] '
        local resposta=''
        read -r resposta || true
        case "$resposta" in p|P) return 0 ;; esac
    fi

    passo 1 0 \
        'É o dono da escola na plataforma: define as regras da instituição.' \
        'Abra a gestão de usuários: veja todos os perfis já cadastrados.' \
        'Crie um usuário novo (ex.: outro professor) e teste o login dele depois.' \
        'Abra "Cores do layout" e "Mensagens": só o superperfil mexe nas cores.'

    passo 2 1 \
        'É a secretaria: cuida de turmas, disciplinas, alunos e documentos.' \
        'Confira a Turma A e as disciplinas de demonstração (Matemática e Física).' \
        'Publique um comunicado e veja que ele aparece para todos.' \
        'Repare que o administrador NÃO acessa a gestão do superperfil.'

    passo 3 2 \
        'O professor rege as disciplinas em que está vinculado.' \
        'Abra Matemática: lance uma atividade e uma nota para o aluno.' \
        'Veja o curso "Álgebra para todos os anos" e as aulas dele.' \
        'Ele lê mensagens, mas não acessa as telas da secretaria.'

    passo 4 3 \
        'O aluno vê as disciplinas, o curso, as notas e os comunicados.' \
        'Abra Matemática e confira a atividade e a nota lançadas no passo 3.' \
        'Tente abrir /super/usuarios na barra de endereço: deve dar acesso negado.' \
        'Opcional: entre como "outro_aluno@teste.local", que não vê a turma.'

    echo
    ok 'Tutorial concluído! Agora o sistema é todo seu para explorar e testar.'
}

# ---------- Menu final ----------

menu() {
    [ -t 0 ] || { mostrar_logins; return 0; }
    while true; do
        echo
        printf '%sMENU%s  (o sistema continua rodando em %s)\n' "$NEGRITO" "$FIM" "$URL"
        local i=0
        while [ $i -lt ${#EMAILS[@]} ]; do
            printf '  %d) Entrar como %s\n' $((i + 1)) "${PERFIS[$i]}"
            i=$((i + 1))
        done
        echo '  l) Mostrar os logins de novo'
        echo '  r) Abrir o roteiro completo de testes'
        echo '  t) Refazer o tutorial'
        echo '  e) Encerrar o ambiente e apagar os dados de demonstração'
        echo '  0) Sair do menu (o sistema continua no ar)'
        printf 'Escolha: '
        local op=''
        read -r op || break
        case "$op" in
            [1-5]) entrar_como $((op - 1)) ;;
            l|L) mostrar_logins ;;
            r|R) abrir "$ROTEIRO" ;;
            t|T) tutorial ;;
            e|E)
                printf 'Isso apaga tudo que foi criado nos testes. Confirmar? [s/N] '
                local c=''
                read -r c || true
                case "$c" in s|S) parar; return 0 ;; *) echo 'Cancelado.' ;; esac ;;
            0) break ;;
            *) echo 'Opção inválida.' ;;
        esac
    done
    echo
    echo "O EducaFast continua rodando em $URL. Logins em: $FOLHA"
    echo 'Para encerrar depois: ./iniciar-educafast.sh parar'
}

# ---------- Ações ----------

iniciar() {
    info 'Preparando a aplicação e o MySQL de testes (na primeira vez o Docker baixa as imagens e pode demorar alguns minutos)...'
    compose up -d --build --wait --wait-timeout 300 manual 2>&1 | tee -a "$LOG"
    [ "${PIPESTATUS[0]}" -eq 0 ] || falhar 'O Docker não conseguiu subir o ambiente. Confira a mensagem acima.'
    aplicacao_respondendo || falhar "Os containers subiram, mas a tela de login não respondeu em $URL."
    escrever_folha
    echo
    ok "EducaFast no ar: $URL"
    mostrar_logins
    if [ "$SEM_TUTORIAL" -eq 0 ]; then
        tutorial
    elif [ "$SEM_NAVEGADOR" -eq 0 ]; then
        abrir "$URL/"
    fi
    menu
}

parar() {
    aviso 'Encerrando o ambiente e descartando os dados de demonstração...'
    compose down 2>&1 | tee -a "$LOG"
    [ "${PIPESTATUS[0]}" -eq 0 ] || falhar 'O Docker não conseguiu encerrar o ambiente.'
    ok 'Ambiente encerrado. Na próxima vez os dados de exemplo são recriados do zero.'
}

[ -f "$COMPOSE" ] || falhar 'Não encontrei api/docker-compose.test.yml. Mantenha este script na raiz do projeto.'
log "---- início: ação=$ACAO"

case "$ACAO" in
    logins) mostrar_logins; exit 0 ;;
esac

achar_docker
garantir_docker
cd "$RAIZ" || falhar "Não consegui entrar em $RAIZ."

case "$ACAO" in
    iniciar) iniciar ;;
    status) compose ps; echo "Endereço: $URL" ;;
    parar) parar ;;
esac
