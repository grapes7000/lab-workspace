import os,tempfile,unittest,importlib
class DatabaseTests(unittest.TestCase):
 def test_material_sample_and_request(self):
  with tempfile.TemporaryDirectory() as d:
   os.environ['LAB_WORKSPACE_DATA_DIR']=d
   import lab_workspace.core.config as config;importlib.reload(config)
   import lab_workspace.data.database as database;importlib.reload(database)
   db=database.Database();m=db.save_material({'name':'Water','formula':'H2O'});s=db.save_sample({'name':'Fuel A','sample_type':'Gasoline'});r=db.save_request({'sample_code':s,'method_code':'DENSITY'})
   self.assertEqual(len(db.search('materials','Water')),1);self.assertEqual(len(db.search('samples','Fuel')),1);self.assertTrue(r.startswith('TREQ-'))
if __name__=='__main__':unittest.main()
