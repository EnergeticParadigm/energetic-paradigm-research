#!/usr/bin/env python3
import csv, json, time, urllib.parse, urllib.request, difflib, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

START='2025-01-01'; END='2026-09-26'
OUT=Path('_meta_tmp/out_v2'); BY=OUT/'by_journal'; BY.mkdir(parents=True,exist_ok=True)
UA='EP-Meta-Research-Census/2.0'

# canonical title, publisher/family, aliases
JOURNALS=[
('ACM Transactions on Intelligent Systems and Technology (TIST)','ACM',['ACM Transactions on Intelligent Systems and Technology']),
('ACM Transactions on Autonomous and Adaptive Systems (TAAS)','ACM',['ACM Transactions on Autonomous and Adaptive Systems']),
('ACM Transactions on Evolutionary Learning and Optimization (TELO)','ACM',['ACM Transactions on Evolutionary Learning and Optimization']),
('ACM Transactions on Probabilistic Machine Learning (TOPML)','ACM',['ACM Transactions on Probabilistic Machine Learning']),
('ACM Transactions on Interactive Intelligent Systems (TiiS)','ACM',['ACM Transactions on Interactive Intelligent Systems']),
('ACM Transactions on Knowledge Discovery from Data (TKDD)','ACM',['ACM Transactions on Knowledge Discovery from Data']),
('ACM Transactions on Information Systems (TOIS)','ACM',['ACM Transactions on Information Systems']),
('ACM Computing Surveys (CSUR)','ACM',['ACM Computing Surveys']),
('ACM Transactions on Recommender Systems (TORS)','ACM',['ACM Transactions on Recommender Systems']),
('ACM Transactions on Human-Robot Interaction (THRI)','ACM',['ACM Transactions on Human-Robot Interaction']),
('ACM Transactions on Cyber-Physical Systems (TCPS)','ACM',['ACM Transactions on Cyber-Physical Systems']),
('ACM Transactions on Software Engineering and Methodology (TOSEM)','ACM',['ACM Transactions on Software Engineering and Methodology']),
('ACM Journal on Responsible Computing (JRC)','ACM',['ACM Journal on Responsible Computing']),
('Collective Intelligence','ACM/SAGE',['Collective Intelligence']),
('Journal of Artificial Intelligence Research (JAIR)','Independent',['Journal of Artificial Intelligence Research']),
('Journal of Machine Learning Research (JMLR)','Independent',['Journal of Machine Learning Research']),
('Transactions on Machine Learning Research (TMLR)','Independent',['Transactions on Machine Learning Research']),
('Artificial Intelligence','Elsevier',['Artificial Intelligence']),
('Neural Networks','Elsevier',['Neural Networks']),
('Knowledge-Based Systems','Elsevier',['Knowledge-Based Systems']),
('Expert Systems with Applications','Elsevier',['Expert Systems with Applications']),
('Information Sciences','Elsevier',['Information Sciences']),
('International Journal of Approximate Reasoning','Elsevier',['International Journal of Approximate Reasoning']),
('Neurocomputing','Elsevier',['Neurocomputing']),
('Applied Soft Computing','Elsevier',['Applied Soft Computing']),
('Engineering Applications of Artificial Intelligence','Elsevier',['Engineering Applications of Artificial Intelligence']),
('Robotics and Autonomous Systems','Elsevier',['Robotics and Autonomous Systems']),
('Cognitive Systems Research','Elsevier',['Cognitive Systems Research']),
('AI Open','Elsevier',['AI Open']),
('Artificial Intelligence Review','Springer Nature',['Artificial Intelligence Review']),
('Machine Learning','Springer Nature',['Machine Learning']),
('Applied Intelligence','Springer Nature',['Applied Intelligence']),
('Autonomous Agents and Multi-Agent Systems','Springer Nature',['Autonomous Agents and Multi-Agent Systems']),
('Genetic Programming and Evolvable Machines','Springer Nature',['Genetic Programming and Evolvable Machines']),
('Swarm Intelligence','Springer Nature',['Swarm Intelligence']),
('Data Mining and Knowledge Discovery','Springer Nature',['Data Mining and Knowledge Discovery']),
('Machine Intelligence Research','Springer Nature',['Machine Intelligence Research']),
('IEEE Transactions on Artificial Intelligence','IEEE',['IEEE Transactions on Artificial Intelligence']),
('IEEE Transactions on Neural Networks and Learning Systems','IEEE',['IEEE Transactions on Neural Networks and Learning Systems']),
('IEEE Transactions on Knowledge and Data Engineering','IEEE',['IEEE Transactions on Knowledge and Data Engineering']),
('IEEE Transactions on Emerging Topics in Computational Intelligence','IEEE',['IEEE Transactions on Emerging Topics in Computational Intelligence']),
('IEEE Transactions on Cognitive and Developmental Systems','IEEE',['IEEE Transactions on Cognitive and Developmental Systems']),
('IEEE Transactions on Systems, Man, and Cybernetics: Systems','IEEE',['IEEE Transactions on Systems, Man, and Cybernetics: Systems']),
('IEEE Robotics and Automation Letters','IEEE',['IEEE Robotics and Automation Letters']),
('Computational Linguistics','MIT Press',['Computational Linguistics']),
('Transactions of the Association for Computational Linguistics (TACL)','MIT Press/ACL',['Transactions of the Association for Computational Linguistics']),
('Evolutionary Computation','MIT Press',['Evolutionary Computation']),
('Artificial Life','MIT Press',['Artificial Life']),
('Natural Language Processing','Cambridge University Press',['Natural Language Processing','Natural Language Engineering']),
('Nature Machine Intelligence','Nature Portfolio',['Nature Machine Intelligence']),
('npj Artificial Intelligence','Nature Portfolio',['npj Artificial Intelligence','NPJ Artificial Intelligence']),
('Science Robotics','AAAS',['Science Robotics']),
]

def gj(url,retries=5):
  last=None
  for i in range(retries):
    try:
      req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
      with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
    except Exception as e:
      last=e; time.sleep(min(2**i,12))
  raise last

def norm(s): return re.sub(r'[^a-z0-9]+',' ',(s or '').lower()).strip()
def sim(a,b): return difflib.SequenceMatcher(None,norm(a),norm(b)).ratio()
def resolve_sources(aliases):
  found={}
  for alias in aliases:
    q=urllib.parse.quote(alias)
    d=gj(f'https://api.openalex.org/sources?search={q}&per-page=15')
    candidates=d.get('results',[])
    ranked=sorted(((sim(x.get('display_name',''),alias),x) for x in candidates),reverse=True,key=lambda z:z[0])
    if ranked and ranked[0][0] >= 0.72:
      sc,x=ranked[0]; found[x['id'].split('/')[-1]]=(x,sc,alias)
  return found

def matching_location(x, source_ids):
  for loc in x.get('locations') or []:
    sid=((loc.get('source') or {}).get('id') or '').split('/')[-1]
    if sid in source_ids:return loc
  return x.get('primary_location') or {}

def fetch_source_works(sid, canonical, publisher, source_ids):
  rows=[]; cursor='*'
  while cursor:
    flt=f'locations.source.id:{sid},from_publication_date:{START},to_publication_date:{END}'
    params=urllib.parse.urlencode({'filter':flt,'per-page':200,'cursor':cursor})
    d=gj('https://api.openalex.org/works?'+params); arr=d.get('results',[])
    for x in arr:
      loc=matching_location(x,source_ids); bib=x.get('biblio') or {}; auth=[]
      for au in x.get('authorships') or []:
        n=((au.get('author') or {}).get('display_name') or '')
        if n:auth.append(n)
      doi=(x.get('doi') or '').replace('https://doi.org/','')
      rows.append({'journal':canonical,'publisher_family':publisher,'year':(x.get('publication_date') or '')[:4],
      'publication_date':x.get('publication_date') or '','title':x.get('title') or '','authors':'; '.join(auth),
      'volume':bib.get('volume') or '','issue':bib.get('issue') or '','doi':doi,
      'article_url':loc.get('landing_page_url') or x.get('id') or '',
      'article_type':x.get('type_crossref') or x.get('type') or '',
      'source_container_title':((loc.get('source') or {}).get('display_name') or ''),'openalex_id':x.get('id') or ''})
    cursor=(d.get('meta') or {}).get('next_cursor')
    if not arr:break
  return rows

def one(entry):
  canonical,publisher,aliases=entry
  srcs=resolve_sources(aliases); sids=set(srcs)
  if not sids:
    return [],{'journal':canonical,'publisher_family':publisher,'status':'UNRESOLVED','source_ids':'','source_names':'','issns':'','count':0,'notes':'No OpenAlex source resolved'}
  allr=[]
  for sid in sids: allr.extend(fetch_source_works(sid,canonical,publisher,sids))
  ded={}
  for r in allr:
    k=('doi:'+r['doi'].lower()) if r['doi'] else ('t:'+norm(r['title']))
    ded[k]=r
  rows=list(ded.values())
  names=[]; issns=[]
  for sid,(x,sc,alias) in srcs.items():
    names.append(f"{sid}:{x.get('display_name','')}")
    for z in x.get('issn') or []:issns.append(z)
  cov={'journal':canonical,'publisher_family':publisher,'status':'OK','source_ids':';'.join(sorted(sids)),
       'source_names':' | '.join(names),'issns':';'.join(sorted(set(issns))),'count':len(rows),'notes':''}
  return rows,cov

allrows=[]; coverage=[]
with ThreadPoolExecutor(max_workers=5) as ex:
  fut={ex.submit(one,e):e[0] for e in JOURNALS}
  for f in as_completed(fut):
    n=fut[f]
    try:
      rows,c=f.result(); allrows.extend(rows); coverage.append(c); print(n,len(rows),flush=True)
    except Exception as e:
      coverage.append({'journal':n,'publisher_family':'','status':'ERROR','source_ids':'','source_names':'','issns':'','count':0,'notes':repr(e)})
      print('ERROR',n,repr(e),flush=True)
# global sort
allrows.sort(key=lambda r:(r['journal'],r['publication_date'],r['title']))
fields=['journal','publisher_family','year','publication_date','title','authors','volume','issue','doi','article_url','article_type','source_container_title','openalex_id']
with open(OUT/'level_a_journals_2025_2026.csv','w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(allrows)
# split by journal for connector retrieval
index=[]
for i,(canonical,publisher,aliases) in enumerate(JOURNALS,1):
  rs=[r for r in allrows if r['journal']==canonical]
  slug=re.sub(r'[^a-z0-9]+','_',norm(canonical)).strip('_')[:90]
  fn=f'{i:02d}_{slug}.csv'
  with open(BY/fn,'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rs)
  index.append({'index':i,'journal':canonical,'publisher_family':publisher,'file':fn,'count':len(rs)})
with open(OUT/'coverage.csv','w',newline='',encoding='utf-8') as f:
  cf=['journal','publisher_family','status','source_ids','source_names','issns','count','notes'];w=csv.DictWriter(f,fieldnames=cf);w.writeheader();w.writerows(sorted(coverage,key=lambda x:x['journal']))
with open(OUT/'index.json','w',encoding='utf-8') as f:json.dump(index,f,indent=2,ensure_ascii=False)
with open(OUT/'manifest.json','w',encoding='utf-8') as f:json.dump({'start':START,'end':END,'journal_count':len(JOURNALS),'paper_count':len(allrows),'generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},f,indent=2)
print('DONE',len(allrows),flush=True)
