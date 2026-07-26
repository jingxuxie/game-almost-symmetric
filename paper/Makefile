SHELL := /bin/bash
TEXINPUTS := ../AAAI_AuthorKit27//:$(TEXINPUTS)
BSTINPUTS := ../AAAI_AuthorKit27//:$(BSTINPUTS)

FIGURES := \
	../experiments/figures/nonstrategic_separation.pdf \
	../experiments/figures/certificate_calibration.pdf \
	../experiments/figures/compression_frontier.pdf \
	../experiments/figures/role_assignment.pdf \
	../experiments/figures/runtime_scaling.pdf \
	../experiments/figures/sampling_certificate.pdf \
	../experiments/figures/reynolds_tightness.pdf

.PHONY: all main supplement checklist figures reproduce check clean

all: main supplement checklist

main: figures
	TEXINPUTS="$(TEXINPUTS)" BSTINPUTS="$(BSTINPUTS)" latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

supplement:
	TEXINPUTS="$(TEXINPUTS)" BSTINPUTS="$(BSTINPUTS)" latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex

checklist:
	TEXINPUTS="$(TEXINPUTS)" BSTINPUTS="$(BSTINPUTS)" latexmk -pdf -interaction=nonstopmode -halt-on-error reproducibility_checklist.tex

figures: $(FIGURES)

$(FIGURES):
	cd .. && PYTHONPATH=src python -m experiments.run_all

reproduce: all

check: all
	cd .. && python scripts/check_submission.py

clean:
	latexmk -C main.tex supplement.tex reproducibility_checklist.tex
	rm -f *.bbl *.blg *.out *.fdb_latexmk *.fls
