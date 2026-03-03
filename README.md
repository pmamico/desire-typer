# desire statement typer

Desire statement typing in your terminal.

You maintain a folder of desire statements under `~/.statements/`. The app picks one at random and you type it out.

## Install

PyPI package name is `typer-cli-tool` (it installs the `desire` CLI):

```bash
python -m pip install --upgrade typer-cli-tool
```

`pipx` also works well for CLI tools:

```bash
pipx install typer-cli-tool
```

Homebrew is not supported yet.

## Run

```bash
desire
```

Or, if you prefer module execution:

```bash
python -m desire
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

| Key   | Action |
|------:|--------|
| `tab` | new statement |
| `esc` | quit |
| `s`   | stats |
| `t`   | cycle theme |

## Data Storage

- Statements: `~/.statements/`
- Local profile/stats: `~/.config/typer/profile.json` (legacy path name)

## Update

```bash
python -m pip install --upgrade typer-cli-tool
```

## Platform Notes

- macOS/Linux: uses stdlib `curses`
- Windows: requires `windows-curses` (declared as a conditional dependency in `pyproject.toml`)
