import sqlite3,json,csv,hashlib
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from lab_workspace.core.config import DB,ensure
SCHEMA="""
CREATE TABLE IF NOT EXISTS documents(key TEXT PRIMARY KEY,current_text TEXT NOT NULL DEFAULT '',updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS document_revisions(id INTEGER PRIMARY KEY,document_key TEXT,text TEXT,created_at TEXT,reason TEXT);
CREATE TABLE IF NOT EXISTS materials(id INTEGER PRIMARY KEY,code TEXT UNIQUE,name TEXT NOT NULL,formula TEXT,mw REAL,density REAL,density_unit TEXT,form TEXT,purity REAL,active_fraction REAL,aliases TEXT,tags TEXT,notes TEXT,created_at TEXT,updated_at TEXT,superseded_at TEXT);
CREATE TABLE IF NOT EXISTS material_revisions(id INTEGER PRIMARY KEY,material_id INTEGER,snapshot_json TEXT,changed_at TEXT,reason TEXT);
CREATE TABLE IF NOT EXISTS samples(id INTEGER PRIMARY KEY,code TEXT UNIQUE,name TEXT NOT NULL,sample_type TEXT,project TEXT,status TEXT,source TEXT,collection_location TEXT,collection_date TEXT,received_date TEXT,fuel_grade TEXT,nominal_ethanol REAL,lot_number TEXT,quantity REAL,quantity_unit TEXT,container TEXT,storage_location TEXT,parent_sample_code TEXT,tags TEXT,notes TEXT,created_at TEXT,updated_at TEXT,superseded_at TEXT);
CREATE TABLE IF NOT EXISTS sample_revisions(id INTEGER PRIMARY KEY,sample_id INTEGER,snapshot_json TEXT,changed_at TEXT,reason TEXT);
CREATE TABLE IF NOT EXISTS test_methods(id INTEGER PRIMARY KEY,code TEXT UNIQUE,name TEXT NOT NULL,fields_json TEXT,active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS test_requests(id INTEGER PRIMARY KEY,code TEXT UNIQUE,sample_code TEXT,method_code TEXT,status TEXT,priority TEXT,assigned_to TEXT,due_date TEXT,notes TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS test_runs(id INTEGER PRIMARY KEY,request_code TEXT,run_code TEXT UNIQUE,status TEXT,operator TEXT,instrument TEXT,completed_at TEXT,notes TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS test_values(id INTEGER PRIMARY KEY,run_code TEXT,field_key TEXT,numeric_value REAL,text_value TEXT,unit TEXT,qualifier TEXT);
CREATE TABLE IF NOT EXISTS calculations(id INTEGER PRIMARY KEY,title TEXT,input_json TEXT,result_json TEXT,markdown TEXT,created_at TEXT,engine_version TEXT);
CREATE TABLE IF NOT EXISTS imports(id INTEGER PRIMARY KEY,filename TEXT,file_hash TEXT,format TEXT,imported_at TEXT,rows_added INTEGER,rows_skipped INTEGER,warnings_json TEXT);
CREATE TRIGGER IF NOT EXISTS no_delete_doc_rev BEFORE DELETE ON document_revisions BEGIN SELECT RAISE(ABORT,'history is append-only'); END;
CREATE TRIGGER IF NOT EXISTS no_delete_mat_rev BEFORE DELETE ON material_revisions BEGIN SELECT RAISE(ABORT,'history is append-only'); END;
CREATE TRIGGER IF NOT EXISTS no_delete_sample_rev BEFORE DELETE ON sample_revisions BEGIN SELECT RAISE(ABORT,'history is append-only'); END;
CREATE TRIGGER IF NOT EXISTS no_delete_calc BEFORE DELETE ON calculations BEGIN SELECT RAISE(ABORT,'history is append-only'); END;
"""
def now():return datetime.now().isoformat(timespec="seconds")
class Database:
 def __init__(self):
  ensure()
  with self.connect() as c:c.executescript(SCHEMA)
  for k in ('scratchpad','final'):
   with self.connect() as c:c.execute("INSERT OR IGNORE INTO documents VALUES(?,?,?)",(k,'',now()))
  self.seed_methods()
 @contextmanager
 def connect(self):
  c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
  try:yield c;c.commit()
  except: c.rollback();raise
  finally:c.close()
 def doc(self,key):
  with self.connect() as c:return c.execute("SELECT current_text FROM documents WHERE key=?",(key,)).fetchone()[0]
 def save_doc(self,key,text,reason='autosave'):
  with self.connect() as c:
   old=c.execute("SELECT current_text FROM documents WHERE key=?",(key,)).fetchone()[0]
   if old==text:return False
   c.execute("UPDATE documents SET current_text=?,updated_at=? WHERE key=?",(text,now(),key));c.execute("INSERT INTO document_revisions(document_key,text,created_at,reason) VALUES(?,?,?,?)",(key,text,now(),reason));return True
 def next_code(self,table,prefix):
  with self.connect() as c:n=c.execute(f"SELECT COALESCE(MAX(id),0)+1 FROM {table}").fetchone()[0]
  return f"{prefix}-{datetime.now().year}-{n:04d}"
 def save_material(self,d):
  code=d.get('code') or self.next_code('materials','MAT');timestamp=now()
  with self.connect() as c:
   existing=c.execute("SELECT * FROM materials WHERE code=?",(code,)).fetchone()
   vals=(d['name'],d.get('formula',''),d.get('mw'),d.get('density'),d.get('density_unit','g/mL'),d.get('form','Other'),d.get('purity',100),d.get('active_fraction',100),d.get('aliases',''),d.get('tags',''),d.get('notes',''),timestamp,code)
   if existing:
    c.execute("INSERT INTO material_revisions(material_id,snapshot_json,changed_at,reason) VALUES(?,?,?,?)",(existing['id'],json.dumps(dict(existing)),timestamp,'updated'))
    c.execute("UPDATE materials SET name=?,formula=?,mw=?,density=?,density_unit=?,form=?,purity=?,active_fraction=?,aliases=?,tags=?,notes=?,updated_at=? WHERE code=?",vals)
   else:c.execute("INSERT INTO materials(code,name,formula,mw,density,density_unit,form,purity,active_fraction,aliases,tags,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(code,*vals[:-1],timestamp))
  return code
 def save_sample(self,d):
  code=d.get('code') or self.next_code('samples','SMP');timestamp=now()
  cols=['name','sample_type','project','status','source','collection_location','collection_date','received_date','fuel_grade','nominal_ethanol','lot_number','quantity','quantity_unit','container','storage_location','parent_sample_code','tags','notes']
  values=[d.get(x,'') for x in cols]
  with self.connect() as c:
   existing=c.execute("SELECT * FROM samples WHERE code=?",(code,)).fetchone()
   if existing:
    c.execute("INSERT INTO sample_revisions(sample_id,snapshot_json,changed_at,reason) VALUES(?,?,?,?)",(existing['id'],json.dumps(dict(existing)),timestamp,'updated'))
    c.execute(f"UPDATE samples SET {','.join(x+'=?' for x in cols)},updated_at=? WHERE code=?",(*values,timestamp,code))
   else:c.execute(f"INSERT INTO samples(code,{','.join(cols)},created_at,updated_at) VALUES(? ,{','.join('?' for _ in cols)},?,?)",(code,*values,timestamp,timestamp))
  return code
 def search(self,table,term=''):
  allowed={'materials':('name','formula','aliases','tags','notes','code'),'samples':('name','sample_type','project','source','fuel_grade','lot_number','tags','notes','code'),'test_requests':('code','sample_code','method_code','status','assigned_to','notes')}
  cols=allowed[table];pattern=f"%{term}%"
  with self.connect() as c:return c.execute(f"SELECT * FROM {table} WHERE {' OR '.join(x+' LIKE ?' for x in cols)} ORDER BY id DESC",(pattern,)*len(cols)).fetchall()
 def methods(self):
  with self.connect() as c:return c.execute("SELECT * FROM test_methods WHERE active=1 ORDER BY name").fetchall()
 def seed_methods(self):
  methods=[('DENSITY','Density',[{'key':'density','name':'Density','type':'number','unit':'kg/m3'},{'key':'temperature','name':'Test temperature','type':'number','unit':'C'}]),('DISTILLATION','Distillation',[{'key':x.lower(),'name':x,'type':'number','unit':'C'} for x in ['IBP','T10','T50','T90','FBP']]),('FTIR','FTIR Screening',[{'key':'classification','name':'Classification','type':'text','unit':''},{'key':'notes','name':'Interpretation','type':'text','unit':''}]),('CUSTOM','Custom Test',[{'key':'result','name':'Result','type':'text','unit':''}])]
  with self.connect() as c:
   for code,name,fields in methods:c.execute("INSERT OR IGNORE INTO test_methods(code,name,fields_json) VALUES(?,?,?)",(code,name,json.dumps(fields)))
 def save_request(self,d):
  code=d.get('code') or self.next_code('test_requests','TREQ')
  with self.connect() as c:c.execute("INSERT INTO test_requests(code,sample_code,method_code,status,priority,assigned_to,due_date,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(code,d['sample_code'],d['method_code'],d.get('status','Requested'),d.get('priority','Normal'),d.get('assigned_to',''),d.get('due_date',''),d.get('notes',''),now()))
  return code
 def save_run(self,request_code,method_code,values,meta):
  run=self.next_code('test_runs','RUN')
  with self.connect() as c:
   c.execute("INSERT INTO test_runs(request_code,run_code,status,operator,instrument,completed_at,notes,created_at) VALUES(?,?,?,?,?,?,?,?)",(request_code,run,meta.get('status','Completed'),meta.get('operator',''),meta.get('instrument',''),now(),meta.get('notes',''),now()))
   for v in values:c.execute("INSERT INTO test_values(run_code,field_key,numeric_value,text_value,unit,qualifier) VALUES(?,?,?,?,?,?)",(run,v['field_key'],v.get('numeric_value'),v.get('text_value'),v.get('unit',''),v.get('qualifier','')))
  return run
 def save_calculation(self,title,inputs,result,markdown):
  with self.connect() as c:return c.execute("INSERT INTO calculations(title,input_json,result_json,markdown,created_at,engine_version) VALUES(?,?,?,?,?,?)",(title,json.dumps(inputs),json.dumps(result),markdown,now(),'1.2')).lastrowid
 def export_csv(self,table,path):
  rows=self.search(table,'')
  if not rows:return 0
  with open(path,'w',newline='',encoding='utf-8-sig') as f:
   w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(dict(r) for r in rows)
  return len(rows)
 def import_csv(self,table,path):
  added=skipped=0;warnings=[]
  with open(path,newline='',encoding='utf-8-sig') as f:
   for n,row in enumerate(csv.DictReader(f),2):
    try:
     if table=='materials':
      for k in ('mw','density','purity','active_fraction'):
       row[k]=float(row[k]) if row.get(k) else None
      if not row.get('name'):raise ValueError('name required')
      self.save_material(row)
     else:
      if not row.get('name'):raise ValueError('name required')
      self.save_sample(row)
     added+=1
    except Exception as e:skipped+=1;warnings.append(f"Row {n}: {e}")
  digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
  with self.connect() as c:c.execute("INSERT INTO imports(filename,file_hash,format,imported_at,rows_added,rows_skipped,warnings_json) VALUES(?,?,?,?,?,?,?)",(str(path),digest,'csv',now(),added,skipped,json.dumps(warnings)))
  return added,skipped,warnings
