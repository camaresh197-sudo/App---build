import re, sys, collections
MAP = {'AA':'ɑ','AE':'æ','AH':'ʌ','AO':'ɔ','AW':'aʊ','AY':'aɪ','EH':'ɛ','ER':'ɝ','EY':'eɪ',
'IH':'ɪ','IY':'i','OW':'oʊ','OY':'ɔɪ','UH':'ʊ','UW':'u',
'B':'b','CH':'tʃ','D':'d','DH':'ð','F':'f','G':'ɡ','HH':'h','JH':'dʒ','K':'k','L':'l','M':'m',
'N':'n','NG':'ŋ','P':'p','R':'ɹ','S':'s','SH':'ʃ','T':'t','TH':'θ','V':'v','W':'w','Y':'j','Z':'z','ZH':'ʒ'}
VOWELS={'AA','AE','AH','AO','AW','AY','EH','ER','EY','IH','IY','OW','OY','UH','UW'}
def convert(phones):
    out=[]; onset=0
    for p in phones:
        m=re.match(r'([A-Z]+)([012])?$',p)
        base,stress=m.group(1),m.group(2)
        if base=='ER' and stress=='0': ipa='ɚ'
        elif base=='AH' and stress=='0': ipa='ə'
        else: ipa=MAP[base]
        out.append(ipa)
        if base in VOWELS:
            if stress in ('1','2'):
                out.insert(onset,'ˈ' if stress=='1' else 'ˌ')
            onset=len(out)
    return ''.join(out)
src,dst=sys.argv[1],sys.argv[2]
rows=[];bad=[]
for line in open(src,encoding='latin-1'):
    if line.startswith(';;;') or not line.strip(): continue
    word,*ph=line.split()
    word=re.sub(r'\(\d+\)$','',word)
    try: rows.append((word.lower(),convert(ph),' '.join(ph)))
    except (AttributeError,KeyError): bad.append(line.strip())
with open(dst,'w',encoding='utf-8') as f:
    f.write('word\tipa\tarpabet\n')
    for w,i,a in rows: f.write(f'{w}\t/{i}/\t{a}\n')
print('entries',len(rows),'skipped',len(bad)); print(bad[:5])
