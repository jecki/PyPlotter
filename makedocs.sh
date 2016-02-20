#!/bin/sh

sh cleanup.sh

pdflatex PyPlotter_Doc.tex
pdflatex PyPlotter_Doc.tex

#latex2html -local_icons PyPlotter_Doc.tex
python3 latex2html.py PyPlotter_Doc.tex
#tar -cvf PyPlotter_Doc.html.tar PyPlotter_Doc
#gzip PyPlotter_Doc.html.tar
cp PyPlotter_Doc.pdf PyPlotter_Doc

rm PyPlotter_Doc.log
rm PyPlotter_Doc.aux
rm PyPlotter_Doc.toc
