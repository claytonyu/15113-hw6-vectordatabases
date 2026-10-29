"""Text interface: a command loop for searching, viewing, pinning and adding papers."""

import re
from dataclasses import dataclass, field

import requests

from . import categories, formatting, library, pins, store

# New-style IDs look like 1706.03762, old-style ones like hep-th/9901001; a version suffix is optional.
ARXIV_ID = re.compile(r"^(\d{4}\.\d{4,5}|[a-z-]+(\.[A-Za-z-]+)?/\d{7})(v\d+)?$")

DEFAULT_PAGE_SIZE = 10
DEFAULT_CATEGORY_LIMIT = 20

# Offered when the library is empty: the newest papers of these arXiv categories.
STARTER_CATEGORIES = ("cs.CL", "q-bio.CB")
STARTER_PAPERS_EACH = 250

HELP = """\
Commands (short forms in brackets)
  search <text>        Find papers by meaning, e.g. search making models follow instructions  [s]
  more                 Show the next page of the last search  [m]
  limit [n]            Show, or set, how many results appear at a time
  view <n|id>          Show everything stored about a paper  [v]
  pin [n|id]           Pin a paper. With no argument: the paper you viewed last  [p]
  unpin [n|id]         Remove a pin. With no argument: the paper you viewed last
  pins                 List your pinned papers
  addid <arXiv id>     Fetch one paper from arXiv and add it, e.g. addid 1706.03762
  addcat <cat> [k]     Fetch the k newest papers of an arXiv category (default 20),
                       e.g. addcat cs.CL 50. Without a category: list all valid ones
  help                 Show this list  [h]
  quit                 Leave  [q]

<n> is the number beside a paper in the latest list (search results or pins).
<id> is an arXiv ID. Either one works anywhere a paper is expected."""


@dataclass
class Session:
    db: str
    page_size: int = DEFAULT_PAGE_SIZE
    query: str | None = None  # the last search, so `more` can continue it
    listing: list[dict] = field(default_factory=list)  # papers numbered 1..n on screen
    last_viewed: dict | None = None

    def collection(self):
        # Reopening is cheap (the model is cached in memory) and avoids holding a stale handle.
        return store.open_collection(self.db)


def _confirm(question: str) -> bool:
    return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")


def _print_listing(session: Session, start: int) -> None:
    """Print the papers of the current list from index `start` on, numbered from start + 1."""
    width = max(2, len(str(len(session.listing))))
    for number, paper in enumerate(session.listing[start:], start=start + 1):
        print(formatting.result_line(number, paper, width))


def _resolve(session: Session, ref: str) -> str | None:
    """Turn a list number or an arXiv ID into a paper ID. Prints the problem and returns None if it can't."""
    if not ref.isdecimal():
        if not ARXIV_ID.match(ref):
            print(f"{ref!r} is neither a list number nor an arXiv ID like 1706.03762.")
            return None
        return store.paper_id(ref)
    number = int(ref)
    if not session.listing:
        print("There is no numbered list yet. Run 'search' or 'pins' first, or use an arXiv ID.")
    elif not 1 <= number <= len(session.listing):
        print(f"No item {number}: the current list runs from 1 to {len(session.listing)}.")
    else:
        return session.listing[number - 1]["id"]
    return None


def _lookup(session: Session, ref: str) -> dict | None:
    """The full record of the paper `ref` points to, or None (after saying why)."""
    paper_id = _resolve(session, ref)
    if paper_id is None:
        return None
    papers = store.get_papers(session.collection(), [paper_id])
    if not papers:
        print(f"{paper_id} is not in the library. Add it with 'addid {paper_id}'.")
        return None
    return papers[0]


def _target(session: Session, arg: str) -> dict | None:
    """The paper a pin/unpin refers to: the given number or ID, else the paper viewed last."""
    if arg:
        return _lookup(session, arg)
    if session.last_viewed is None:
        print("No paper viewed yet. View one first, or give a number or arXiv ID.")
    return session.last_viewed


def _show_next_page(session: Session) -> None:
    collection = session.collection()
    total = collection.count()
    if total == 0:
        print("The library is empty. Add papers with 'addid' or 'addcat'.")
        return
    shown = len(session.listing)
    # Chroma has no offset, so ask for everything up to the end of the new page and keep the tail.
    results = store.search(collection, session.query, min(shown + session.page_size, total))
    new_papers = [paper for paper, _distance in results[shown:]]
    if not new_papers:
        print("No more results.")
        return
    session.listing += new_papers
    _print_listing(session, shown)


# --- commands: each takes the session and the text typed after the command name -------------


def cmd_search(session: Session, arg: str) -> None:
    if not arg:
        print("Usage: search <what you are looking for, in plain language>")
        return
    session.query, session.listing = arg, []
    _show_next_page(session)
    if session.listing:
        print(f"\n'more' for the next {session.page_size}, 'view <n>' to read one, 'pin <n>' to save one.")


def cmd_more(session: Session, arg: str) -> None:
    if session.query is None:
        print("Nothing to continue. Run 'search' first.")
        return
    _show_next_page(session)


def cmd_limit(session: Session, arg: str) -> None:
    if not arg:
        print(f"Showing {session.page_size} results at a time. Change it with 'limit <n>'.")
    elif arg.isdecimal() and int(arg) >= 1:
        session.page_size = int(arg)
        print(f"Now showing {session.page_size} results at a time.")
    else:
        print("Usage: limit <n>, where n is a whole number of 1 or more.")


def cmd_view(session: Session, arg: str) -> None:
    if not arg:
        print("Usage: view <number from the list, or arXiv ID>")
        return
    paper = _lookup(session, arg)
    if paper:
        session.last_viewed = paper
        print(formatting.paper_details(paper, pinned=paper["id"] in pins.read(session.db)))


def cmd_pin(session: Session, arg: str) -> None:
    paper = _target(session, arg)
    if paper:
        label = formatting.paper_label(paper)
        print(f"Pinned: {label}" if pins.add(session.db, paper["id"]) else f"Already pinned: {label}")


def cmd_unpin(session: Session, arg: str) -> None:
    paper = _target(session, arg)
    if paper:
        label = formatting.paper_label(paper)
        print(f"Unpinned: {label}" if pins.remove(session.db, paper["id"]) else f"Was not pinned: {label}")


def cmd_pins(session: Session, arg: str) -> None:
    papers = store.get_papers(session.collection(), pins.read(session.db))
    if not papers:
        print("Nothing pinned yet. Use 'pin <n>' on a search result, or 'view' a paper and then 'pin'.")
        return
    session.query, session.listing = None, papers  # the numbers now refer to the pins
    _print_listing(session, 0)


def cmd_addid(session: Session, arg: str) -> None:
    if not arg:
        print("Usage: addid <arXiv ID>, e.g. addid 1706.03762")
        return
    paper = library.add_paper(arg, db=session.db)
    print(f"Added. Use 'view {store.paper_id(paper['id'])}' to read it.")


def cmd_addcat(session: Session, arg: str) -> None:
    parts = arg.split()
    if not parts:
        print(formatting.category_list(categories.CATEGORIES, categories.ALIASES))
        print("\nPick one with: addcat <category> [k], e.g. addcat cs.CL 50")
        return
    count_ok = len(parts) < 2 or (parts[1].isdecimal() and int(parts[1]) >= 1)
    if not 1 <= len(parts) <= 2 or not count_ok:
        print("Usage: addcat <category> [k], e.g. addcat cs.CL 50")
        return
    k = int(parts[1]) if len(parts) == 2 else DEFAULT_CATEGORY_LIMIT

    typed = library.normalize_category(parts[0])  # accepts "cs.CL", "cs.cl", "cat:cs.CL"
    category = library.canonical_category(typed)  # follows aliases: stat.TH -> math.ST
    if category != typed:
        print(f"{typed} is an alias of {category}; arXiv files its papers under {category}.")

    stored = library.fetch_category(category, limit=k, db=session.db)
    if stored == 0 and category in library.ingested_categories(session.db):
        # fetch_category skipped it because it was already fetched; let the user override that.
        if _confirm("Fetch it again anyway?"):
            stored = library.fetch_category(category, limit=k, refresh=True, db=session.db)
    elif stored == 0:
        print(f"arXiv returned no papers for {category!r}. Check the category name.")
    if stored:
        print(f"Added {stored} papers from {category}.")


def cmd_help(session: Session, arg: str) -> None:
    print(HELP)


COMMANDS = {
    "search": cmd_search, "s": cmd_search,
    "more": cmd_more, "m": cmd_more,
    "limit": cmd_limit,
    "view": cmd_view, "v": cmd_view,
    "pin": cmd_pin, "p": cmd_pin,
    "unpin": cmd_unpin,
    "pins": cmd_pins,
    "addid": cmd_addid,
    "addcat": cmd_addcat,
    "help": cmd_help, "h": cmd_help, "?": cmd_help,
}
QUIT_WORDS = {"quit", "exit", "q"}


def _ask_yes_no(question: str) -> bool:
    """Ask until the user types yes or no. Ctrl-C and end of input count as no."""
    while True:
        try:
            answer = input(f"{question} (yes/no): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False
        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False
        print("Please type yes or no.")


def _offer_starter_set(session: Session) -> None:
    """For an empty library, offer to download the starter papers (all or nothing)."""
    total = len(STARTER_CATEGORIES) * STARTER_PAPERS_EACH
    print(f"The library is empty. Download a starter set of {total} papers "
          f"(the {STARTER_PAPERS_EACH} newest from each of {' and '.join(STARTER_CATEGORIES)})?")
    print("This fetches from arXiv and embeds them; it usually takes one to two minutes.")
    if not _ask_yes_no("Download them now?"):
        print("Skipped. Add papers later with 'addid' or 'addcat'.")
        return
    try:
        for category in STARTER_CATEGORIES:
            # refresh=True because the library is empty, whatever the fetch log says.
            library.fetch_category(category, limit=STARTER_PAPERS_EACH, refresh=True, db=session.db)
    except requests.RequestException as exc:
        print(f"Could not reach arXiv: {exc}\nContinuing; try 'addcat' again later.")
    except KeyboardInterrupt:
        print("\nCancelled. Continuing with what was downloaded; use 'addcat' to add more.")


def run(db: str = store.DB_PATH) -> None:
    """Run the interface until the user quits."""
    session = Session(db)
    print("Loading the embedding model...")
    count = session.collection().count()
    print(f"\narXiv paper library: {count} papers in {db}\n")
    if count == 0:
        _offer_starter_set(session)
        print()
    print(HELP)

    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):  # Ctrl-D or Ctrl-C at the prompt leaves
            print()
            break
        if not line:
            continue
        name, _, arg = line.partition(" ")
        if name.lower() in QUIT_WORDS:
            break
        handler = COMMANDS.get(name.lower())
        if handler is None:
            print(f"Unknown command {name!r}. Type 'help' to see the commands.")
            continue
        try:
            handler(session, arg.strip())
        except KeyboardInterrupt:  # Ctrl-C during a long fetch cancels it but keeps the session
            print("\nCancelled.")
        except ValueError as exc:  # e.g. an invalid arXiv ID or category name
            print(exc)
        except requests.RequestException as exc:
            print(f"Could not reach arXiv: {exc}")
        except Exception as exc:  # keep the loop alive; the user can retry or quit
            print(f"Something went wrong: {exc}")
