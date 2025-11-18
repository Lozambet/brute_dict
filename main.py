#!/usr/bin/env python3
"""
Editorial Password Generator

Generates "editorial" password combinations using first name, last name,
nicknames, surname variants, numbers and symbols.

Implemented:
- interactive input for required fields
- generation of combinations with 1..3 tokens, optional separators,
  number placement (prepend/append/insert) and capitalization modes
- length filter between 6 and 25 characters
- internal shuffle of results
- print all results numbered to console

The script is modular and ready for extensions (styles, extra patterns).
"""

from __future__ import annotations

import itertools
import os
import random
import sys
from typing import Iterable, List, Optional, Sequence, Set, Tuple

# Hacker-style UI helpers (colors only if stdout is a TTY)
def _make_colors():
    if sys.stdout.isatty():
        return {
            "C": "\033[96m",   # cyan
            "G": "\033[92m",   # green
            "Y": "\033[93m",   # yellow
            "R": "\033[91m",   # red
            "B": "\033[95m",   # magenta / blue-ish
            "D": "\033[2m",    # dim
            "RESET": "\033[0m",
        }
    return {k: "" for k in ("C", "G", "Y", "R", "B", "D", "RESET")}

COL = _make_colors()


def ask(prompt: str, default: Optional[str] = None) -> str:
    """Stylized input prompt (hacker-ish) with green [+] at the start of the line."""
    plus = f"{COL['G']}[+]{COL['RESET']}"
    # place [+] at the very start of the line before the prompt text
    if default:
        display = f"{plus} {COL['C']}{prompt}{COL['RESET']} [{default}]: "
    else:
        display = f"{plus} {COL['C']}{prompt}{COL['RESET']}: "
    try:
        res = input(display)
    except KeyboardInterrupt:
        print("\n" + COL["R"] + "[!] Interrupted." + COL["RESET"])
        sys.exit(1)
    if not res and default is not None:
        return default
    return res.strip()


def split_list(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


# build symbol sequences (e.g. "_", "__", "-.", etc.) up to max_count
def build_symbol_variants(symbols: Sequence[str], max_count: int, allow_repeat: bool) -> List[str]:
    out: Set[str] = set()
    if not symbols or max_count <= 0:
        return []
    if allow_repeat:
        # allow repetition: cartesian product for lengths 1..max_count
        for r in range(1, max_count + 1):
            for prod in itertools.product(symbols, repeat=r):
                out.add("".join(prod))
    else:
        # no repetition: use permutations without replacement (r cannot exceed len(symbols))
        for r in range(1, min(max_count, len(symbols)) + 1):
            for perm in itertools.permutations(symbols, r):
                out.add("".join(perm))
    return sorted(out)


class Token:
    def __init__(self, text: str, kind: str):
        self.text = text
        self.kind = kind  # 'name', 'surname', 'nickname', 'other'

    def variants(self, use_caps_for: Set[str]) -> List[str]:
        """Return variants of this token according to capitalization rules.

        If token.kind is in use_caps_for, include capitalized version.
        Always include original form and lowercased form to preserve editorial feel.
        """
        v = set()
        base = self.text
        if base:
            v.add(base)
            v.add(base.lower())
        if self.kind in use_caps_for:
            v.add(base.capitalize())
        return sorted(v)


def build_groups(
    first_name: str,
    last_name: str,
    nicknames: Sequence[str],
    surname_variants: Sequence[str],
) -> List[List[Token]]:
    """Build groups of alternative tokens.

    Name-group includes `first_name` and all `nicknames` (alternatives).
    Surname-group includes `last_name` and all `surname_variants` (alternatives).
    Each group provides at most one token per password.
    """
    groups: List[List[Token]] = []
    name_group: List[Token] = []
    surname_group: List[Token] = []
    if first_name:
        name_group.append(Token(first_name, "name"))
    for s in nicknames:
        name_group.append(Token(s, "name"))
    if last_name:
        surname_group.append(Token(last_name, "surname"))
    for v in surname_variants:
        surname_group.append(Token(v, "surname"))
    if name_group:
        groups.append(name_group)
    if surname_group:
        groups.append(surname_group)
    return groups


def generate_editorial_passwords(
    groups: List[List[Token]],
    numbers: Sequence[str],
    symbols: Sequence[str],
    caps_mode: str,
    caps_scope: str,
    min_len: int = 6,
    max_len: int = 25,
    max_parts: int = 3,
    max_symbols_per_sep: int = 1,
    allow_repeat_symbols: bool = True,
) -> List[str]:
    """Generate editorial-style combinations.

    Strategy:
    - Use 1..max_parts distinct tokens (order matters)
    - Between tokens, either join directly or insert a single symbol-sequence from symbols_variants
    - Optionally place a single number at any position (prepend, append, between tokens)
    - Respect capitalization choices (names/surnames/both/none)
    - Filter by length

    Note: symbol sequences between tokens are built according to max_symbols_per_sep
    and allow_repeat_symbols.
    """
    # caps_mode: 'none' | 'tokens' | 'firstchar'
    use_caps_for: Set[str] = set()
    if caps_mode == "tokens":
        if caps_scope == "names":
            use_caps_for.add("name")
        elif caps_scope == "surnames":
            use_caps_for.add("surname")
        elif caps_scope == "both":
            use_caps_for.update({"name", "surname"})

    # For each group, build the list of string variants (flatten tokens' variants)
    group_variant_lists: List[List[str]] = []
    for group in groups:
        variants: Set[str] = set()
        for t in group:
            # Token.variants will include base, lower and capitalize when applicable
            for v in t.variants(use_caps_for):
                variants.add(v)
        group_variant_lists.append(sorted(variants))

    # build symbol variants according to user choice
    symbol_variants = build_symbol_variants(list(symbols), max_symbols_per_sep, allow_repeat_symbols)
    symbols_choices = [""] + symbol_variants
    number_choices = [""] + list(numbers)

    results: Set[str] = set()

    group_indices = list(range(len(groups)))

    for parts in range(1, min(max_parts, len(groups)) + 1):
        # choose which groups to include (order matters -> permutations)
        for grp_perm in itertools.permutations(group_indices, parts):
            variant_lists = [group_variant_lists[i] for i in grp_perm]

            sep_positions = parts - 1
            sep_choices_iter = itertools.product(symbols_choices, repeat=max(0, sep_positions))

            for sep_choices in sep_choices_iter:
                for combo in itertools.product(*variant_lists):
                    if sep_positions == 0:
                        core = combo[0]
                    else:
                        pieces = []
                        for i, piece in enumerate(combo):
                            pieces.append(piece)
                            if i < sep_positions:
                                pieces.append(sep_choices[i])
                        core = "".join(pieces)

                    for num in number_choices:
                        def add_candidate(cand_str: str) -> None:
                            if min_len <= len(cand_str) <= max_len:
                                results.add(cand_str)

                        if not num:
                            candidate = core
                            add_candidate(candidate)
                            # if mode is 'firstchar', also add capitalized-first variant when applicable
                            if caps_mode == "firstchar" and candidate and candidate[0].isalpha():
                                candidate_fc = candidate[0].upper() + candidate[1:]
                                add_candidate(candidate_fc)
                        else:
                            cand1 = num + core
                            add_candidate(cand1)
                            if caps_mode == "firstchar" and cand1 and cand1[0].isalpha():
                                add_candidate(cand1[0].upper() + cand1[1:])
                            cand2 = core + num
                            add_candidate(cand2)
                            if caps_mode == "firstchar" and cand2 and cand2[0].isalpha():
                                add_candidate(cand2[0].upper() + cand2[1:])
                            if parts > 1 and sep_positions > 0:
                                # reconstruct pieces to insert number between token boundaries
                                pieces = []
                                for i, piece in enumerate(combo):
                                    pieces.append(piece)
                                    if i < sep_positions:
                                        pieces.append(sep_choices[i])
                                token_piece_indices = [i * 2 for i in range(parts)]
                                for b in range(1, parts):
                                    insert_pos = token_piece_indices[b]
                                    new_pieces = pieces[:insert_pos] + [num] + pieces[insert_pos:]
                                    cand = "".join(new_pieces)
                                    add_candidate(cand)
                                    if caps_mode == "firstchar" and cand and cand[0].isalpha():
                                        add_candidate(cand[0].upper() + cand[1:])

    return sorted(results)


def save_passwords(path: str, passwords: Sequence[str]) -> None:
    """Save passwords as plain lines (no numbering)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for p in passwords:
            f.write(f"{p}\n")


def write_with_progress(path: str, passwords: Sequence[str], col: dict) -> None:
    """Write passwords to file showing a simple textual progress bar with hacker markers."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    total = len(passwords)
    bar_width = 40
    try:
        with open(path, "w", encoding="utf-8") as f:
            for i, p in enumerate(passwords, start=1):
                f.write(f"{p}\n")
                # progress display (updates in-place) with green [+] marker at line start
                filled = int(bar_width * i / total) if total else bar_width
                bar = "[" + "#" * filled + "-" * (bar_width - filled) + "]"
                percent = int(100 * i / total) if total else 100
                print(f"\r{col['G']}[+]{col['RESET']} {col['B']}Saving{col['RESET']} {bar} {percent:3d}% ({i:,}/{total:,})", end="", flush=True)
        # finish line with green [*] at line start
        print(f"\r{col['G']}[*]{col['RESET']} Save complete.{' ' * (bar_width + 30)}")
    except Exception as e:
        print(f"\n{col['R']}[!] Error while saving: {e}{col['RESET']}")
        raise


def confirm_if_large(count_estimate: int) -> bool:
    threshold = 2_000_000
    if count_estimate > threshold:
        print(f"{COL['R']}[!!] Estimated combinations: {count_estimate:,}. This may take a long time and use a lot of RAM.{COL['RESET']}")
        ans = ask("[?] Continue anyway? (y/n)", "n").lower()
        return ans.startswith("y")
    # small, show green [+] at start
    print(f"{COL['G']}[+]{COL['RESET']} Estimated combinations: {count_estimate:,}")
    return True


def generate_mix_passwords(
    keywords: Sequence[str],
    max_words: int,
    min_len: int = 6,
    max_len: int = 25,
) -> List[str]:
    """Generate 'minestrone' passwords by mixing given keywords.

    - Uses permutations (words not repeated in a single password).
    - Builds strings by concatenating 1..max_words words.
    - Filters by length.
    """
    kws = [k for k in keywords if k]
    results: Set[str] = set()
    if not kws or max_words <= 0:
        return []

    max_r = min(max_words, len(kws))
    for r in range(1, max_r + 1):
        for perm in itertools.permutations(kws, r):
            s = "".join(perm)
            if min_len <= len(s) <= max_len:
                results.add(s)
    return sorted(results)


def main() -> None:
    # ASCII banner — user-provided
    banner = f"""{COL['G']}
_                _            _ _      _   
| |              | |          | (_)    | |  
| |__  _ __ _   _| |_ ___   __| |_  ___| |_ 
| '_ \\| '__| | | | __/ _ \\ / _` | |/ __| __|
| |_) | |  | |_| | ||  __/| (_| | | (__| |_ 
|_.__/|_|   \\__,_|\\__\\___| \\__,_|_|\\___|\\__|
          
Tool created by @Lo_zambet
{COL['RESET']}"""
    print(banner)
    print(f"{COL['D']}Initializing module...{COL['RESET']}\n")

    # MODE MENU: choose before any data entry
    # [+] in green, title in blue, option text in green, numbers kept in yellow
    print(f"{COL['G']}[+]{COL['RESET']} {COL['B']}Select mode:{COL['RESET']}")
    print(f"  {COL['Y']}1{COL['RESET']}) {COL['G']}Biographical infos{COL['RESET']}")
    print(f"  {COL['Y']}2{COL['RESET']}) {COL['G']}Keywords-based mix{COL['RESET']}\n")
    m_choice = ask("Choose mode (1/2)", "1").strip().lower()
    if m_choice in ("2", "mix", "m"):
        mode = "mix"
    else:
        mode = "editorial"

    # ----- MIX MODE -----
    if mode == "mix":
        keywords_raw = ask("Keywords (comma-separated)")
        # compact prompt as requested: "[+] Max words per password [3]:"
        max_words_raw = ask("Max words per password", "3").strip()
        try:
            max_words = max(1, int(max_words_raw))
        except Exception:
            max_words = 3

        keywords = split_list(keywords_raw)
        if not keywords:
            print(COL["R"] + "[!] No keywords provided. Exiting." + COL["RESET"])
            return

        # estimate permutations
        n = len(keywords)
        estimate = 0
        for r in range(1, min(max_words, n) + 1):
            perm_count = 1
            for i in range(n, n - r, -1):
                perm_count *= i
            estimate += perm_count

        if not confirm_if_large(estimate):
            print(COL["R"] + "Operation cancelled by user." + COL["RESET"])
            return

        print(f"{COL['B']}Generating mix mode — this may take a while.{COL['RESET']}")
        passwords = generate_mix_passwords(keywords, max_words, min_len=6, max_len=25)

        if not passwords:
            print(COL["R"] + "No combinations found matching the length criteria." + COL["RESET"])
            return

        random.shuffle(passwords)

        output_path = os.path.join(os.path.dirname(__file__), "output.txt")
        print()  # spacer
        write_with_progress(output_path, passwords, COL)

        # emphasized final box
        print(f"\n{COL['G']}+{'=' * 60}{COL['RESET']}")
        print(f"{COL['G']}[*]{COL['RESET']} {COL['B']}TOTAL COMBINATIONS{COL['RESET']}: {COL['Y']}{len(passwords):,}{COL['RESET']}")
        print(f"{COL['G']}[*]{COL['RESET']} Saved to: {COL['C']}{output_path}{COL['RESET']}")
        print(f"{COL['G']}+{'=' * 60}{COL['RESET']}\n")
        return

    # ----- EDITORIAL MODE (existing flow) -----
    first_name = ask("First name")
    last_name = ask("Last name")
    nicknames_raw = ask("Nicknames (comma-separated)", "")
    surname_variants_raw = ask("Surname variants (comma-separated)", "")

    # Capitalization mode:
    # - none: no modification
    # - tokens: capitalize first-letter of tokens according to scope
    # - firstchar: capitalize first character of the final password if it is a letter
    caps_mode = ask("Capitalization? (none/tokens/firstchar)", "none").strip().lower()
    caps_scope = "none"
    if caps_mode in ("tokens", "token", "t"):
        caps_mode = "tokens"
        # default to 'both' as requested
        caps_choice = ask("Apply to? (names/surnames/both)", "both").strip().lower()
        if caps_choice in ("names", "name", "n"):
            caps_scope = "names"
        elif caps_choice in ("surnames", "surname", "s"):
            caps_scope = "surnames"
        elif caps_choice in ("both", "b"):
            caps_scope = "both"
        else:
            caps_scope = "names"
    elif caps_mode in ("firstchar", "first", "f"):
        caps_mode = "firstchar"
    else:
        caps_mode = "none"

    numbers_raw = ask("Numbers to include (comma-separated)", "")
    symbols_raw = ask("Symbols to include (comma-separated)", "")

    nicknames = split_list(nicknames_raw)
    surname_variants = split_list(surname_variants_raw)
    numbers = split_list(numbers_raw)
    symbols = split_list(symbols_raw)

    groups = build_groups(first_name, last_name, nicknames, surname_variants)

    if not groups:
        print(COL["R"] + "No valid tokens provided. Exiting." + COL["RESET"])
        return

    # Quick conservative estimate of combinations (very rough)
    estimate = 0
    n_groups = len(groups)
    n_numbers = max(1, len(numbers))
    n_symbols = max(1, len(symbols))
    avg_variants = 2
    for parts in range(1, min(3, n_groups) + 1):
        perms = 1
        for i in range(parts):
            perms *= (n_groups - i)
        sep_choices = n_symbols ** max(0, parts - 1)
        estimate += perms * (avg_variants ** parts) * sep_choices * n_numbers

    # Stylized warning if large
    if estimate > 2_000_000:
        print(f"{COL['R']}[!!] Estimated combinations: {estimate:,} — heavy operation{COL['RESET']}")
    else:
        print(f"{COL['Y']}Estimated combinations: {estimate:,}{COL['RESET']}")

    if not confirm_if_large(estimate):
        print(COL["R"] + "Operation cancelled by user." + COL["RESET"])
        return

    print(f"\n{COL['B']}Generating — do not close this terminal.{COL['RESET']}")
    passwords = generate_editorial_passwords(
        groups=groups,
        numbers=numbers,
        symbols=symbols,
        caps_mode=caps_mode,
        caps_scope=caps_scope,
        min_len=6,
        max_len=25,
        max_parts=3,
    )

    if not passwords:
        print(COL["R"] + "No combinations found matching the length criteria." + COL["RESET"])
        return

    random.shuffle(passwords)

    # Save all passwords to output.txt in the script directory with a progress bar
    output_path = os.path.join(os.path.dirname(__file__), "output.txt")
    print()  # spacer
    write_with_progress(output_path, passwords, COL)

    # emphasized final box — clearer UX
    print(f"\n{COL['G']}+{'=' * 60}{COL['RESET']}")
    print(f"{COL['G']}[*]{COL['RESET']} {COL['B']}TOTAL COMBINATIONS{COL['RESET']}: {COL['Y']}{len(passwords):,}{COL['RESET']}")
    print(f"{COL['G']}[*]{COL['RESET']} Saved to: {COL['C']}{output_path}{COL['RESET']}")
    print(f"{COL['G']}+{'=' * 60}{COL['RESET']}\n")


if __name__ == "__main__":
    main()

