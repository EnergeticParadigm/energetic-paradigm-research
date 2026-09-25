#!/usr/bin/env python3
import csv,json,time,urllib.parse,urllib.request,difflib,re
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
START='2025-01-01'; END='2026-09-26'; OUT=Path('_meta_tmp/out_fast'); OUT.mkdir(parents=True,exist_ok=True)
NAMES=[
'ACM Transactions on Intelligent Systems and Technology','ACM Transactions on Autonomous and Adaptive Systems','ACM Transactions on Evolutionary Learning and Optimization','ACM Transactions on Probabilistic Machine Learning','ACM Transactions on Interactive Intelligent Systems','ACM Transactions on Knowledge Discovery from Data','ACM Transactions on Information Systems','ACM Computing Surveys','ACM Transactions on Recommender Systems','ACM Transactions on Human-Robot Interaction','ACM Transactions on Cyber-Physical Systems','ACM Transactions on Software Engineering and Methodology','ACM Journal on Responsible Computing','Collective Intelligence','Journal of Artificial Intelligence Research','Journal of Machine Learning Research','Transactions on Machine Learning Research','Artificial Intelligence','Neural Networks','Knowledge-Based Systems','Expert Systems with Applications','Information Sciences','International Journal of Approximate Reasoning','Neurocomputing','Applied Soft Computing','Engineering Applications of Artificial Intelligence','Robotics and Autonomous Systems','Cognitive Systems Research','AI Open','Artificial Intelligence Review','Machine Learning','Applied Intelligence','Autonomous Agents and Multi-Agent Systems','Genetic Programming and Evolvable Machines','Swarm Intelligence','Data Mining and Knowledge Discovery','Machine Intelligence Research','IEEE Transactions on Artificial Intelligence','IEEE Transactions on Neural Networks and Learning Systems','IEEE Transactions on Knowledge and Data Engineering','IEEE Transactions on Emerging Topics in Computational Intelligence','IEEE Transactions on Cognitive and Developmental Systems','IEEE Transactions on Systems, Man, and Cybernetics: Systems','IEEE Robotics and Automation Letters','Computational Linguistics','Transactions of the Association for Computational Linguistics','Evolutionary Computation','Artificial Life','Natural Language Processing','Nature Machine Intelligence','npj Artificial Intelligence','Science Robotics']
ALIASES={'Natural Language Processing':['Natural Language Processing','Natural Language Engineering']}
UA='EP-Meta-Research-Census/1.1'
def gj(url,retries=4):
  last=None
  for i in range(retries):
    try:
      req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
      with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
    except Exception as e:last=e; time.sleep(1.5*(i+1))
  raise last
def norm(s):return re.sub(r'[^a-z0-9]+',' ',(s or '').lower()).strip()
def sim(a,b):return difflib.SequenceMatcher(None,norm(a),norm(b)).ratio()
def one(name):
  als=ALIASES.get(name,[name]); q=urllib.parse.quote(name)
  sd=gj(f'https://api.openalex.org/sources?search={q}&per-page=10')
  best=None; bs=-1
  for s in sd.get('results',[]):
    sc=max(sim(s.get('display_name',''),a) for a in als)
    if sc>bs:best,bs=s,sc
  if not best or bs<0.68:return name,[],{'journal':name,'status':'UNRESOLVED','source':'','source_id':'','match_score':round(bs,3)}
  sid=best['id'].split('/')[-1]; rows=[]; cursor='*'
  while cursor:
    flt=f'primary_location.source.id:{sid},from_publication_date:{START},to_publication_date:{END}'
    params=urllib.parse.urlencode({'filter':flt,'per-page':200,'cursor':cursor})
    d=gj('https://api.openalex.org/works?'+params); arr=d.get('results',[])
    for x in arr:
      loc=x.get('primary_location') or {}; bib=x.get('biblio') or {}; auth=[]
      for au in x.get('authorships') or []:
        n=((au.get('author') or {}).get('display_name') or '')
        if n:auth.append(n)
      doi=(x.get('doi') or '').replace('https://doi.org/','')
      rows.append({'journal':name,'year':(x.get('publication_date') or '')[:4],'publication_date':x.get('publication_date') or '','title':x.get('title') or '','authors':'; '.join(auth),'volume':bib.get('volume') or '','issue':bib.get('issue') or '','doi':doi,'article_url':loc.get('landing_page_url') or x.get('id') or '','article_type':x.get('type_crossref') or x.get('type') or '','source_used':'OpenAlex','source_container_title':((loc.get('source') or {}).get('display_name') or ''),'openalex_id':x.get('id') or ''})
    cursor=(d.get('meta') or {}).get('next_cursor')
    if not arr:break
  return name,rows,{'journal':name,'status':'OK','source':best.get('display_name',''),'source_id':sid,'match_score':round(bs,3),'count':len(rows),'issn_l':best.get('issn_l') or '','issn':';'.join(best.get('issn') or [])}
allrows=[]; cov=[]
with ThreadPoolExecutor(max_workers=6) as ex:
  fut={ex.submit(one,n):n for n in NAMES}
  for f in as_completed(fut):
    n=fut[f]
    try:
      name,rows,c=f.result(); allrows.extend(rows); cov.append(c); print(name,len(rows),flush=True)
    except Exception as e:
      cov.append({'journal':n,'status':'ERROR','source':'','source_id':'','match_score':'','count':0,'notes':repr(e)}); print('ERROR',n,repr(e),flush=True)
# dedupe by DOI else title+journal
seen={};
for r in allrows:
  k=('doi:'+r['doi'].lower()) if r['doi'] else ('t:'+norm(r['title'])+'|'+norm(r['journal']))
  seen[k]=r
rows=list(seen.values()); rows.sort(key=lambda r:(r['journal'],r['publication_date'],r['title']))
fields=['journal','year','publication_date','title','authors','volume','issue','doi','article_url','article_type','source_used','source_container_title','openalex_id']
with open(OUT/'level_a_journals_2025_2026_openalex.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
cf=sorted({k for x in cov for k in x.keys()})
with open(OUT/'coverage_openalex.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=cf);w.writeheader();w.writerows(sorted(cov,key=lambda x:x['journal']))
with open(OUT/'manifest.json','w') as f:json.dump({'start':START,'end':END,'journal_count':len(NAMES),'paper_count':len(rows)},f,indent=2)
print('DONE',len(rows),flush=True)
