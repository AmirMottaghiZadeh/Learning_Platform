"""Build four portable search-suggestion previews from the read-only snapshot.

The suggestions run the real TypeScript SearchCatalog with a small, documented
subset of snapshot aliases. No server, network or package key is embedded.
"""
import base64
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from apps.uptodate.search_catalog import SearchCatalog, normalize
from apps.uptodate.text import plain_title

PREFIXES = ('h ', 'helico', 'diab', 'hyper', 'asth', 'apix', 'copd', 'heart failure', 'dvt', 'warfarin', 'pneumo')


def read_only(name):
    return sqlite3.connect(f'file:/home/amir/Documents/UpToDate/{name}.db?mode=ro', uri=True)


def build():
    db = read_only('search')
    fts = read_only('fts')
    try:
        rows = [r for r in db.execute('SELECT id, word, weight FROM query ORDER BY rowid')
                if normalize(r[1]).startswith(PREFIXES)]
        catalog = SearchCatalog.from_rows(rows, db.execute(
            'SELECT id, x_topic_hits, a_topic_hits, p_topic_hits, i_topic_hits FROM query_topic'))
        titles = {str(cid): plain_title(title) for cid, title in fts.execute('SELECT contentId, title FROM fts WHERE type=1 ORDER BY rowid')}
    finally:
        db.close()
        fts.close()
    details = {}
    compact = {}
    for cid, lists in catalog.topics.items():
        info, small = [], []
        for hits in lists:
            valid = list(dict.fromkeys(t.strip() for t in hits.split(',') if t.strip() in titles))
            small.append(','.join(valid[:2]))
            info.append({'count': len(valid), 'articles': [{'id': t, 'title': titles[t]} for t in valid[:3]]})
        compact[cid] = small
        details[cid] = info
    data = {'search': {'queries': catalog.queries, 'topics': compact}, 'details': details,
            'validIds': sorted({t for lists in compact.values() for csv in lists for t in csv.split(',') if t}),
            'defaults': ['h py', 'h pylori', 'diab', 'hyper', 'asth', 'apix']}
    # Compile the production catalog and title sanitizer, rather than recreating
    # ranking logic in a visual prototype.
    compiler = r"""
const fs=require('node:fs'),path=require('node:path'),{createRequire}=require('node:module');
const root=process.argv[1],req=createRequire(path.join(root,'frontend/package.json')),ts=req('typescript');
const compile=f=>ts.transpileModule(fs.readFileSync(path.join(root,'frontend/src',f),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;
process.stdout.write(JSON.stringify({html:compile('utils/html.ts'),catalog:compile('offline/uptodateSearchCatalog.ts')}));
"""
    modules = json.loads(subprocess.check_output(['node', '-e', compiler, str(ROOT)], text=True))
    template = (HERE / 'preview.template.html').read_text()
    for token, filename in [('__FONT_REGULAR__', '400Regular/Vazirmatn_400Regular.ttf'),
                            ('__FONT_SEMIBOLD__', '600SemiBold/Vazirmatn_600SemiBold.ttf')]:
        font = ROOT / 'frontend/node_modules/@expo-google-fonts/vazirmatn' / filename
        template = template.replace(token, base64.b64encode(font.read_bytes()).decode())
    logo = ROOT / 'frontend/assets/icons/uptodate-logo.png'
    template = template.replace('__LOGO__', base64.b64encode(logo.read_bytes()).decode())
    template = template.replace('__DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c'))
    template = template.replace('__MODULES__', json.dumps(modules, ensure_ascii=False).replace('<', '\\u003c'))
    for name, mode in [('index', 'attached'), ('attached', 'attached'), ('guided', 'guided'), ('preview', 'preview'), ('focused', 'focused')]:
        target = HERE / f'{name}.html'
        target.write_text(template.replace('__MODE__', mode))
        print(f'{target.name}: {target.stat().st_size:,} bytes')
    print(f'{len(catalog.queries)} real aliases, {len(details)} concepts; ranking shared with the app')


if __name__ == '__main__':
    build()
