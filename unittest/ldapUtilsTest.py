import unittest
import sys
sys.path.append('../src/lib')
import json
import backend_ldap_utils as ldap
import backend_utils as u
class backendLdapCase(unittest.TestCase):
    def test01_ldapconnect(self):
        config=u.read_config('./files_backend_utils/config1.conf')
        data=u.get_config()
        l=ldap.connect_ldap(data['host'],data['dn'],data['password'])
        self.assertNotEqual(l,1)

    def test02_composedn(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        entity = u.readjsonfile("./files_ad_utils/identity1.json")
        dn=ldap.compose_dn(entity)
        self.assertEqual(dn,'uid=omaton,ou=adm,ou=PERSONNES,dc=lyon,dc=archi,dc=fr')
    def test03_composedn_template(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        u.__CONFIG__.set('config', 'dnTemplate', 'cn={{e.cn}},{{branch}},ou=myspecialbranch,{{config.base}}')
        ldap.set_config(config)
        entity = u.readjsonfile("./files_ad_utils/identity1.json")
        dn = ldap.compose_dn(entity)
        self.assertEqual(dn, 'cn=Maton Olivier,ou=adm,ou=myspecialbranch,dc=lyon,dc=archi,dc=fr')

    def test04_compose_dn_otherpopulation(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        config.set('config', 'branchFortest', 'ou=test')
        ldap.set_config(config)
        entity = u.readjsonfile("./files_ad_utils/identity1.json")
        entity['payload']['identity']['identity']['inetOrgPerson']['departmentNumber']=['test']
        dn = ldap.compose_dn(entity)
        self.assertEqual(dn, 'uid=omaton,ou=test,ou=PERSONNES,dc=lyon,dc=archi,dc=fr')

    def test05_compose_dn_nobranch(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        entity = u.readjsonfile("./files_ad_utils/identity1.json")
        entity['payload']['identity']['identity']['inetOrgPerson']['departmentNumber']=['test']
        dn = ldap.compose_dn(entity)
        self.assertEqual(dn, 'uid=omaton,ou=PERSONNES,dc=lyon,dc=archi,dc=fr')

    def test06_testrdn(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        entity = u.readjsonfile("./files_ad_utils/identity1.json")
        rdn = ldap.compose_rdn(entity)
        self.assertEqual(rdn, 'uid=omaton')
        u.__CONFIG__.set('config', 'rdnAttribute', 'cn')
        rdn = ldap.compose_rdn(entity)
        self.assertEqual(rdn, 'cn=Maton Olivier')

    def test07_dnsuperior(self):
        self.assertEqual(ldap.dn_superior("uid=omaton,ou=PERSONNES,dc=lyon,dc=archi,dc=fr"),"ou=PERSONNES,dc=lyon,dc=archi,dc=fr")

    def test08_make_objectclass(self):
        entity = u.readjsonfile("./files_ad_utils/identity1.json")
        test=u.make_objectclass(entity,[])
        x=1
        self.assertEqual(len(test),6)

    def test09_upsertEntry(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        l = ldap.connect_ldap(data['host'], data['dn'], data['password'])
        entity = u.readjsonfile("./files_ad_utils/identity1.json")

        x=ldap.upsert_entry(l,entity)
        result=json.loads(x)
        self.assertEqual(result['status'],0)
        self.assertEqual(result['message'], "Entree uid=omaton,ou=adm,ou=PERSONNES,dc=lyon,dc=archi,dc=fr add")

    def test10_upsertMod(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        l = ldap.connect_ldap(data['host'], data['dn'], data['password'])
        entity = u.readjsonfile("./files_ad_utils/identity1.json")
        entity['payload']['identity']['identity']['inetOrgPerson']['mail']='aa@aa.com'
        x = ldap.upsert_entry(l, entity)
        result = json.loads(x)
        self.assertEqual(result['status'], 0)
        self.assertEqual(result['message'], "Entree uid=omaton,ou=adm,ou=PERSONNES,dc=lyon,dc=archi,dc=fr mod")

    def test11_move_entry(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        l = ldap.connect_ldap(data['host'], data['dn'], data['password'])
        entity = u.readjsonfile("./files_ad_utils/identity1.json")
        entity['payload']['identity']['identity']['inetOrgPerson']['departmentNumber'] = ['esn']
        x = ldap.upsert_entry(l, entity)
        result = json.loads(x)
        self.assertEqual(result['status'], 0)
        self.assertEqual(result['message'], "Entree uid=omaton,ou=esn,ou=PERSONNES,dc=lyon,dc=archi,dc=fr rename")

    def test12_initpassword(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        l = ldap.connect_ldap(data['host'], data['dn'], data['password'])
        entity = u.readjsonfile("./files_ad_utils/resetpassword.json")
        x=ldap.reset_entity_password(l,entity)
        result = json.loads(x)
        self.assertEqual(result['status'], 0)
        self.assertEqual(result['message'], "Password for omaton changed")

    def test15_testpassword(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        ## test du mot de passe
        l1 = ldap.connect_ldap(data['host'], 'uid=omaton,ou=esn,ou=PERSONNES,dc=lyon,dc=archi,dc=fr','Abbert1xIEIIE88!')
        self.assertNotEqual(l1,1)

    def test16_test_wrongpassword(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        ## test du mot de passe
        l1 = ldap.connect_ldap(data['host'], 'uid=omaton,ou=esn,ou=PERSONNES,dc=lyon,dc=archi,dc=fr',
                               'xx')
        self.assertEqual(l1, 1)

    def test20_changepassword(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        l = ldap.connect_ldap(data['host'], data['dn'], data['password'])
        entity = u.readjsonfile("./files_ad_utils/changepassword_true.json")
        x = ldap.change_entity_password(l, entity)
        result = json.loads(x)
        self.assertEqual(result['status'], 0)
        self.assertEqual(result['message'], "Password for omaton changed")

    def test21_testpassword(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        ## test du mot de passe
        l1 = ldap.connect_ldap(data['host'], 'uid=omaton,ou=esn,ou=PERSONNES,dc=lyon,dc=archi,dc=fr','AbCx34IddWZE1!')
        self.assertNotEqual(l1,1)

    def test22_testoldpassword(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        ## test du mot de passe
        l1 = ldap.connect_ldap(data['host'], 'uid=omaton,ou=esn,ou=PERSONNES,dc=lyon,dc=archi,dc=fr',
                               'Abbert1xIEIIE88!')
        self.assertEqual(l1, 1)

    def test23_changepassword_wrong(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        l = ldap.connect_ldap(data['host'], data['dn'], data['password'])
        entity = u.readjsonfile("./files_ad_utils/changepassword_true.json")
        x = ldap.change_entity_password(l, entity)
        result = json.loads(x)
        self.assertEqual(result['status'], 1)

    def test24_activation_entity(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        l = ldap.connect_ldap(data['host'], data['dn'], data['password'])
        entity = u.readjsonfile("./files_ad_utils/identity1.json")
        x=ldap.activate_entry(l,entity,True)
        result = json.loads(x)
        self.assertEqual(result['status'], 0)
        self.assertEqual(result['message'],"Identity enabled")

    def test24_desactivation_entity(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        l = ldap.connect_ldap(data['host'], data['dn'], data['password'])
        entity = u.readjsonfile("./files_ad_utils/identity1.json")
        x=ldap.activate_entry(l,entity,False)
        result = json.loads(x)
        self.assertEqual(result['status'], 0)
        self.assertEqual(result['message'],"Identity disabled")
    def test25_eduperson(self):
        config = u.read_config('./files_backend_utils/configeal.conf')
        ldap.set_config(config)
        data = u.get_config()
        l = ldap.connect_ldap(data['host'], data['dn'], data['password'])
        entity = u.readjsonfile("./files_ad_utils/edupersonTest.json")
        x = ldap.upsert_entry(l, entity)
        result = json.loads(x)
        self.assertEqual(result['status'], 0)
        self.assertEqual(result['message'], "Entree uid=ddoloty,ou=adm,ou=PERSONNES,dc=lyon,dc=archi,dc=fr mod")
    def test26_delete_entry(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        l = ldap.connect_ldap(data['host'], data['dn'], data['password'])
        entity = u.readjsonfile("./files_ad_utils/identity1.json")
        x= ldap.delete_entity(l, entity)
        result = json.loads(x)
        self.assertEqual(result['status'], 0)
        self.assertEqual(result['message'], "user : uid=omaton,ou=esn,ou=PERSONNES,dc=lyon,dc=archi,dc=fr deleted")

    def test99_delete_entry(self):
        config = u.read_config('./files_backend_utils/config1.conf')
        ldap.set_config(config)
        data = u.get_config()
        l = ldap.connect_ldap(data['host'], data['dn'], data['password'])
        entity = u.readjsonfile("./files_ad_utils/identity1.json")
        x= ldap.delete_entity(l, entity)
        result = json.loads(x)
        self.assertEqual(result['status'], 0)
        self.assertEqual(result['message'], "user : uid=omaton,ou=esn,ou=PERSONNES,dc=lyon,dc=archi,dc=fr deleted")

if __name__ == '__main__':
    unittest.main()
