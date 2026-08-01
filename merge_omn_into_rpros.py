#!/usr/bin/env python3
"""Prepend the presentation content from omn.tex to RPROS_Team4.tex."""

from __future__ import annotations

import re
from pathlib import Path


SOURCE = Path("omn.tex")
TARGET = Path("RPROS_Team4.tex")
START_MARKER = "% BEGIN CONTENT IMPORTED FROM omn.tex"
END_MARKER = "% END CONTENT IMPORTED FROM omn.tex"


def extract_content(source: str) -> str:
    """Return source slides, excluding document setup, title, and outline."""
    document_start = source.find(r"\begin{document}")
    document_end = source.rfind(r"\end{document}")
    first_section = source.find(r"\section", document_start)

    if document_start == -1 or document_end == -1 or first_section == -1:
        raise ValueError("omn.tex does not contain the expected document structure")
    if not document_start < first_section < document_end:
        raise ValueError("Could not locate the slide content inside omn.tex")

    content = source[first_section:document_end].strip()

    # The target's section-divider design relies on \presentationsection.
    # Preserve the original full section title as its navigation label.
    content = re.sub(
        r"(?m)^\\section\{([^{}]+)\}",
        lambda match: (
            rf"\presentationsection[{match.group(1)}]{{{match.group(1)}}}"
        ),
        content,
    )

    # Repair the malformed two-column calibration table in the source.
    content = content.replace(
        """             Type & Webcam
             & Frame & 640x480
             & FOV & 60
             & Calibrated Distance & 1 Meter 
             & Calibrated Pixels & 9750""",
        r"""             Type & Webcam \\
             Frame & 640x480 \\
             FOV & 60 \\
             Calibrated Distance & 1 Meter \\
             Calibrated Pixels & 9750""",
    )

    # Some image references in omn.tex omit the repository's img/ directory.
    def resolve_image(match: re.Match[str]) -> str:
        options = match.group(1) or ""
        image = match.group(2)
        if not Path(image).exists() and (Path("img") / image).exists():
            image = f"img/{image}"
        return rf"\includegraphics{options}{{{image}}}"

    return re.sub(
        r"\\includegraphics(\[[^\]]*\])?\{([^{}]+)\}",
        resolve_image,
        content,
    )


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    target = TARGET.read_text(encoding="utf-8")

    content = extract_content(source)

    # omn.tex uses \lstinline in its slides.
    if r"\lstinline" in content and r"\usepackage{listings}" not in target:
        package_anchor = r"\usepackage{hyperref}"
        if package_anchor not in target:
            raise ValueError("Could not find a package insertion point in the target")
        target = target.replace(
            package_anchor,
            package_anchor + "\n" + r"\usepackage{listings}",
            1,
        )

    imported = f"{START_MARKER}\n{content}\n{END_MARKER}\n\n"
    if START_MARKER in target and END_MARKER in target:
        block_start = target.index(START_MARKER)
        block_end = target.index(END_MARKER, block_start) + len(END_MARKER)
        while block_end < len(target) and target[block_end] == "\n":
            block_end += 1
        merged = target[:block_start] + imported + target[block_end:]
        action = "Refreshed"
    elif START_MARKER in target or END_MARKER in target:
        raise ValueError("The target contains only one import marker")
    else:
        # Insert after the target's title/outline and before its first content section.
        insertion_point = target.find(
            r"\presentationsection", target.find(r"\begin{document}")
        )
        if insertion_point == -1:
            raise ValueError("Could not find the first target presentation section")
        merged = target[:insertion_point] + imported + target[insertion_point:]
        action = "Imported"

    TARGET.write_text(merged, encoding="utf-8")
    print(f"{action} omn.tex content at the beginning of {TARGET}.")


if __name__ == "__main__":
    main()
