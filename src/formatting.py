"""Turn papers into text for the terminal. Pure functions: no I/O, no database."""

import shutil
import textwrap

LABEL_WIDTH = 13  # room for "Primary cat." plus a gap


def _width() -> int:
    """Wrap text to the terminal width, but never wider than is comfortable to read."""
    return min(shutil.get_terminal_size((80, 24)).columns, 100)


def _wrap(text: str, indent: str = "", hanging: str | None = None) -> str:
    """Wrap `text`; later lines use `hanging` as their indent (default: same as `indent`)."""
    return textwrap.fill(
        text,
        _width(),
        initial_indent=indent,
        subsequent_indent=indent if hanging is None else hanging,
        break_long_words=False,  # keep URLs and IDs whole
        break_on_hyphens=False,
    )


def paper_label(paper: dict) -> str:
    """The short name used wherever a paper is mentioned, e.g. 'Some Title (2610.12345)'."""
    return f"{paper['title']} ({paper['id']})"


def result_line(number: int, paper: dict, number_width: int = 2) -> str:
    """One numbered list entry, e.g. ' 3. Some Title (2610.12345)'."""
    prefix = f"{number:>{number_width}}. "
    return _wrap(paper_label(paper), prefix, " " * len(prefix))


def category_list(categories: dict[str, list[tuple[str, str]]], aliases: dict[str, str] | None = None) -> str:
    """Categories under their group headings, one 'code  name' per line.
    Codes in `aliases` are marked as an alias of the code arXiv really files papers under."""
    aliases = aliases or {}
    lines = []
    for group, cats in categories.items():
        code_width = max(len(code) for code, _name in cats)  # align each group on its own
        lines += ["", group]
        for code, name in cats:
            target = aliases.get(code)
            label = f"{name} (alias of {target})" if target else name
            lines.append(_wrap(label, f"  {code:<{code_width}}  ", " " * (code_width + 4)))
    return "\n".join(lines)


def _field(label: str, value: str) -> str:
    """A 'Label       value' row whose wrapped lines line up under the value."""
    return _wrap(value or "(not recorded)", f"{label:<{LABEL_WIDTH}}", " " * LABEL_WIDTH)


def paper_details(paper: dict, pinned: bool) -> str:
    """Everything stored about one paper, laid out for reading."""
    rule = "─" * _width()
    return "\n".join([
        rule,
        _wrap(paper["title"]),
        rule,
        _field("arXiv ID", paper["id"]),
        _field("Year", str(paper["year"])),
        _field("Authors", paper["authors"]),
        _field("Primary cat.", paper.get("primary_category", "")),
        _field("Categories", paper.get("categories", "")),
        _field("Page", paper["url"]),
        _field("PDF", paper["pdf_url"]),
        _field("Pinned", "yes" if pinned else "no"),
        "",
        "Abstract",
        _wrap(paper["abstract"], indent="  "),
        rule,
    ])
