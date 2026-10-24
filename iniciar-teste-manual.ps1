[CmdletBinding()]
param(
    [ValidateSet('Iniciar', 'Parar', 'Status')]
    [string]$Acao = 'Iniciar',
    [switch]$SemNavegador
)

# Atalho compatível com o nome anterior.
& (Join-Path $PSScriptRoot 'iniciar-educafast.ps1') @PSBoundParameters
exit $LASTEXITCODE
