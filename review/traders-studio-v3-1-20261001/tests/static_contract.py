from pathlib import Path,PurePosixPath
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];P=R/'public';V=R/'private';checks=[]
def check(name,cond):
 if not cond:raise AssertionError(name)
 checks.append(name)
public=json.loads((P/'trading/assets/catalog.json').read_text());full=json.loads((V/'catalog-full.json').read_text())
check('unique 39 catalog entries',len(public)==39 and len({d['id'] for d in public})==39)
check('7 populated source platforms',len(set(p for d in public for p in d['platforms']))==7)
check('source ZIPs are absent from public directory',not list(P.rglob('*.zip')))
check('source trees are absent from public directory',not (P/'trading/sources').exists() and not (P/'trading/downloads').exists())
check('pending author directory is private',not list(P.rglob('*pending*')))
for d in full:
 zpath=V/d['download'];check(d['id']+' source archive exists',zpath.exists())
 with zipfile.ZipFile(zpath) as z:
  check(d['id']+' valid ZIP integrity',z.testzip() is None)
  names=z.namelist();check(d['id']+' includes usage conditions',any(PurePosixPath(n).name=='LICENSE.txt' for n in names))
  check(d['id']+' safe ZIP names',all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts for n in names))
 for f in d['files']:
  b=(V/f['local_source']).read_bytes();check(d['id']+' existing source file '+f['path'],len(b)>0)
  if f.get('sha256'):check(d['id']+' SHA256 '+f['path'],hashlib.sha256(b).hexdigest()==f['sha256'])
 check(d['id']+' public metadata only',set(next(x for x in public if x['id']==d['id'])).isdisjoint({'files','local_source','download','permissionEvidence','ownerId'}))
for f in P.rglob('*'):
 if f.is_file() and f.suffix in {'.html','.js','.json','.css'}:
  s=f.read_text();check(str(f.relative_to(P))+' no obsolete access copy',all(x not in s for x in ['メール登録不要','元のライセンスとともに','No email gate','No email required','window.BSV_ZIPS','window.BSV_DETAILS']))
check('creator license requires an explicit choice','id="license" name="license" required' in (P/'trading/publish/index.html').read_text())
result={'status':'PASS','checks':len(checks),'scope':'Local files, package integrity, source hash consistency and public/private layout only. Not legal advice, runtime testing, production auth or deployment.','details':checks}
(R/'tests/static-results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False));print('Static checks:',len(checks),'PASS')
