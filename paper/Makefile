SHELL := /bin/bash
TEXINPUTS := ../AAAI_AuthorKit27//:$(TEXINPUTS)
BSTINPUTS := ../AAAI_AuthorKit27//:$(BSTINPUTS)

.PHONY: all main supplement figures reproduce check clean

all: main supplement

main:
	TEXINPUTS="$(TEXINPUTS)" BSTINPUTS="$(BSTINPUTS)" latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

supplement:
	TEXINPUTS="$(TEXINPUTS)" BSTINPUTS="$(BSTINPUTS)" latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex

figures:
	cd .. && PYTHONPATH=src python -m experiments.run_all

reproduce: figures all

check: reproduce
	cd .. && python scripts/check_submission.py

clean:
	latexmk -C main.tex supplement.tex
	rm -f *.bbl *.blg *.out *.fdb_latexmk *.fls
