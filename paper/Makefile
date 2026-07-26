SHELL := /bin/bash
TEXINPUTS := ../AAAI_AuthorKit27//:$(TEXINPUTS)
BSTINPUTS := ../AAAI_AuthorKit27//:$(BSTINPUTS)

.PHONY: all main supplement clean

all: main supplement

main:
	TEXINPUTS="$(TEXINPUTS)" BSTINPUTS="$(BSTINPUTS)" latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

supplement:
	TEXINPUTS="$(TEXINPUTS)" BSTINPUTS="$(BSTINPUTS)" latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex

clean:
	latexmk -C main.tex supplement.tex
	rm -f *.bbl *.blg *.out *.fdb_latexmk *.fls
