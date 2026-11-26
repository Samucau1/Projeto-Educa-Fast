#!/usr/bin/env bash
# macOS: dê dois cliques neste arquivo no Finder para subir o EducaFast com o tutorial.
# Na primeira vez, se o macOS bloquear, clique com o botão direito > Abrir > Abrir.
cd "$(dirname "$0")" || exit 1
bash ./iniciar-educafast.sh "$@"
resultado=$?
echo
[ "$resultado" -ne 0 ] && echo 'O EducaFast não iniciou. Confira a mensagem acima.'
read -r -p 'Pressione Enter para fechar esta janela...' _
exit "$resultado"
