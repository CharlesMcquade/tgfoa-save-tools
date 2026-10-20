#!/usr/bin/env python3
"""Tainted Grail: The Fall of Avalon save reader (stdlib only).

Usage:
  tgfoa_save.py quests <save.zip>                     # quest-level states
  tgfoa_save.py objectives <save.zip> [QuestName ...] # per-objective states
  tgfoa_save.py diff <a.zip> <b.zip>                  # quest-state diff between two saves
  tgfoa_save.py pull [--host H] [--path P] [--dest D] # copy saves (local or over ssh)
  tgfoa_save.py where                                 # print default save dir(s)

`quests`/`objectives` with no file use the newest .zip in the cache dir
(default ./saves, override with --dest or TGFOA_CACHE).

pull:
  * no --host  -> copies from the local save dir (Windows default, or --path)
  * --host H   -> `ssh H tar` stream (remote needs tar); needs --path (or TGFOA_SAVE_PATH)
                  in the remote shell's path syntax, e.g. for git-bash on Windows:
                  "/c/Users/<you>/AppData/LocalLow/Questline/Fall of Avalon/<steamid>/Saved"
Env vars: TGFOA_HOST, TGFOA_SAVE_PATH, TGFOA_CACHE.

Format notes: see SKILL.md. Verified against patch 1.30 (mono branch).
"""
import glob, json, os, re, shutil, subprocess, sys, zipfile, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
TPL_JSON = os.path.join(HERE, 'quest_templates.json')


def opt(argv, name, env, default=None):
    if name in argv:
        i = argv.index(name)
        val = argv[i + 1]
        del argv[i:i + 2]
        return val
    return os.environ.get(env, default)


def default_save_dirs():
    """Windows default: %USERPROFILE%/AppData/LocalLow/Questline/Fall of Avalon/<steamid>/Saved"""
    base = os.path.join(os.path.expanduser('~'), 'AppData', 'LocalLow')
    hits = glob.glob(os.path.join(base, 'Questline', 'Fall of Avalon', '*', 'Saved'))
    return sorted(hits)


def lebv(buf, i):
    shift = val = 0
    while True:
        b = buf[i]; i += 1
        val |= (b & 0x7f) << shift
        if not (b & 0x80):
            return val, i
        shift += 7


def load_templates():
    return {q['guid']: q['go_name'] for q in json.load(open(TPL_JSON)) if q['guid']}


def gameplay(zpath):
    with zipfile.ZipFile(zpath) as zf:
        return zlib.decompressobj(-15).decompress(zf.read('Gameplay.data'))


def quest_states(g, g2q):
    out = {}
    for m in re.finditer(rb'\x7c\x7d\x7c\x87\x00([0-9a-f]{32})\x00', g):
        guid = m.group(1).decode()
        name = g2q.get(guid)
        if not name:
            continue
        fwd = g[m.end():m.end() + 8]
        if fwd and fwd[0] == 0x7c:
            tag, j = lebv(fwd, 1)
            if tag in (0x56, 0x57):
                val, _ = lebv(fwd, j)
                out[name] = val
    return out


def objective_states(g, g2q):
    pat = re.compile(rb'(?:[0-9a-f]\x00){32}/\x00(?:[0-9a-f-]\x00){36}\x00\x00')
    per = {}
    for m in pat.finditer(g):
        seg = m.group()
        qg = seg[:64].replace(b'\x00', b'').decode()
        og = seg[66:66 + 72].replace(b'\x00', b'').decode()
        back = g[max(0, m.start() - 1500):m.start()]
        hits = re.findall(rb's\x00t\x00a\x00t\x00e\x00\x00\x00\x06(.)', back, re.S)
        per.setdefault(g2q.get(qg, 'Q?' + qg[:8]), []).append((og, hits[-1][0] if hits else None))
    return per


def newest(cache):
    cands = glob.glob(os.path.join(cache, '*.zip'))
    if not cands:
        sys.exit(f'no .zip saves in {cache} - pass a save path or run `pull` first')
    return max(cands, key=os.path.getmtime)


def cmd_pull(host, path, dest):
    os.makedirs(dest, exist_ok=True)
    if host:
        if not path:
            sys.exit('--path (or TGFOA_SAVE_PATH) is required with --host')
        # tar over ssh: one round-trip, and it preserves mtimes so "newest save" stays correct
        # (per-file `ssh cat` would stamp every file with the download time).
        tar = subprocess.Popen(['ssh', host, f'cd "{path}" && tar -cf - *.zip'], stdout=subprocess.PIPE)
        subprocess.run(['tar', '-xf', '-', '-C', dest], stdin=tar.stdout, check=True)
        if tar.wait() != 0:
            sys.exit('ssh/tar pull failed')
    else:
        dirs = [path] if path else default_save_dirs()
        if not dirs:
            sys.exit('no local save dir found - pass --path')
        for d in dirs:
            for src in glob.glob(os.path.join(d, '*.zip')):
                # always overwrite: the game reuses slot names (AutoSave_N rotates)
                shutil.copy2(src, os.path.join(dest, os.path.basename(src)))
    for f in glob.glob(os.path.join(dest, '*.zip')):
        zipfile.ZipFile(f).testzip()   # raises on a corrupt/truncated transfer
    print('\n'.join(sorted((os.path.basename(f) for f in glob.glob(os.path.join(dest, '*.zip'))),
                           key=lambda f: os.path.getmtime(os.path.join(dest, f)))))


def cmd_quests(z):
    st = quest_states(gameplay(z), load_templates())
    print('ACTIVE (in journal):')
    for n in sorted(n for n, v in st.items() if v == 1):
        print('  ', n)
    print('OTHER (completed or dormant):')
    for n in sorted(n for n, v in st.items() if v != 1):
        print('  ', n)


def cmd_objectives(z, want):
    per = objective_states(gameplay(z), load_templates())
    for q in sorted(per):
        if want and not any(w.lower() in q.lower() for w in want):
            continue
        print('==', q)
        for og, v in per[q]:
            print(f'   {og} state={v}')


def cmd_diff(a, b):
    g2q = load_templates()
    sa, sb = quest_states(gameplay(a), g2q), quest_states(gameplay(b), g2q)
    for n in sorted(set(sa) | set(sb)):
        if sa.get(n) != sb.get(n):
            print(f'{n:<44} {sa.get(n)} -> {sb.get(n)}')


def main(argv):
    host = opt(argv, '--host', 'TGFOA_HOST')
    path = opt(argv, '--path', 'TGFOA_SAVE_PATH')
    dest = opt(argv, '--dest', 'TGFOA_CACHE', 'saves')
    cmd = argv[0] if argv else ''
    if cmd == 'pull':
        cmd_pull(host, path, dest)
    elif cmd == 'where':
        print('\n'.join(default_save_dirs()) or 'no default save dir found on this machine')
    elif cmd == 'quests':
        cmd_quests(argv[1] if len(argv) > 1 else newest(dest))
    elif cmd == 'objectives':
        cmd_objectives(argv[1] if len(argv) > 1 else newest(dest), argv[2:])
    elif cmd == 'diff' and len(argv) == 3:
        cmd_diff(argv[1], argv[2])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv[1:])
