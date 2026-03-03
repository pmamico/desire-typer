# desire statement typer

Desire statement typing in your terminal.

Put your desire statements into files under `~/.statements/` (one statement per non-empty line). For multi-line statements, end the line with `\` to continue on the next line. The app picks one at random and uses it as the typing text.

## Install

**Homebrew** (macOS/Linux):

```
brew tap William-Ger/typer
brew install desire
```

**pip**:

```
pip install typer-cli-tool
```

Then just run:

```
desire
```

## Usage

```
desire              # start practicing
```

## Controls

| Key       | Action              |
|-----------|---------------------|
| `tab`     | restart / home      |
| `ctrl+q`  | quit                |
| `←` `→`  | change time         |
| `↑` `↓`  | change difficulty   |
| `click`   | click time/difficulty|
| `s`       | stats               |

## Features

- Random desire statement from `~/.statements/`
- Repetition counter (how many times you completed the statement)
- Personal stats: best WPM, streaks, per-difficulty averages, sparkline
- User profiles stored locally at `~/.config/typer/`
- Passive update check — shows update command if a new version is available

## Update

Homebrew:

```
brew update && brew upgrade desire
```

pip:

```
pip install --upgrade typer-cli-tool
```

## Zero dependencies

Pure Python. Only uses `curses` (built-in). Works on macOS and Linux out of the box.
