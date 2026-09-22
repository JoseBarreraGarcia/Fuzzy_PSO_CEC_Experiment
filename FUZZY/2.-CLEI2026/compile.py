"""
Compila manuscript.tex a PDF usando pdflatex + bibtex.
Ejecutar con F5 desde VS Code o: python compile.py [--clean] [--open]
"""
import subprocess
import sys
import os
import argparse

DIR = os.path.dirname(os.path.abspath(__file__))
JOB = "manuscript"

def run(cmd, label):
    print(f"\n[{label}]")
    result = subprocess.run(cmd, cwd=DIR)
    return result.returncode

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="Eliminar auxiliares antes de compilar")
    parser.add_argument("--open",  action="store_true", help="Abrir PDF al finalizar")
    args = parser.parse_args()

    if args.clean:
        print("[Limpieza] Eliminando archivos auxiliares...")
        for ext in ["aux","log","bbl","blg","out","toc","lof","lot","fls","fdb_latexmk","synctex.gz"]:
            f = os.path.join(DIR, f"{JOB}.{ext}")
            if os.path.exists(f):
                os.remove(f)

    pdflatex = ["pdflatex", "-interaction=nonstopmode", "-file-line-error", f"{JOB}.tex"]

    run(pdflatex,              "pdflatex (pasada 1/3)")
    run(["bibtex", JOB],       "bibtex")
    run(pdflatex,              "pdflatex (pasada 2/3)")
    run(pdflatex,              "pdflatex (pasada 3/3)")

    pdf = os.path.join(DIR, f"{JOB}.pdf")
    if os.path.exists(pdf):
        print(f"\nPDF generado: {pdf}")
        if args.open:
            os.startfile(pdf)
    else:
        print("\nERROR: No se generó el PDF. Revisa manuscript.log")
        sys.exit(1)

if __name__ == "__main__":
    main()
