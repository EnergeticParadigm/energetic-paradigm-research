#!/usr/bin/env python3
import csv, json, time, urllib.parse, urllib.request, difflib, re
from collections import defaultdict
from pathlib import Path

START='2025-01-01'
END='2026-09-26'
OUT=Path('_meta_tmp/out')
OUT.mkdir(parents=True, exist_ok=True)

JOURNALS=[
('ACM Transactions on Intelligent Systems and Technology (TIST)', ['ACM Transactions on Intelligent Systems and Technology']),
('ACM Transactions on Autonomous and Adaptive Systems (TAAS)', ['ACM Transactions on Autonomous and Adaptive Systems']),
('ACM Transactions on Evolutionary Learning and Optimization (TELO)', ['ACM Transactions on Evolutionary Learning and Optimization']),
('ACM Transactions on Probabilistic Machine Learning (TOPML)', ['ACM Transactions on Probabilistic Machine Learning']),
('ACM Transactions on Interactive Intelligent Systems (TiiS)', ['ACM Transactions on Interactive Intelligent Systems']),
('ACM Transactions on Knowledge Discovery from Data (TKDD)', ['ACM Transactions on Knowledge Discovery from Data']),
('ACM Transactions on Information Systems (TOIS)', ['ACM Transactions on Information Systems']),
('ACM Computing Surveys (CSUR)', ['ACM Computing Surveys']),
('ACM Transactions on Recommender Systems (TORS)', ['ACM Transactions on Recommender Systems']),
('ACM Transactions on Human-Robot Interaction (THRI)', ['ACM Transactions on Human-Robot Interaction']),
('ACM Transactions on Cyber-Physical Systems (TCPS)', ['ACM Transactions on Cyber-Physical Systems']),
('ACM Transactions on Software Engineering and Methodology (TOSEM)', ['ACM Transactions on Software Engineering and Methodology']),
('ACM Journal on Responsible Computing (JRC)', ['ACM Journal on Responsible Computing']),
('Collective Intelligence', ['Collective Intelligence']),
('Journal of Artificial Intelligence Research (JAIR)', ['Journal of Artificial Intelligence Research']),
('Journal of Machine Learning Research (JMLR)', ['Journal of Machine Learning Research']),
('Transactions on Machine Learning Research (TMLR)', ['Transactions on Machine Learning Research']),
('Artificial Intelligence', ['Artificial Intelligence']),
('Neural Networks', ['Neural Networks']),
('Knowledge-Based Systems', ['Knowledge-Based Systems']),
('Expert Systems with Applications', ['Expert Systems with Applications']),
('Information Sciences', ['Information Sciences']),
('International Journal of Approximate Reasoning', ['International Journal of Approximate Reasoning']),
('Neurocomputing', ['Neurocomputing']),
('Applied Soft Computing', ['Applied Soft Computing']),
('Engineering Applications of Artificial Intelligence', ['Engineering Applications of Artificial Intelligence']),
('Robotics and Autonomous Systems', ['Robotics and Autonomous Systems']),
('Cognitive Systems Research', ['Cognitive Systems Research']),
('AI Open', ['AI Open']),
('Artificial Intelligence Review', ['Artificial Intelligence Review']),
('Machine Learning', ['Machine Learning']),
('Applied Intelligence', ['Applied Intelligence']),
('Autonomous Agents and Multi-Agent Systems', ['Autonomous Agents and Multi-Agent Systems']),
('Genetic Programming and Evolvable Machines', ['Genetic Programming and Evolvable Machines']),
('Swarm Intelligence', ['Swarm Intelligence']),
('Data Mining and Knowledge Discovery', ['Data Mining and Knowledge Discovery']),
('Machine Intelligence Research', ['Machine Intelligence Research']),
('IEEE Transactions on Artificial Intelligence', ['IEEE Transactions on Artificial Intelligence']),
('IEEE Transactions on Neural Networks and Learning Systems', ['IEEE Transactions on Neural Networks and Learning Systems']),
('IEEE Transactions on Knowledge and Data Engineering', ['IEEE Transactions on Knowledge and Data Engineering']),
('IEEE Transactions on Emerging Topics in Computational Intelligence', ['IEEE Transactions on Emerging Topics in Computational Intelligence']),
('IEEE Transactions on Cognitive and Developmental Systems', ['IEEE Transactions on Cognitive and Developmental Systems']),
('IEEE Transactions on Systems, Man, and Cybernetics: Systems', ['IEEE Transactions on Systems, Man, and Cybernetics: Systems']),
('IEEE Robotics and Automation Letters', ['IEEE Robotics and Automation Letters']),
('Computational Linguistics', ['Computational Linguistics']),
('Transactions of the Association for Computational Linguistics (TACL)', ['Transactions of the Association for Computational Linguistics']),
('Evolutionary Computation', ['Evolutionary Computation']),
('Artificial Life', ['Artificial Life']),
('Natural Language Processing', ['Natural Language Processing','Natural Language Engineering']),
('Nature Machine Intelligence', ['Nature Machine Intelligence']),
('npj Artificial Intelligence', ['npj Artificial Intelligence','NPJ Artificial Intelligence']),
('Science Robotics', ['Science Robotics']),
]

UA='EP-Meta-Research-Journal-Census/1.0 (research metadata census)'
def get_json(url, retries=5):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url, headers={'User-Agent':UA,'Accept':'application/json'})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            last=e; time.sleep(min(2**i,16))
    raise last

def norm(s):
    return re.sub(r'[^a-z0-9]+',' ',(s or '').lower()).strip()

def sim(a,b):
    return difflib.SequenceMatcher(None,norm(a),norm(b)).ratio()

def best_match(items, aliases, name_getter):
    best=None; bs=-1
    for it in items:
        n=name_getter(it)
        s=max(sim(n,a) for a in aliases)
        if s>bs: best,bs=it,s
    return best,bs

def fmt_auth_openalex(authorships):
    out=[]
    for x in authorships or []:
        a=(x.get('author') or {}).get('display_name')
        if a: out.append(a)
    return '; '.join(out)

def fmt_auth_crossref(auths):
    out=[]
    for a in auths or []:
        n=' '.join(x for x in [a.get('given',''),a.get('family','')] if x).strip()
        if n: out.append(n)
    return '; '.join(out)

records={}
coverage=[]

def key_for(doi,title,journal):
    doi=(doi or '').lower().replace('https://doi.org/','').strip()
    if doi: return 'doi:'+doi
    return 'title:'+norm(title)+'|'+norm(journal)

for idx,(canonical,aliases) in enumerate(JOURNALS,1):
    print(f'[{idx}/{len(JOURNALS)}] {canonical}', flush=True)
    cov={'journal':canonical,'openalex_source_id':'','openalex_source_name':'','openalex_match_score':'','openalex_count':0,
         'crossref_issn':'','crossref_source_name':'','crossref_match_score':'','crossref_count':0,'unique_count':0,'notes':''}
    before=len(records)
    # OpenAlex source resolution + works
    try:
        q=urllib.parse.quote(aliases[0])
        data=get_json(f'https://api.openalex.org/sources?search={q}&per-page=10')
        src,score=best_match(data.get('results',[]),aliases,lambda x:x.get('display_name',''))
        if src and score>=0.68:
            sid=src['id'].split('/')[-1]
            cov['openalex_source_id']=sid; cov['openalex_source_name']=src.get('display_name',''); cov['openalex_match_score']=round(score,3)
            cursor='*'; count=0
            while cursor:
                flt=f'primary_location.source.id:{sid},from_publication_date:{START},to_publication_date:{END}'
                params=urllib.parse.urlencode({'filter':flt,'per-page':200,'cursor':cursor,'select':'id,doi,title,publication_date,authorships,biblio,type,type_crossref,primary_location'})
                w=get_json('https://api.openalex.org/works?'+params)
                arr=w.get('results',[])
                for x in arr:
                    loc=x.get('primary_location') or {}; bib=x.get('biblio') or {}
                    rawsrc=((loc.get('source') or {}).get('display_name') or '')
                    title=x.get('title') or ''
                    doi=x.get('doi') or ''
                    k=key_for(doi,title,canonical)
                    rec=records.get(k,{})
                    rec.update({
                        'journal':canonical,'year':(x.get('publication_date') or '')[:4], 'publication_date':x.get('publication_date') or '',
                        'title':title,'authors':fmt_auth_openalex(x.get('authorships')),'volume':bib.get('volume') or '',
                        'issue':bib.get('issue') or '', 'doi':doi.replace('https://doi.org/','') if doi else '',
                        'article_url':loc.get('landing_page_url') or x.get('id') or '', 'article_type':x.get('type_crossref') or x.get('type') or '',
                        'source_used':'OpenAlex','source_container_title':rawsrc,'openalex_id':x.get('id') or ''
                    })
                    records[k]=rec; count+=1
                cursor=(w.get('meta') or {}).get('next_cursor')
                if not arr: break
                time.sleep(0.06)
            cov['openalex_count']=count
        else:
            cov['notes'] += 'OpenAlex source unresolved; '
    except Exception as e:
        cov['notes'] += f'OpenAlex error: {type(e).__name__}; '
    # Crossref source resolution + works
    try:
        params=urllib.parse.urlencode({'query':aliases[0],'rows':20})
        jd=get_json('https://api.crossref.org/journals?'+params)
        items=(jd.get('message') or {}).get('items',[])
        js,score=best_match(items,aliases,lambda x:x.get('title',''))
        if js and score>=0.68 and js.get('ISSN'):
            issn=(js.get('ISSN') or [''])[0]
            cov['crossref_issn']=issn; cov['crossref_source_name']=js.get('title',''); cov['crossref_match_score']=round(score,3)
            cursor='*'; count=0
            while cursor:
                flt=f'from-pub-date:{START},until-pub-date:{END},type:journal-article'
                params=urllib.parse.urlencode({'filter':flt,'rows':1000,'cursor':cursor,'select':'DOI,title,author,published,published-online,published-print,container-title,volume,issue,type,URL'})
                cd=get_json(f'https://api.crossref.org/journals/{urllib.parse.quote(issn)}/works?'+params)
                msg=cd.get('message') or {}; arr=msg.get('items',[])
                for x in arr:
                    title=' '.join(x.get('title') or [])
                    cont='; '.join(x.get('container-title') or [])
                    doi=x.get('DOI') or ''
                    date=''
                    for fld in ['published-online','published-print','published']:
                        parts=((x.get(fld) or {}).get('date-parts') or [])
                        if parts and parts[0]:
                            p=parts[0]; date='-'.join([str(p[0]).zfill(4)]+([str(p[1]).zfill(2)] if len(p)>1 else ['01'])+([str(p[2]).zfill(2)] if len(p)>2 else ['01']))
                            break
                    k=key_for(doi,title,canonical)
                    rec=records.get(k,{})
                    # Keep OpenAlex date if exact; fill/augment with Crossref metadata
                    rec.setdefault('journal',canonical); rec.setdefault('year',date[:4]); rec.setdefault('publication_date',date)
                    rec.setdefault('title',title); rec.setdefault('authors',fmt_auth_crossref(x.get('author')))
                    if not rec.get('authors'): rec['authors']=fmt_auth_crossref(x.get('author'))
                    if not rec.get('volume'): rec['volume']=x.get('volume') or ''
                    if not rec.get('issue'): rec['issue']=x.get('issue') or ''
                    if not rec.get('doi'): rec['doi']=doi
                    if not rec.get('article_url'): rec['article_url']=x.get('URL') or ''
                    if not rec.get('article_type'): rec['article_type']=x.get('type') or ''
                    rec['source_used']='OpenAlex + Crossref' if rec.get('openalex_id') else 'Crossref'
                    rec['source_container_title']=rec.get('source_container_title') or cont
                    rec.setdefault('openalex_id','')
                    records[k]=rec; count+=1
                cursor=msg.get('next-cursor')
                if not arr: break
                if len(arr)<1000: break
                time.sleep(0.08)
            cov['crossref_count']=count
        else:
            cov['notes'] += 'Crossref journal unresolved; '
    except Exception as e:
        cov['notes'] += f'Crossref error: {type(e).__name__}; '
    cov['unique_count']=len(records)-before
    coverage.append(cov)

# stable sort and output
rows=list(records.values())
rows=[r for r in rows if START <= (r.get('publication_date') or '9999') <= END]
rows.sort(key=lambda r:(r.get('journal',''),r.get('publication_date',''),r.get('title','')))
fields=['journal','year','publication_date','title','authors','volume','issue','doi','article_url','article_type','source_used','source_container_title','openalex_id']
with open(OUT/'level_a_journals_2025_2026.csv','w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
with open(OUT/'level_a_journal_coverage.csv','w',encoding='utf-8',newline='') as f:
    fields2=list(coverage[0].keys()); w=csv.DictWriter(f,fieldnames=fields2); w.writeheader(); w.writerows(coverage)
with open(OUT/'manifest.json','w',encoding='utf-8') as f:
    json.dump({'start':START,'end':END,'journals':len(JOURNALS),'papers':len(rows),'generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},f,indent=2)
print('DONE',len(rows),'papers',flush=True)
