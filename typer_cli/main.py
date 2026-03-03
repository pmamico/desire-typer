import curses
import time
import argparse
import sys
import locale

from typer_cli.sentences import generate
from typer_cli.update import get_update_info
from typer_cli.profile import (
    profile_exists, read_profile, create_profile, append_statement,
    get_theme, set_theme,
)
from typer_cli.themes import THEMES, THEME_NAMES


locale.setlocale(locale.LC_ALL, "")

# ── colors ───────────────────────────────────────────────────────────────────

C_DIM = 1
C_OK = 2
C_ERR = 3
C_CURSOR = 4
C_ACCENT = 5
C_STAT = 6
C_TITLE = 7
C_BORDER = 8
C_GOOD = 9
C_BAD = 10
C_HINT = 11


def init_colors(theme_name="default"):
    curses.start_color()
    curses.use_default_colors()
    theme = THEMES.get(theme_name, THEMES["default"])
    for pair_id, (fg, bg) in theme.items():
        curses.init_pair(pair_id, fg, bg)


# ── draw helpers ─────────────────────────────────────────────────────────────

def cx(w, n):
    return max(0, (w - n) // 2)


def put(win, y, x, text, cp=0, attr=0):
    try:
        win.addstr(y, x, text, curses.color_pair(cp) | attr)
    except curses.error:
        pass


def putc(win, y, w, text, cp=0, attr=0):
    put(win, y, cx(w, len(text)), text, cp, attr)


def hline(win, y, x, n, cp=C_BORDER):
    put(win, y, x, "-" * n, cp)


def wrap(text, width):
    lines, cur = [], ""
    for word in text.split(" "):
        test = f"{cur} {word}" if cur else word
        if len(test) <= width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ── logo ─────────────────────────────────────────────────────────────────────

LOGO = [
    " ▄▄▄▄▄ ▄· ▄▌ ▄▄▄·▄▄▄ .▄▄▄  ",
    " •██  ▐█▪██▌▐█ ▄█▀▄.▀·▀▄ █·",
    "  ▐█.▪▐█▌▐█▪ ██▀·▐▀▀▪▄▐▀▀▄ ",
    "  ▐█▌·▐█▀·.▐█▪·•▐█▄▄▌▐█•█▌",
    "  ▀▀▀  ▀ •  .▀    ▀▀▀ .▀  ▀",
]
LOGO_H = len(LOGO)


def draw_logo(win, y, w):
    for i, line in enumerate(LOGO):
        putc(win, y + i, w, line, C_ACCENT, curses.A_BOLD)


def _count_errors(target, typed):
    n = min(len(typed), len(target))
    return sum(1 for i in range(n) if typed[i] != target[i])


def draw_stats(scr, y, w, reps, errs, today):
    bar = f"{reps} reps   {today} today   {errs} err"
    sx = cx(w, len(bar))
    px = sx
    put(scr, y, px, str(reps), C_ACCENT, curses.A_BOLD)
    px += len(str(reps))
    put(scr, y, px, " reps   ", C_DIM)
    px += 8
    put(scr, y, px, str(today), C_STAT, curses.A_BOLD)
    px += len(str(today))
    put(scr, y, px, " today   ", C_DIM)
    px += 9
    ec = C_BAD if errs > 0 else C_GOOD
    put(scr, y, px, str(errs), ec, curses.A_BOLD)
    px += len(str(errs))
    put(scr, y, px, " err", C_DIM)


# ── text drawing ─────────────────────────────────────────────────────────────

def draw_text(scr, lines, typed, target, sy, sx, aw, sh):
    pos = len(typed)
    maxl = sh - sy - 3
    cline, ci = 0, 0
    for i, line in enumerate(lines):
        if ci + len(line) >= pos:
            cline = i
            break
        ci += len(line) + 1

    vis = min(maxl, 3)
    ss = max(0, min(cline - 1, len(lines) - vis))
    off = sum(len(lines[i]) + 1 for i in range(ss))

    cursor_pos = None
    for li in range(ss, min(ss + vis, len(lines))):
        line = lines[li]
        y = sy + (li - ss)
        if y >= sh - 2:
            break
        for ci2, ch in enumerate(line):
            ri = off + ci2
            x = sx + ci2
            if x >= sx + aw:
                break
            if ri < pos:
                cp = C_OK if ri < len(typed) and typed[ri] == target[ri] else C_ERR
                at = curses.A_UNDERLINE if cp == C_ERR else 0
                put(scr, y, x, ch, cp, at)
            elif ri == pos:
                put(scr, y, x, ch, C_DIM)
                cursor_pos = (y, x)
            else:
                put(scr, y, x, ch, C_DIM)
        off += len(line) + 1
    return cursor_pos


# ── main test loop ───────────────────────────────────────────────────────────

def test(scr, update_info=None, theme_name="default"):
    curses.curs_set(0)
    scr.nodelay(True)
    scr.timeout(50)
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

    target = generate(1, "medium")
    typed = []
    started = False
    stats_y = 0
    hint_y = 0
    user_name = read_profile().get("name", "")
    reps = 0
    today = 0
    today_str = time.strftime("%Y-%m-%d")
    try:
        today = sum(1 for ev in read_profile().get("statements", []) if str(ev.get("ts", ""))[:10] == today_str)
    except Exception:
        today = 0

    while True:
        scr.erase()
        h, w = scr.getmaxyx()
        if h < 10 or w < 40:
            scr.addstr(0, 0, "terminal too small!")
            scr.refresh()
            if scr.getch() == 27:  # esc
                return None, theme_name
            continue

        # ── responsive text width ──
        aw = min(w - 6, 90)
        lines = wrap(target, aw)
        text_vis = min(3, len(lines))

        # ── compute layout — text stays fixed at vertical center ──
        text_y = max(1, (h - text_vis) // 2)

        logo_y = text_y - LOGO_H - 3
        stats_y = text_y - 2
        hint_y = text_y + text_vis + 1

        tx = cx(w, aw)

        # ── draw ──
        if not started:
            draw_logo(scr, logo_y, w)
            cpos = draw_text(scr, lines, typed, target, text_y, tx, aw, h)
            putc(scr, hint_y, w, "start typing...", C_DIM)
            if update_info and update_info["update_available"]:
                notice = f"v{update_info['latest']} available: {update_info['update_cmd']}"
                putc(scr, h - 2, w, notice, C_BAD)
            putc(scr, h - 1, w, "s stats   t theme   tab new statement   esc quit", C_HINT)
            ver = f"v{update_info['version']}" if update_info else ""
            if ver:
                put(scr, h - 1, 1, ver, C_DIM)
                put(scr, h - 1, 1 + len(ver) + 2, theme_name, C_DIM)
            if user_name:
                put(scr, h - 1, w - len(user_name) - 1, user_name, C_DIM)
        else:
            errs = _count_errors(target, typed)
            draw_stats(scr, stats_y, w, reps, errs, today)
            cpos = draw_text(scr, lines, typed, target, text_y, tx, aw, h)
            putc(scr, h - 1, w, "tab new statement   esc quit", C_HINT)

        # show line cursor at current typing position
        if cpos:
            try:
                sys.stdout.write("\033[6 q")  # steady bar cursor
                sys.stdout.flush()
                curses.curs_set(1)
                scr.move(cpos[0], cpos[1])
            except curses.error:
                pass
        else:
            sys.stdout.write("\033[0 q")  # restore default cursor
            sys.stdout.flush()
            curses.curs_set(0)

        scr.refresh()

        # ── input ──
        try:
            k = scr.get_wch()
        except curses.error:
            continue

        if k in (9, "\t"):  # tab
            sys.stdout.write("\033[0 q")
            sys.stdout.flush()
            return "restart", theme_name

        if not started:
            if k in (27, "\x1b"):  # esc
                sys.stdout.write("\033[0 q")
                sys.stdout.flush()
                return None, theme_name
            if k in (ord('s'), 's'):
                return "stats", theme_name
            if k in (ord('t'), 't'):
                idx = THEME_NAMES.index(theme_name)
                theme_name = THEME_NAMES[(idx + 1) % len(THEME_NAMES)]
                init_colors(theme_name)
                set_theme(theme_name)
                continue

        # typing
        if not started and ((isinstance(k, str) and len(k) == 1 and k.isprintable() and k not in ("\x1b",)) or (isinstance(k, int) and 32 <= k <= 126)):
            started = True
            t0 = time.time()

        if k in (curses.KEY_BACKSPACE, 127, 8, "\b", "\x7f"):
            if typed:
                typed.pop()
        elif len(typed) < len(target):
            if isinstance(k, str) and len(k) == 1 and k.isprintable() and k not in ("\x1b",):
                typed.append(k)
            elif isinstance(k, int) and 32 <= k <= 126:
                typed.append(chr(k))

        if len(typed) == len(target) and "".join(typed) == target:
            reps += 1
            append_statement(target)
            if time.strftime("%Y-%m-%d") == today_str:
                today += 1
            typed = []

    sys.stdout.write("\033[0 q")
    sys.stdout.flush()
    return None, theme_name


# ── name prompt ──────────────────────────────────────────────────────────────

def name_prompt(scr, existing=""):
    curses.curs_set(1)
    scr.nodelay(False)
    scr.timeout(-1)

    buf = list(existing)
    MAX_LEN = 20

    while True:
        scr.erase()
        h, w = scr.getmaxyx()
        y = max(1, h // 2 - 3)

        title = "-- change name --" if existing else "-- welcome to desire statement typer --"
        putc(scr, y, w, title, C_TITLE, curses.A_BOLD)
        y += 2
        putc(scr, y, w, "enter your name:", C_DIM)
        y += 2

        name_str = "".join(buf)
        input_display = "> " + name_str
        ix = cx(w, len(input_display) + 1)
        put(scr, y, ix, ">", C_ACCENT, curses.A_BOLD)
        put(scr, y, ix + 2, name_str, C_TITLE)
        cursor_y, cursor_x = y, ix + 2 + len(name_str)

        y += 2
        if existing:
            putc(scr, y, w, "enter to confirm   esc cancel", C_HINT)
        else:
            putc(scr, y, w, "enter to confirm", C_HINT)

        # move cursor after all drawing so addstr doesn't override it
        try:
            scr.move(cursor_y, cursor_x)
        except curses.error:
            pass
        scr.refresh()

        k = scr.getch()
        if k == 27:
            curses.curs_set(0)
            return None
        elif k in (10, 13):
            name = "".join(buf).strip()
            if name:
                curses.curs_set(0)
                return name
        elif k in (curses.KEY_BACKSPACE, 127, 8):
            if buf:
                buf.pop()
        elif 32 <= k <= 126 and len(buf) < MAX_LEN:
            buf.append(chr(k))

    curses.curs_set(0)


# ── stats screen ─────────────────────────────────────────────────────────────

def show_stats(scr):
    from typer_cli.profile import read_profile, set_name, compute_stats

    curses.curs_set(0)
    scr.nodelay(False)
    scr.timeout(-1)

    while True:
        profile = read_profile()
        stats = compute_stats(profile)

        scr.erase()
        h, w = scr.getmaxyx()

        if h < 15 or w < 40:
            try:
                scr.addstr(0, 0, "terminal too small!")
            except curses.error:
                pass
            scr.refresh()
            k = scr.getch()
            if k in (27, ord('q'), ord('Q')):
                return
            continue

        dw = min(50, w - 10)
        lx = cx(w, dw)
        rx = lx + dw // 2

        content_h = 22
        y = max(1, (h - content_h) // 2)

        # title
        putc(scr, y, w, "-- stats --", C_TITLE, curses.A_BOLD)
        y += 2

        # name
        putc(scr, y, w, stats["name"] or "(no name)", C_ACCENT, curses.A_BOLD)
        y += 1
        putc(scr, y, w, f"member since {stats['member_since']}", C_DIM)
        y += 2

        # divider
        hline(scr, y, cx(w, dw), dw)
        y += 2

        if stats["tests_completed"] == 0 and stats.get("statements_completed", 0) == 0:
            putc(scr, y, w, "no stats yet -- start typing!", C_DIM)
        else:
            # tests + total time
            put(scr, y, lx, "tests  ", C_DIM)
            put(scr, y, lx + 7, str(stats["tests_completed"]), C_STAT, curses.A_BOLD)
            put(scr, y, rx, "total time  ", C_DIM)
            put(scr, y, rx + 12, stats["total_time_fmt"], C_STAT, curses.A_BOLD)
            y += 1

            put(scr, y, lx, "statements ", C_DIM)
            put(scr, y, lx + 11, str(stats.get("statements_completed", 0)), C_ACCENT, curses.A_BOLD)
            put(scr, y, rx, "today  ", C_DIM)
            put(scr, y, rx + 7, str(stats.get("statements_today", 0)), C_STAT, curses.A_BOLD)
            y += 1

            put(scr, y, lx, "stmt streak ", C_DIM)
            put(scr, y, lx + 11, f"{stats.get('statements_streak', 0)} day{'s' if stats.get('statements_streak', 0) != 1 else ''}", C_ACCENT if stats.get('statements_streak', 0) > 0 else C_DIM, curses.A_BOLD)
            y += 2

            # best wpm
            put(scr, y, lx, "best   ", C_DIM)
            if stats["best_wpm"] is not None:
                put(scr, y, lx + 7, f"{stats['best_wpm']:.0f} wpm", C_ACCENT, curses.A_BOLD)
                ctx = f"({stats['best_wpm_diff']}, {stats['best_wpm_date']})"
                put(scr, y, rx, ctx, C_DIM)
            y += 1

            # avg wpm (last 10)
            put(scr, y, lx, "avg    ", C_DIM)
            if stats["avg_wpm_recent"] is not None:
                put(scr, y, lx + 7, f"{stats['avg_wpm_recent']:.0f} wpm", C_STAT, curses.A_BOLD)
                put(scr, y, rx, "(last 10 tests)", C_DIM)
            y += 1

            # avg accuracy
            put(scr, y, lx, "acc    ", C_DIM)
            if stats["avg_acc"] is not None:
                acp = C_GOOD if stats["avg_acc"] >= 90 else C_BAD
                put(scr, y, lx + 7, f"{stats['avg_acc']:.1f}%", acp, curses.A_BOLD)
            y += 1

            # streak
            put(scr, y, lx, "streak ", C_DIM)
            sv = stats["streak"]
            scp = C_ACCENT if sv > 0 else C_DIM
            put(scr, y, lx + 7, f"{sv} day{'s' if sv != 1 else ''}", scp, curses.A_BOLD)
            y += 2

            # divider
            hline(scr, y, cx(w, dw), dw)
            y += 2

            # sparkline
            if stats["sparkline"]:
                label = "last 10  "
                sl = stats["sparkline"]
                sx = cx(w, len(label) + len(sl))
                put(scr, y, sx, label, C_DIM)
                put(scr, y, sx + len(label), sl, C_ACCENT, curses.A_BOLD)
                y += 2

                # divider
                hline(scr, y, cx(w, dw), dw)
                y += 2

            # per-difficulty breakdown
            diff_colors = {"easy": C_GOOD, "medium": C_STAT, "hard": C_BAD}
            for diff_name in ("easy", "medium", "hard"):
                diff_avg = stats["per_diff"].get(diff_name)
                put(scr, y, lx, f"{diff_name:8s}", C_DIM)
                if diff_avg is not None:
                    put(scr, y, lx + 8, f"{diff_avg:.0f} wpm", diff_colors[diff_name], curses.A_BOLD)
                else:
                    put(scr, y, lx + 8, "--", C_DIM)
                y += 1

        # bottom hint
        putc(scr, h - 1, w, "n change name   esc back", C_HINT)
        scr.refresh()

        k = scr.getch()
        if k in (27, ord('q'), ord('Q')):
            return
        elif k == ord('n'):
            new_name = name_prompt(scr, profile.get("name", ""))
            if new_name is not None:
                set_name(new_name)


# ── main ─────────────────────────────────────────────────────────────────────

def run(scr, args):
    theme_name = get_theme()
    if theme_name not in THEMES:
        theme_name = "default"
    init_colors(theme_name)
    curses.curs_set(0)

    # first-launch: prompt for name
    if not profile_exists():
        name = name_prompt(scr)
        if name:
            create_profile(name)
        else:
            create_profile("")

    update_info = get_update_info()

    while True:
        result, theme_name = test(scr, update_info, theme_name)

        if result is None:
            return
        if result == "restart":
            continue
        if result == "stats":
            show_stats(scr)
            continue


def entry():
    parser = argparse.ArgumentParser(
        prog="desire",
        description="desire statement typer — desire statement typing in your terminal",
    )
    parser.add_argument("-t", "--time", type=int, metavar="SEC",
                        help="ignored (no time limit)")
    parser.add_argument("-d", "--diff", type=str, metavar="LEVEL",
                        help="ignored")
    args = parser.parse_args()

    try:
        curses.wrapper(lambda scr: run(scr, args))
    except KeyboardInterrupt:
        pass
