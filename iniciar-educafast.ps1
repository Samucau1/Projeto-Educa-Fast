[CmdletBinding()]
param(
    [ValidateSet('Iniciar', 'Parar', 'Status')]
    [string]$Acao = 'Iniciar',
    [switch]$SemNavegador
)

$ErrorActionPreference = 'Stop'
$manualUrl = 'http://127.0.0.1:5050'
$composePath = Join-Path $PSScriptRoot 'Códigos/docker-compose.test.yml'
$composeArguments = @('compose', '-p', 'educafast-manual', '-f', $composePath, '--profile', 'manual')

function Test-DockerEngine {
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $script:DockerExecutable info --format '{{.ServerVersion}}' *> $null
        return ($LASTEXITCODE -eq 0)
    }
    finally { $ErrorActionPreference = $previousPreference }
}

function Invoke-ManualDocker {
    param([string[]]$Arguments)
    & $script:DockerExecutable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "O Docker retornou o código $LASTEXITCODE. Confira a mensagem acima."
    }
}

try {
    if (-not (Test-Path -LiteralPath $composePath)) {
        throw 'Não encontrei Códigos/docker-compose.test.yml. Mantenha o script na raiz do projeto.'
    }
    $dockerCommand = Get-Command docker.exe -ErrorAction SilentlyContinue
    if ($dockerCommand) {
        $script:DockerExecutable = $dockerCommand.Source
    }
    else {
        $script:DockerExecutable = Join-Path $env:ProgramFiles 'Docker/Docker/resources/bin/docker.exe'
        if (-not (Test-Path -LiteralPath $script:DockerExecutable)) {
            throw 'Docker Desktop não encontrado. Instale-o antes de iniciar o teste manual.'
        }
    }

    Push-Location -LiteralPath $PSScriptRoot
    try {
        if (-not (Test-DockerEngine)) {
            if ($Acao -ne 'Iniciar') {
                Write-Host 'O Docker está desligado. Nenhuma ação foi executada.'
                exit 0
            }
            $desktopPath = Join-Path $env:ProgramFiles 'Docker/Docker/Docker Desktop.exe'
            if (-not (Test-Path -LiteralPath $desktopPath)) {
                throw 'Abra o Docker Desktop e execute o script novamente.'
            }
            Write-Host 'Iniciando Docker Desktop...' -ForegroundColor Cyan
            Start-Process -FilePath $desktopPath -WindowStyle Hidden
            $dockerDeadline = (Get-Date).AddMinutes(3)
            while (-not (Test-DockerEngine)) {
                if ((Get-Date) -ge $dockerDeadline) {
                    throw 'O Docker não ficou pronto em 3 minutos. Confira o Docker Desktop e tente novamente.'
                }
                Start-Sleep -Seconds 2
            }
        }

        if ($Acao -eq 'Parar') {
            Write-Host 'Encerrando o ambiente manual e descartando seus dados de demonstração...' -ForegroundColor Yellow
            Invoke-ManualDocker -Arguments ($composeArguments + @('down'))
            Write-Host 'Ambiente manual encerrado. O MySQL instalado não foi alterado.' -ForegroundColor Green
        }
        elseif ($Acao -eq 'Status') {
            Invoke-ManualDocker -Arguments ($composeArguments + @('ps'))
            Write-Host "Endereço do ambiente manual: $manualUrl"
        }
        else {
            Write-Host 'Preparando a aplicação e o MySQL de testes...' -ForegroundColor Cyan
            Invoke-ManualDocker -Arguments ($composeArguments + @('up', '-d', '--build', '--wait', '--wait-timeout', '180', 'manual'))
            $response = Invoke-WebRequest -Uri $manualUrl -UseBasicParsing -TimeoutSec 15
            # A marca e o nome da escola são personalizáveis; valide o formulário de acesso.
            if ($response.StatusCode -ne 200 -or $response.Content -notmatch '<form\b[^>]*\bid=["'']login-form["'']') {
                throw "Os containers iniciaram, mas não consegui confirmar a aplicação em $manualUrl."
            }

            Write-Host "`nTeste manual pronto: $manualUrl" -ForegroundColor Green
            Write-Host 'Aplicação e banco estão rodando em segundo plano. Você pode fechar este terminal.'
            Write-Host 'Senha de todos os usuários de exemplo: Teste-local-2026!'
            Write-Host '  Superperfil: superadmin@teste.local'
            Write-Host '  Admin:       admin@teste.local'
            Write-Host '  Professor:   professor@teste.local'
            Write-Host '  Aluno:       aluno@teste.local'
            Write-Host '  Outro aluno: outro_aluno@teste.local'
            Write-Host "`nRoteiro: Documentos/testes/TESTE_MANUAL.md"
            Write-Host 'Os dados atuais são preservados ao iniciar novamente.'
            Write-Host 'Para consultar o ambiente: .\iniciar-educafast.ps1 -Acao Status'
            Write-Host 'Para encerrar e descartar os dados: .\iniciar-educafast.ps1 -Acao Parar'
            if (-not $SemNavegador) {
                try { Start-Process -FilePath $manualUrl }
                catch { Write-Host "Ambiente pronto. Abra o navegador em $manualUrl." -ForegroundColor Yellow }
            }
        }
    }
    finally { Pop-Location }
}
catch {
    Write-Host "`nNão foi possível concluir: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
