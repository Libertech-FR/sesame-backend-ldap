import sys
sys.path.append('../src/lib')
import unittest
import backend_utils as u

class BackendUtilsCase(unittest.TestCase):
    def test_config(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        self.assertEqual(u.config('host','x'),"1.2.3.4")
        # test cle non existante
        self.assertEqual(u.config('NoExistantKey','x'),'x')
    def test_getConfig(self):
        u.read_config('./files_backend_utils/config1.conf')
        data=u.get_config()
        self.assertEqual(data['host'],"1.2.3.4")
        self.assertEqual(data['user'], "administrateur")
        self.assertEqual(data['base'], "dc=libertest1,dc=fr")
        self.assertEqual(data['backendfor'], "adm,etd,esn")
    def test_returncode(self):
        x=u.returncode(0,"test")
        self.assertEqual(u.returncode(0,"test"),'{"status": 0, "message": "test"}')
        self.assertEqual(u.returncode(1,"Erreur"),'{"status": 1, "message": "Erreur"}')
    def test_is_backend_concerned(self):
        config=u.read_config('./files_backend_utils/config1.conf')
        entry=u.readjsonfile("./files_backend_utils/dummy.json")
        self.assertTrue(type(entry) is dict,'Not a list')
        self.assertFalse(u.is_backend_concerned(entry))
        u.__CONFIG__.set('config','backendfor','esn,adiv')
        self.assertFalse(u.is_backend_concerned(entry))
        u.__CONFIG__.set('config', 'backendfor', 'esn,div')
        self.assertTrue(u.is_backend_concerned(entry))
        # now wit array
        u.__CONFIG__.set('config', 'branchAttr', 'departmentNumber')
        u.__CONFIG__.set('config', 'backendfor', 'esn,etd,adm')
        self.assertFalse(u.is_backend_concerned(entry))
        u.__CONFIG__.set('config', 'backendfor', 'esn,etd,adiv')
        self.assertFalse(u.is_backend_concerned(entry))
        u.__CONFIG__.set('config', 'backendfor', 'esn,div')
        self.assertTrue(u.is_backend_concerned(entry))
        # test backend à vide
        u.__CONFIG__.remove_option('config', 'backendfor')
        x=u.is_backend_concerned(entry)
        self.assertTrue(u.is_backend_concerned(entry))
        # test si branchAttr est vide
        u.__CONFIG__.remove_option('config', 'branchAttr')
        self.assertTrue(u.is_backend_concerned(entry))
    def test_make_entry_array(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        entry = u.readjsonfile("./files_backend_utils/dummy.json")
        entity=u.make_entry_array(entry)
        self.assertEqual(entity['supannEmpId'],"0")
    def test_find_key(self):
        entry = u.readjsonfile("./files_backend_utils/dummy.json")
        self.assertEqual(u.find_key(entry,'supannEntiteAffectationPrincipale'),'div')
        # test clé qui n existe pas
        self.assertEqual(u.find_key(entry, 'abcdef'), '')
if __name__ == '__main__':
    unittest.main()
