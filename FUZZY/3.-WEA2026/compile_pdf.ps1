# compile_pdf.ps1
# Compila paper_wea2026.tex a PDF usando pdflatex + bibtex

$DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$TEX = "paper_wea2026"

Push-Location $DIR

Write-Host "=== Compilando $TEX.tex ===" -ForegroundColor Cyan

# Primera pasada
pdflatex -interaction=nonstopmode "$TEX.tex"
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR en primera pasada de pdflatex" -ForegroundColor Red; Pop-Location; exit 1 }

# BibTeX
bibtex "$TEX"
if ($LASTEXITCODE -ne 0) { Write-Host "ADVERTENCIA: bibtex retorno codigo $LASTEXITCODE" -ForegroundColor Yellow }

# Segunda pasada (resuelve referencias bibliograficas)
pdflatex -interaction=nonstopmode "$TEX.tex"
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR en segunda pasada de pdflatex" -ForegroundColor Red; Pop-Location; exit 1 }

# Tercera pasada (resuelve referencias cruzadas)
pdflatex -interaction=nonstopmode "$TEX.tex"
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR en tercera pasada de pdflatex" -ForegroundColor Red; Pop-Location; exit 1 }

if (Test-Path "$TEX.pdf") {
    Write-Host "=== PDF generado: $DIR\$TEX.pdf ===" -ForegroundColor Green
} else {
    Write-Host "ERROR: No se genero el PDF" -ForegroundColor Red
    Pop-Location; exit 1
}

Pop-Location
