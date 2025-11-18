# Brute_dict: Bruteforce dictionary generator

A small Python tool to generate bruteforce password lists from a person's first name, last name, nicknames, surname variants, numbers and symbols. Output is human-readable, numbered, and printed to the console.

Ethical note: Intended for legitimate uses only (editorial exercises, usability testing, word gathering for writing). Do not use for unauthorized access or illegal activities.

## Highlights (new & notable)
- Two operation modes chosen at start:
  - Biographical infos — builds passwords from First name, Last name, Nicknames, Surname variants, Numbers and Symbols.
  - Keywords-based mix — "minestrone" mode that permutes user keywords (user sets max words per password; default = 3).
- Output file: `output.txt` in the script directory. Plain lines, no numbering.
- UI / UX:
  - Hacker-style prompts and markers ([+] for input modules, [*] for completed save).
  - ASCII banner and colored feedback (when terminal supports ANSI).
  - Progress bar while writing `output.txt`.
  - Emphasized final box showing the total combinations saved and the path to `output.txt`.
- Capitalization modes:
  - `none` — leave tokens as entered.
  - `tokens` — capitalize the first letter of tokens (default scope = both names and surnames).
  - `firstchar` — capitalize the first character of the final password if it is a letter.
- Symbols control:
  - User can set "Max symbols per separator" (0..N).
  - User can choose whether symbols may repeat in sequences (allow repeat yes/no).
  - Symbol sequences between tokens are generated according to those settings.
- Generation constraints:
  - Password length filtered between 6 and 25 characters (configurable in code).
  - Uses 1..3 token parts for editorial mode; mix-mode uses permutations up to user-set max words.
  - Internal shuffle before saving.
  - Pre-check estimate with confirmation for very large result sets.

## Usage
Requirements
- Python 3.8+ (Windows)
- No external libraries

Run:
```powershell
git clone https://Lo_zambet/brute_dict
cd brute_dict
python main.py
```
The flow is a multiple choice menu, very interactive and intuitive to use

after that you can run

```powershell
start outuput.txt
```
to open output result, or:

```powershell
cat outuput.txt
```
to just read it into the powershell

Flow (interactive):
1. Choose mode:
   - 1) Biographical infos
   - 2) Keywords-based mix
2. Follow prompts (hacker-style with green [+] markers). Example prompts:
   - First name
   - Last name
   - Nicknames (comma-separated)
   - Surname variants (comma-separated)
   - Capitalization? (none/tokens/firstchar) — tokens defaults to both
   - Numbers (comma-separated)
   - Symbols (comma-separated)
   - Max symbols per separator (0 = none)
   - Allow symbols to repeat? (y/n)
   - For mix mode: Keywords (comma-separated) and Max words per password (default 3)
3. Script estimates combinations and asks confirmation if very large.
4. Generation runs; a progress bar displays while saving to `output.txt`.
5. On completion you get a final highlighted box with the total saved and the full path.

Output:

- `output.txt` — one password per line, plain text, no numbering.
