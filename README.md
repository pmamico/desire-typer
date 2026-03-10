# Desire Statement Typer

Desire statement typing in your terminal.

You maintain a folder of desire statements under `~/.statements/`. The app picks one at random and you type it out.

## Inspiration

This project is inspired by the “Desire Statement” mental training tool from Kenneth Baum’s *The Mental Edge* (1999): a short, specific statement of what you truly want, revisited often to keep motivation and focus high. Reference: [The Mental Edge (Heroic summary)](https://legacy.heroic.us/pn/the-mental-edge-kenneth-baum#hows-your-desire)

## Install

[https://pypi.org/project/desire-typer/](https://pypi.org/project/desire-typer/)  

```bash
pipx install desire-typer
```

### local

```bash
python3 -m pip install -e .
```

## Run

```bash
desire
```

Or, if you prefer module execution:

```bash
python3 -m desire
```

## Statements Folder

- Location: `~/.statements/`
- One statement per non-empty line
- Multi-line statements: end the line with a trailing `\` to continue on the next line
- Lines starting with `#` are ignored

Example `~/.statements/my_statements.txt`:

```text
# one-liners
I treat my time with respect.
I finish what I start.

# multi-line (note the trailing backslash)
I am the kind of person who \
does the work even when I do not feel like it.
```

## Controls

|   Key | Action        |
|------:|---------------|
| `tab` | new statement |
| `esc` | quit          |
|   `s` | stats         |
|   `t` | cycle theme   |

## Data Storage

- Statements: `~/.statements/`
- Local profile/stats: `~/.config/typer/profile.json` (legacy path name)

## Platform Notes

- macOS/Linux: uses stdlib `curses`
- Windows: requires `windows-curses` (declared as a conditional dependency in `pyproject.toml`)
