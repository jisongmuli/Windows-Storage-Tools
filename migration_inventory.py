import json
import os
import pathlib
import time
from collections import defaultdict

import argparse
parser = argparse.ArgumentParser(description='Read-only directory inventory, recording links without following them.')
parser.add_argument('--root', action='append', help='Directory to inspect; may be repeated. Default: user home.')
parser.add_argument('--output-dir', type=pathlib.Path, default=pathlib.Path('reports'))
args = parser.parse_args()
OUT = args.output_dir.resolve()
OUT.mkdir(parents=True, exist_ok=True)
roots = [os.path.abspath(item) for item in (args.root or [str(pathlib.Path.home())])]
sizes = defaultdict(int)
counts = defaultdict(int)
links = {}
aliases = {}
errors = []
seen_dirs = {}
started = time.time()
for root in roots:
    stack = [(root, False)]
    while stack:
        p, done = stack.pop()
        if done:
            if p != root:
                parent = os.path.dirname(p)
                sizes[parent] += sizes[p]
                counts[parent] += counts[p]
            continue
        try:
            st = os.lstat(p)
            if getattr(st, 'st_file_attributes', 0) & 1024:
                links[p] = os.path.realpath(p)
                continue
            identity = (st.st_dev, st.st_ino)
            if st.st_ino and identity in seen_dirs:
                aliases[p] = seen_dirs[identity]
                continue
            if st.st_ino:
                seen_dirs[identity] = p
            stack.append((p, True))
            dirs = []
            with os.scandir(p) as entries:
                for entry in entries:
                    try:
                        es = entry.stat(follow_symlinks=False)
                        if getattr(es, 'st_file_attributes', 0) & 1024:
                            links[entry.path] = os.path.realpath(entry.path)
                        elif entry.is_dir(follow_symlinks=False):
                            dirs.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            sizes[p] += es.st_size
                            counts[p] += 1
                    except OSError as exc:
                        errors.append({'path': entry.path, 'error': str(exc)})
            # Scan Local/Packages last to avoid MSIX aliases obscuring real app data.
            dirs.sort(key=lambda x: ('\\Packages' in x, x.casefold()), reverse=True)
            stack.extend((x, False) for x in dirs)
        except OSError as exc:
            errors.append({'path': p, 'error': str(exc)})
    print(json.dumps({'root': root, 'GiB': round(sizes[root]/2**30, 3), 'seconds': round(time.time()-started, 1)}), flush=True)
result = {'sizes': dict(sizes), 'counts': dict(counts), 'links': links, 'aliases': aliases,
          'errors': errors, 'seconds': time.time()-started}
(OUT / 'storage-inventory.json').write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
print(json.dumps({'report': str(OUT / 'storage-inventory.json'), 'directories': len(sizes), 'errors': len(errors)}), flush=True)
