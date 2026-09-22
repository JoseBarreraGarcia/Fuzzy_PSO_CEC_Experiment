@echo off
REM Compila manuscript.tex a PDF (pdflatex + bibtex)
setlocal
cd /d "%~dp0"

where pdflatex >nul 2>&1 || (echo ERROR: pdflatex no encontrado en PATH. & exit /b 1)
where bibtex   >nul 2>&1 || (echo ERROR: bibtex no encontrado en PATH.   & exit /b 1)

set JOB=manuscript
set OPTS=-interaction=nonstopmode -file-line-error

if /I "%1"=="clean" (
    echo [Limpieza] auxiliares...
    for %%E in (aux log bbl blg out toc lof lot fls fdb_latexmk synctex.gz) do if exist %JOB%.%%E del /q %JOB%.%%E
)

echo [pdflatex 1/3]
pdflatex %OPTS% %JOB%.tex || goto :err
echo [bibtex]
bibtex %JOB%              || goto :err
echo [pdflatex 2/3]
pdflatex %OPTS% %JOB%.tex || goto :err
echo [pdflatex 3/3]
pdflatex %OPTS% %JOB%.tex || goto :err

echo.
echo PDF generado: %CD%\%JOB%.pdf
exit /b 0

:err
echo.
echo Error en compilacion. Revisa %JOB%.log
exit /b 1
