"""Train two local text classifiers, using family-disjoint validation."""
import csv, json, sys
from pathlib import Path
from collections import Counter
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import classification_report, confusion_matrix

ROOT=Path(__file__).resolve().parents[1]
with (ROOT/'data/tickets_labeled.csv').open(encoding='utf-8-sig',newline='') as f:
    rows=list(csv.DictReader(f))
texts=[r['text'] for r in rows]; groups=[r['family'] for r in rows]
train_idx,val_idx=next(GroupShuffleSplit(n_splits=1,test_size=.22,random_state=42).split(texts,groups=groups))
train=[rows[i] for i in train_idx]; val=[rows[i] for i in val_idx]

def make_model():
    return Pipeline([('tfidf',TfidfVectorizer(analyzer='char_wb',ngram_range=(2,5),sublinear_tf=True,min_df=2,max_features=65000)),('clf',LogisticRegression(max_iter=1500,class_weight='balanced',random_state=42))])

scope=make_model(); scope.fit([r['text'] for r in train],[r['scope'] for r in train])
tech_train=[r for r in train if r['scope']=='it']
tech=make_model();tech.fit([r['text'] for r in tech_train],[r['category'] for r in tech_train])

def evaluate(dataset):
    y_scope=[r['scope'] for r in dataset]
    p_scope=scope.predict([r['text'] for r in dataset]).tolist()
    relevant=[r for r in dataset if r['scope']=='it']
    y_cat=[r['category'] for r in relevant]
    p_cat=tech.predict([r['text'] for r in relevant]).tolist()
    return {'scope':classification_report(y_scope,p_scope,zero_division=0,output_dict=True),'category':classification_report(y_cat,p_cat,zero_division=0,output_dict=True), 'scope_errors':[{'text':r['text'],'expected':r['scope'],'predicted':p} for r,p in zip(dataset,p_scope) if r['scope']!=p][:30], 'category_errors':[{'text':r['text'],'expected':r['category'],'predicted':p} for r,p in zip(relevant,p_cat) if r['category']!=p][:40]}

with (ROOT/'data/manual_challenge.csv').open(encoding='utf-8-sig',newline='') as f:
    challenge=list(csv.DictReader(f))
for r in challenge:r['scope']='out' if r['category']=='out_of_scope' else 'it'
report={'counts':{'total':len(rows),'train':len(train),'validation':len(val),'challenge':len(challenge)},'validation':evaluate(val),'challenge':evaluate(challenge),'disclaimer':'Synthetic templated data; challenge examples are independent authored phrases, not production performance.'}
(ROOT/'models').mkdir(exist_ok=True)
joblib.dump({'scope':scope,'category':tech,'version':'v3-local-ml'},ROOT/'models/incidentlens_models.joblib',compress=3)
(ROOT/'models/metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
for name in ('validation','challenge'):
    print(name,'scope accuracy:',round(report[name]['scope']['accuracy'],3),'category accuracy:',round(report[name]['category']['accuracy'],3))
print('Model saved in models/incidentlens_models.joblib')
