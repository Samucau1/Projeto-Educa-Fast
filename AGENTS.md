# EducaFast — instruções de desenvolvimento

Antes de criar ou alterar interfaces, leia `Documentos/PROTOCOLO_DESIGN.md` e reutilize o layout, tokens e componentes existentes.

Toda alteração visual deve passar pelo verificador `Códigos/tests/verificar_protocolo_design.py`, pelo fluxo funcional pertinente e por inspeção de capturas desktop/móvel. Uma nova opção de tema exige conferir também a paleta personalizada. Não introduza outro design system, CSS arbitrário configurável ou dependências externas sem necessidade demonstrada.

Configurações institucionais pertencem ao superadmin. Preserve regras acadêmicas aplicadas e dados históricos; mudanças de divisão/pesos exigem uma nova versão explícita. Use bancos sintéticos descartáveis para testes e nunca deduza vínculos históricos.
