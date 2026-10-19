[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$manuscriptDirectory = $PSScriptRoot
$mainTex = Join-Path $manuscriptDirectory 'main.tex'

if (-not (Test-Path $mainTex)) {
    throw "Manuscript entry point not found: $mainTex"
}

foreach ($toolName in @('pdflatex', 'bibtex')) {
    if (-not (Get-Command $toolName -ErrorAction SilentlyContinue)) {
        throw "Required LaTeX tool '$toolName' was not found on PATH. Install MiKTeX or TeX Live and reopen PowerShell."
    }
}

function Invoke-LatexTool {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Tool,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Write-Host "> $Tool $($Arguments -join ' ')"
    & $Tool @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Tool failed with exit code $LASTEXITCODE. See main.log for details."
    }
}

Push-Location $manuscriptDirectory
try {
    Invoke-LatexTool -Tool 'pdflatex' -Arguments @('-interaction=nonstopmode', '-halt-on-error', '-file-line-error', 'main.tex')
    Invoke-LatexTool -Tool 'bibtex' -Arguments @('main')
    Invoke-LatexTool -Tool 'pdflatex' -Arguments @('-interaction=nonstopmode', '-halt-on-error', '-file-line-error', 'main.tex')
    Invoke-LatexTool -Tool 'pdflatex' -Arguments @('-interaction=nonstopmode', '-halt-on-error', '-file-line-error', 'main.tex')
}
finally {
    Pop-Location
}

Write-Host "Build complete: $(Join-Path $manuscriptDirectory 'main.pdf')"
