#!/usr/bin/env python3
"""Validate the compiled AAAI submission for common hard failures."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def _run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stdout}"
        )
    return completed.stdout


def _technical_page(aux_text: str) -> int:
    for line in aux_text.splitlines():
        if r"\newlabel{lasttechnical}" not in line:
            continue
        match = re.search(
            r"\\newlabel\{lasttechnical\}\{\{.*?\}\{(\d+)\}",
            line,
        )
        if match:
            return int(match.group(1))
    raise ValueError(
        "paper/main.aux does not contain the lasttechnical page marker"
    )


def _font_issues(pdffonts_output: str) -> list[str]:
    lines = pdffonts_output.splitlines()
    if len(lines) < 3:
        return ["pdffonts returned no font table"]
    header = lines[0]
    try:
        embedded_start = header.index("emb")
        subset_start = header.index("sub", embedded_start)
    except ValueError:
        return ["could not parse the pdffonts header"]

    issues: list[str] = []
    for line in lines[2:]:
        if not line.strip():
            continue
        lowered = line.lower()
        if "type 3" in lowered:
            issues.append(f"Type 3 font: {line.strip()}")
        embedded = line[embedded_start:subset_start].strip().lower()
        if embedded == "no":
            issues.append(f"unembedded font: {line.strip()}")
    return issues


def _large_overfull_boxes(log_text: str, threshold: float) -> list[str]:
    issues = []
    pattern = re.compile(r"Overfull \\hbox \(([\d.]+)pt too wide\)")
    for line in log_text.splitlines():
        match = pattern.search(line)
        if match and float(match.group(1)) > threshold:
            issues.append(line.strip())
    return issues


def _pdf_metadata_issues(pdfinfo: str, pdf_name: str) -> list[str]:
    issues: list[str] = []
    page_size_match = re.search(r"^Page size:\s+(.+)$", pdfinfo, re.MULTILINE)
    page_size = page_size_match.group(1).strip() if page_size_match else "unknown"
    if "612 x 792" not in page_size and "letter" not in page_size.lower():
        issues.append(f"{pdf_name} is not US letter: {page_size}")

    author_match = re.search(r"^Author:\s*(.*)$", pdfinfo, re.MULTILINE)
    if author_match:
        author = author_match.group(1).strip()
        if author and "anonymous" not in author.lower():
            issues.append(f"{pdf_name} has non-anonymous Author metadata: {author}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--technical-page-limit", type=int, default=7)
    parser.add_argument("--overfull-threshold", type=float, default=2.0)
    args = parser.parse_args()

    root = args.root.resolve()
    paper = root / "paper"
    main_pdf = paper / "main.pdf"
    supplement_pdf = paper / "supplement.pdf"
    checklist_pdf = paper / "reproducibility_checklist.pdf"
    checklist_source = paper / "reproducibility_checklist.tex"
    pdfs = (main_pdf, supplement_pdf, checklist_pdf)
    logs = (
        paper / "main.log",
        paper / "supplement.log",
        paper / "reproducibility_checklist.log",
    )
    required = [
        *pdfs,
        *logs,
        paper / "main.aux",
        checklist_source,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print("Missing build products:")
        for path in missing:
            print(f"  - {path}")
        return 1

    issues: list[str] = []
    technical_page = _technical_page(
        (paper / "main.aux").read_text(errors="replace")
    )
    if technical_page > args.technical_page_limit:
        issues.append(
            f"technical content reaches page {technical_page}, "
            f"above limit {args.technical_page_limit}"
        )

    checklist_text = checklist_source.read_text(errors="replace")
    # The official template contains the placeholder three times in its
    # instructions/example. Any additional occurrence is an unanswered item.
    placeholder_count = checklist_text.count("Type your response here")
    if placeholder_count > 3:
        issues.append(
            "reproducibility checklist still contains unanswered placeholders"
        )

    main_pdfinfo = _run(["pdfinfo", str(main_pdf)], cwd=root)
    pages_match = re.search(r"^Pages:\s+(\d+)", main_pdfinfo, re.MULTILINE)
    page_size_match = re.search(
        r"^Page size:\s+(.+)$", main_pdfinfo, re.MULTILINE
    )
    total_pages = int(pages_match.group(1)) if pages_match else -1
    main_page_size = (
        page_size_match.group(1).strip() if page_size_match else "unknown"
    )

    for pdf in pdfs:
        pdfinfo = _run(["pdfinfo", str(pdf)], cwd=root)
        issues.extend(_pdf_metadata_issues(pdfinfo, pdf.name))
        font_output = _run(["pdffonts", str(pdf)], cwd=root)
        issues.extend(
            f"{pdf.name}: {issue}" for issue in _font_issues(font_output)
        )

    fatal_log_markers = (
        "! LaTeX Error:",
        "Undefined control sequence",
        "There were undefined references",
        "There were undefined citations",
    )
    overfull: list[str] = []
    for log_path in logs:
        log_text = log_path.read_text(errors="replace")
        for marker in fatal_log_markers:
            if marker in log_text:
                issues.append(f"{log_path.name}: {marker}")
        overfull.extend(
            f"{log_path.name}: {line}"
            for line in _large_overfull_boxes(
                log_text, args.overfull_threshold
            )
        )
    issues.extend(overfull)

    print("AAAI submission validation")
    print(f"  technical content through page: {technical_page}")
    print(f"  main PDF total pages: {total_pages}")
    print(f"  main PDF page size: {main_page_size}")
    for pdf in pdfs:
        print(f"  built PDF: {pdf}")

    if issues:
        print("\nValidation failures:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("\nAll automated submission checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
