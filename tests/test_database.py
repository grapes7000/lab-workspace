import os,tempfile,unittest,importlib
class DatabaseTests(unittest.TestCase):
 def test_combined_database_preserves_writing_and_lab_records(self):
  with tempfile.TemporaryDirectory() as d:
   os.environ['LAB_WORKSPACE_DATA_DIR']=d
   import lab_workspace.core.config as config;importlib.reload(config)
   import lab_workspace.data.database as database;importlib.reload(database)
   db=database.Database();db.save_text('scratchpad','draft');m=db.save_material({'name':'Water','formula':'H2O'});s=db.save_sample({'name':'Fuel A','sample_type':'Gasoline'})
   self.assertEqual(len(db.search('materials','Water')),1);self.assertEqual(len(db.search('samples','Fuel')),1)
   self.assertEqual(db.get_text('scratchpad'),'draft');self.assertTrue(m.startswith('MAT-'));self.assertTrue(s.startswith('SMP-'))
   db.save_sample({'code':s,'name':'Fuel B','sample_type':'Gasoline'})
   self.assertEqual(db.search('samples','Fuel B')[0]['name'],'Fuel B')
   first=db.record_deleted_fragment('scratchpad','first',0);second=db.record_deleted_fragment('scratchpad','second',4)
   db.mark_fragment_recovered(first)
   self.assertEqual([(row['id'],row['fragment']) for row in db.unrecovered_deleted_fragments('scratchpad')],[(second,'second')])
   with self.assertRaises(ValueError):db.next_code('samples; DROP TABLE samples','SMP')
if __name__=='__main__':unittest.main()
