#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把订阅里的同仓相对路径（./xxx）换成你自己 GitHub 仓库的绝对地址。
支持一次生成多条国内镜像线路，哪条通就用哪条。

放在仓库根目录跑，脚本会自己读 git remote 拿到用户名/仓库名。

常用命令
--------
  python3 set-repo.py                       # 只生成官方 raw 直连版
  python3 set-repo.py --mirror              # 生成主力镜像线路全套（推荐）
  python3 set-repo.py --mirror all          # 生成全部线路
  python3 set-repo.py --mirror jsd ghproxy  # 只生成指定线路
  python3 set-repo.py --check               # 在你本机实测每条线路通不通（大陆视角）
  python3 set-repo.py --list                # 列出所有线路代号
  python3 set-repo.py 用户名 仓库名            # 手动指定（不依赖 git remote）
  python3 set-repo.py --at <commit>         # 用 commit 号代替分支名（jsDelivr 更稳）

生成的文件：okys-{full,best,green,multi}-<线路>.json
全部 push 上去，壳里填能通的那几条地址就行。
"""
import json, os, re, subprocess, sys, glob, time
from concurrent.futures import ThreadPoolExecutor

# ── 线路表：代号 -> (说明, 前缀模板) ─────────────────────────────
LINES = [
    ('jsd',      'jsDelivr CDN · 主入口      ', 'https://cdn.jsdelivr.net/gh/{u}/{r}@{b}/'),
    ('fastly',   'jsDelivr · Fastly 节点     ', 'https://fastly.jsdelivr.net/gh/{u}/{r}@{b}/'),
    ('gcore',    'jsDelivr · Gcore 节点      ', 'https://gcore.jsdelivr.net/gh/{u}/{r}@{b}/'),
    ('testingcf','jsDelivr · Cloudflare 节点 ', 'https://testingcf.jsdelivr.net/gh/{u}/{r}@{b}/'),
    ('ghproxy',  'gh-proxy.com 代理          ', 'https://gh-proxy.com/https://raw.githubusercontent.com/{u}/{r}/{b}/'),
    ('ghpnet',   'ghproxy.net 代理           ', 'https://ghproxy.net/https://raw.githubusercontent.com/{u}/{r}/{b}/'),
    ('ghfast',   'ghfast.top 代理            ', 'https://ghfast.top/https://raw.githubusercontent.com/{u}/{r}/{b}/'),
    ('bgh',      'bgithub 镜像               ', 'https://raw.bgithub.xyz/{u}/{r}/{b}/'),
    ('gitproxy', 'gitproxy.click 代理        ', 'https://gitproxy.click/https://raw.githubusercontent.com/{u}/{r}/{b}/'),
    ('raw',      '官方 raw 直连（无镜像）      ', 'https://raw.githubusercontent.com/{u}/{r}/{b}/'),
]
LINE_MAP = {k: (desc, tpl) for k, desc, tpl in LINES}
DEFAULT_LINES = ['jsd', 'fastly', 'gcore', 'ghproxy', 'ghfast']
CONFIGS = ['okys-full', 'okys-best', 'okys-green']
REPO_FILES = CONFIGS + ['okys-multi']


def guess_remote():
    """从 git remote 里猜用户名/仓库名/分支"""
    try:
        out = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return None, None, None
    for line in out.splitlines():
        m = re.search(r'github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?\s', line)
        if m:
            u, r = m.group(1), m.group(2)
            b = 'main'
            try:
                b = subprocess.run(['git', 'symbolic-ref', '--short', 'HEAD'],
                                   capture_output=True, text=True, timeout=10).stdout.strip()
                if not b:
                    b = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                       capture_output=True, text=True, timeout=10).stdout.strip()
            except Exception:
                pass
            if not b or b == 'HEAD':
                b = 'main'
            return u, r, b
    return None, None, None


def fix_str(s, pref):
    """把字符串里的相对引用换成绝对前缀。
    两种形态：①整个字段就是 ./xxx  ②$ 分隔的复合字段里带第二段 ./xxx"""
    if s.startswith('./'):
        s = pref + s[2:]
    if '$$$./' in s:
        s = s.replace('$$$./', '$$$' + pref)
    return s


def to_abs(o, pref):
    """递归替换"""
    if isinstance(o, dict):
        return {k: to_abs(v, pref) for k, v in o.items()}
    if isinstance(o, list):
        return [to_abs(v, pref) for v in o]
    if isinstance(o, str):
        return fix_str(o, pref)
    return o


def leftovers(o, acc):
    """收集还没被换成绝对地址的相对引用（自检用）"""
    if isinstance(o, dict):
        for v in o.values():
            leftovers(v, acc)
    elif isinstance(o, list):
        for v in o:
            leftovers(v, acc)
    elif isinstance(o, str):
        if o.startswith('./') or '$$$./' in o:
            acc.append(o)
    return acc


def gen_line(code, pref, outdir='.'):
    """按前缀生成整套配置，返回生成的文件名列表"""
    made = []
    for name in CONFIGS:
        fp = name + '.json'
        if not os.path.exists(fp):
            continue
        d = to_abs(json.load(open(fp, encoding='utf-8')), pref)
        out = f'{outdir}/{name}-{code}.json'
        json.dump(d, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        made.append(out)
    # 壁纸清单
    if os.path.exists('wall.json'):
        w = to_abs(json.load(open('wall.json', encoding='utf-8')), pref)
        out = f'{outdir}/wall-{code}.json'
        json.dump(w, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        made.append(out)
    # 多仓版：内部那三条指向同线路的镜像版配置
    if os.path.exists('okys-multi.json'):
        m = to_abs(json.load(open('okys-multi.json', encoding='utf-8')), pref)
        for u in m.get('urls', []):
            for n in CONFIGS:
                if u.get('url') == pref + n + '.json':
                    u['url'] = f'{pref}{n}-{code}.json'
        out = f'{outdir}/okys-multi-{code}.json'
        json.dump(m, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        made.append(out)
    return made


def gen_multi_mirror(lines, u, r, b, outdir, ext_urls):
    """镜像多仓版：一个地址里装下所有线路，哪条挂了在壳里切仓就行"""
    urls = []
    for cfg, label in [('okys-full', '全能版'), ('okys-green', '绿源纯净版'), ('okys-best', '精选版')]:
        for lc in lines:
            _d, tpl = LINE_MAP[lc]
            urls.append({'name': f'⭐{label} · {lc}',
                         'url': tpl.format(u=u, r=r, b=b) + f'{cfg}-{lc}.json'})
    urls += ext_urls
    d = {'urls': urls}
    made = []
    for lc in lines:
        out = f'{outdir}/okys-mirror-{lc}.json'
        json.dump(d, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        made.append(out)
    return made, len(urls)


def count_refs(fp, pref):
    """校验：返回（指向本仓库的引用数, 没换干净的残留数, 引用的仓库内文件是否都在）"""
    d = json.load(open(fp, encoding='utf-8'))
    n = [0]
    miss = []

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str):
            if o.startswith(pref):
                n[0] += 1
                p = o[len(pref):].split('?')[0].split('#')[0].split('$$$')[0]
                if not os.path.exists(p):
                    miss.append(p)
            elif pref in o:
                n[0] += 1
    walk(d)
    return n[0], len(leftovers(d, [])), miss


def check(u, r, b, timeout=10):
    """并发实测每条线路可达性（在你自己机器上跑 = 你所在地的真实视角）"""
    import urllib.request, socket

    def probe(item):
        code, desc, tpl = item
        url = tpl.format(u=u, r=r, b=b) + 'okys-multi.json'
        t0 = time.time()
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read(4096)
            ms = int((time.time() - t0) * 1000)
            ok = data.strip().startswith(b'{') or b'urls' in data
            return code, desc, url, ('OK' if ok else '内容异常'), ms
        except Exception as e:
            msg = type(e).__name__
            if 'HTTPError' in msg:
                msg = 'HTTP ' + str(getattr(e, 'code', ''))
            elif 'URLError' in msg:
                msg = '连不上'
            return code, desc, url, msg, int((time.time() - t0) * 1000)

    print(f'正在实测 {len(LINES)} 条线路（目标 {u}/{r}@{b}/okys-multi.json）...\n')
    with ThreadPoolExecutor(max_workers=len(LINES)) as ex:
        res = list(ex.map(probe, LINES))
    res.sort(key=lambda x: (x[3] != 'OK', x[4]))
    ok_list = []
    for code, desc, url, st, ms in res:
        flag = '✅' if st == 'OK' else '❌'
        print(f'  {flag} {code:<10} {ms:>6}ms  {st:<10} {desc.strip()}')
        if st == 'OK':
            ok_list.append(code)
    print()
    if ok_list:
        print('推荐使用（按实测速度排序）：', ' '.join(ok_list[:3]))
        print(f'生成命令： python3 set-repo.py --mirror {" ".join(ok_list[:3])}')
    else:
        print('全部不通。先确认仓库是 Public、文件已经 push 上去、以及本机能访问 GitHub。')
    return ok_list


def main():
    args = list(sys.argv[1:])
    lines, at, do_check, do_list = None, None, False, False
    outdir = '.'
    for flag, setter in (('--check', 'c'), ('--list', 'l')):
        if flag in args:
            args.remove(flag)
            if setter == 'c':
                do_check = True
            else:
                do_list = True
    if '--out' in args:
        i = args.index('--out')
        outdir = args[i + 1]
        del args[i:i + 2]
    if '--at' in args:
        i = args.index('--at')
        at = args[i + 1]
        del args[i:i + 2]
    if '--mirror' in args:
        i = args.index('--mirror')
        lines = []
        j = i + 1
        while j < len(args) and not args[j].startswith('--'):
            lines.append(args[j])
            j += 1
        del args[i:j]
        if not lines or lines == ['all']:
            lines = DEFAULT_LINES if not lines else [k for k, _, _ in LINES]
        lines = [k for k in lines if k in LINE_MAP]
    if '--mode' in args:          # 兼容旧用法
        i = args.index('--mode')
        lines = [args[i + 1]]
        del args[i:i + 2]
    if '--base' in args:          # 兼容旧用法
        i = args.index('--base')
        lines = ['__custom__']
        LINE_MAP['__custom__'] = ('自定义前缀', args[i + 1] if args[i + 1].endswith('/') else args[i + 1] + '/')
        del args[i:i + 2]

    if do_list:
        print('可用线路代号：\n')
        for k, desc, tpl in LINES:
            print(f'  {k:<10} {desc}  {tpl}')
        return

    # 仓库信息
    if len(args) >= 2:
        u, r = args[0], args[1]
        b = args[2] if len(args) > 2 else 'main'
    else:
        u, r, b = guess_remote()
    if not u or not r:
        print('!! 没拿到仓库信息。两种用法：')
        print('   1) 在仓库目录里跑（先配好 git remote）：  python3 set-repo.py')
        print('   2) 手动指定：                          python3 set-repo.py 用户名 仓库名 [分支]')
        sys.exit(1)
    if at:
        b = at

    if do_check:
        check(u, r, b)
        print()
        print('提示：测完把 --check 给出的推荐线路交给 --mirror 生成配置即可。')

    if lines is None:
        if do_check:
            return
        lines = ['raw']

    print(f'仓库: {u}/{r}   分支/commit: {b}')
    os.makedirs(outdir, exist_ok=True)
    sig = f'#t={int(time.time())}'
    all_made, tips = [], []
    for code in lines:
        desc, tpl = LINE_MAP[code]
        pref = tpl.format(u=u, r=r, b=b)
        made = gen_line(code, pref, outdir)
        all_made += made
        if made:
            n, left, miss = count_refs(f'{outdir}/okys-full-{code}.json', pref)
            bad = []
            if left:
                bad.append(f'残留相对路径 {left} 处')
            if miss:
                bad.append(f'仓库内缺文件 {len(miss)} 个: {miss[:3]}')
            status = '✅ 校验通过' if not bad else '⚠️  ' + '；'.join(bad)
            print(f'  [{code:<10}] {desc.strip()}  →  {len(made)} 份配置, {n} 处指向本仓库  {status}')
        tips.append(pref + f'okys-full-{code}.json')

    # 镜像多仓版：把所有线路汇总成一份可切换的仓，壳里哪条挂了就切哪条
    ext = []
    if os.path.exists('okys-multi.json'):
        _m = json.load(open('okys-multi.json', encoding='utf-8'))
        ext = [x for x in _m.get('urls', []) if not x.get('url', '').startswith('./')]
    if len(lines) > 1:
        mmade, nurls = gen_multi_mirror(lines, u, r, b, outdir, ext)
        all_made += mmade
        print(f'  [镜像多仓] {nurls} 个仓入口汇总 → {len(mmade)} 份 okys-mirror-*.json')
        tips.insert(0, (LINE_MAP[lines[0]][1].format(u=u, r=r, b=b) if lines[0] != '__custom__'
                        else LINE_MAP['__custom__'][1]) + f'okys-mirror-{lines[0]}.json   ← 一个地址吃全部线路(推荐)')

    if not all_made:
        print('!! 当前目录没找到 okys-*.json，请在仓库根目录跑')
        sys.exit(1)

    print()
    print('生成完毕，共', len(all_made), '个文件。壳里填下面任一条（挑能通的）：')
    for t in tips:
        print('   ', t)
    print()
    print('别忘了一起 push 上去，地址才会生效：')
    print('    git add . && git commit -m "add mirrors" && git push')
    print()
    print('没把握哪条通？先跑： python3 set-repo.py --check')
    print('（jsDelivr 系列对 main 分支有缓存，刚 push 完可能要等几分钟；急着用就先填 ghproxy 类代理线路，')
    print('  或者用 --at <commit号> 生成基于 commit 的地址，内容寻址、没有缓存延迟。）')


if __name__ == '__main__':
    main()
