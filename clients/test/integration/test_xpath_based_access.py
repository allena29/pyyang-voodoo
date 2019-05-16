import unittest

import yangvoodoo
import subprocess
import sysrepo as sr
from yangvoodoo import Types

command = 'sysrepocfg --import=../init-data/integrationtest.xml --format=xml --datastore=running integrationtest'
process = subprocess.Popen(["bash"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
(out, err) = process.communicate(command.encode('UTF-8'))
if err:
    raise ValueError('Unable to import data\n%s\n%s' % (out, err))


class test_getdata(unittest.TestCase):

    def setUp(self):
        self.subject = yangvoodoo.DataAccess()
        self.subject.connect('integrationtest')

    def test_delete_and_get(self):
        self.subject.set('/integrationtest:simpleenum', 'A', Types.DATA_ABSTRACTION_MAPPING['ENUM'])
        value = self.subject.get('/integrationtest:simpleenum')
        self.assertEqual(value, 'A')

        self.subject.delete('/integrationtest:simpleenum')

        value = self.subject.get('/integrationtest:simpleenum')
        self.assertEqual(value, None)

    def test_get_leaf(self):
        xpath = "/integrationtest:morecomplex/inner/leaf5"
        self.assertEqual(self.subject.get(xpath), 'Inside')

    def test_set_leaves(self):
        """
        This tests setting leaves with and without commits.

        We can see commits don't persist to startup config.
        """
        xpath = "/integrationtest:morecomplex/inner/leaf5"
        value = "Outside"
        self.subject.set(xpath, value)
        self.assertEqual(self.subject.get(xpath), 'Outside')

        self.subject = yangvoodoo.DataAccess()
        self.subject.connect('integrationtest')

        xpath = "/integrationtest:morecomplex/inner/leaf5"
        self.assertNotEqual(self.subject.get(xpath), 'Outside')

        xpath = "/integrationtest:morecomplex/inner/leaf5"
        value = "Outside"
        self.subject.set(xpath, value)
        self.assertEqual(self.subject.get(xpath), 'Outside')
        self.subject.commit()

        self.subject = yangvoodoo.DataAccess()
        self.subject.connect('integrationtest')

        xpath = "/integrationtest:morecomplex/inner/leaf5"
        self.assertEqual(self.subject.get(xpath), 'Outside')

        xpath = "/integrationtest:morecomplex/inner/leaf5"
        value = "Inside"
        self.subject.set(xpath, value)
        self.subject.commit()

    def test_set_leaves_multiple_transactions(self):
        """
        This tests setting values- here we can see sysrepo doesn't block a commit
        when the data changes.

        We can see commits don't persist to startup config.

        Importantly though, we can see that after subject1 has changed the value from
        Inside to Outside subject2 on it's following get picks up the new value
        instead of what it was when it created the value.
        """
        xpath = "/integrationtest:morecomplex/inner/leaf5"
        value = "Outside"

        self.subject1 = yangvoodoo.DataAccess()
        self.subject1.connect('integrationtest', '../yang', 'a')
        self.subject2 = yangvoodoo.DataAccess()
        self.subject2.connect('integrationtest', '../yang', 'b')

        self.subject1.set(xpath, value)
        self.assertEqual(self.subject1.get(xpath), 'Outside')
        self.subject1.commit()
        self.assertEqual(self.subject2.get(xpath), 'Outside')

        value = 'Middle'
        self.subject2.set(xpath, value)
        self.subject2.commit()
        self.assertEqual(self.subject2.get(xpath), 'Middle')

    def test_leafref(self):
        xpath = "/integrationtest:thing-that-is-leafref"
        valid_value = 'GHI'
        self.subject.set(xpath, valid_value)
        self.subject.commit()

        xpath = "/integrationtest:thing-that-is-leafref"
        invalid_value = 'ZZZ'
        self.subject.set(xpath, invalid_value)

        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError) as context:
            self.subject.commit()
        self.assertEqual(str(context.exception),
                         ("1 Errors occured\n"
                          "Error 0: Leafref \"../thing-to-leafref-against\" of value \"ZZZ\" "
                          "points to a non-existing leaf. (Path: /integrationtest:thing-that-is-leafref)\n"))

        self.subject = yangvoodoo.DataAccess()
        self.subject.connect('integrationtest')

        xpath = "/integrationtest:thing-that-is-a-list-based-leafref"
        valid_value = 'I'
        self.subject.set(xpath, valid_value)
        self.subject.commit()

        valid_value = 'W'
        self.subject.set(xpath, valid_value)
        self.subject.commit()

    def test_non_existing_element(self):
        with self.assertRaises(RuntimeError) as context:
            xpath = "/integrationtest:thing-that-never-does-exist-in-yang"
            self.subject.get(xpath)
        self.assertEqual(str(context.exception), 'Request contains unknown element')

    def test_containers_and_non_existing_data(self):
        with self.assertRaises(yangvoodoo.Errors.NodeHasNoValue) as context:
            xpath = "/integrationtest:morecomplex"
            self.subject.get(xpath)
        self.assertEqual(str(context.exception), 'The node: container at /integrationtest:morecomplex has no value')

        xpath = "/integrationtest:morecomplex/inner"
        value = self.subject.get(xpath)
        self.assertTrue(value)

        xpath = "/integrationtest:simplecontainer"
        value = self.subject.get(xpath)
        self.assertEqual(value, None)

        xpath = "/integrationtest:empty"
        self.subject.set(xpath, None, sr.SR_LEAF_EMPTY_T)

        with self.assertRaises(yangvoodoo.Errors.NodeHasNoValue) as context:
            xpath = "/integrationtest:empty"
            self.subject.get(xpath)
        self.assertEqual(str(context.exception), 'The node: empty-leaf at /integrationtest:empty has no value')

    def test_numbers(self):
        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError) as context:
            xpath = "/integrationtest:bronze/silver/gold/platinum/deep"
            self.subject.set(xpath, 123, sr.SR_UINT16_T)
        self.assertEqual(str(context.exception), "1 Errors occured\nError 0: Invalid argument (Path: None)\n")

        xpath = "/integrationtest:bronze/silver/gold/platinum/deep"
        self.subject.set(xpath, "123", sr.SR_STRING_T)

        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError) as context:
            xpath = "/integrationtest:morecomplex/leaf3"
            self.subject.set(xpath, 123, sr.SR_UINT16_T)
        self.assertEqual(str(context.exception), '1 Errors occured\nError 0: Invalid argument (Path: None)\n')

        xpath = "/integrationtest:morecomplex/leaf3"
        self.subject.set(xpath, 123, sr.SR_UINT32_T)

    def test_other_types(self):
        xpath = "/integrationtest:morecomplex/leaf2"
        value = self.subject.get(xpath)
        self.assertTrue(value)

        xpath = "/integrationtest:morecomplex/leaf2"
        self.subject.set(xpath, False, sr.SR_BOOL_T)

        value = self.subject.get(xpath)
        self.assertFalse(value)

        # this leaf is a union of two different typedef's
        xpath = "/integrationtest:morecomplex/leaf4"
        self.subject.set(xpath, 'A', sr.SR_ENUM_T)

        xpath = "/integrationtest:morecomplex/leaf4"
        self.subject.set(xpath, 23499, sr.SR_UINT32_T)

    def test_lists(self):
        """
        We can choose to create list entries or allow them to be created by setting something deeper.
        <container-and-lists xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest">
          <multi-key-list>
            <A>a</A>
            <B>B</B>
          </multi-key-list>
          <multi-key-list>
            <A>aa</A>
            <B>bb</B>
            <inner>
              <C>C</C>
            </inner>
          </multi-key-list>
        </container-and-lists>
        """

        xpath = "/integrationtest:container-and-lists/multi-key-list[A='a'][B='B']"  # [B='b']"
        self.subject.create(xpath)

        xpath = "/integrationtest:container-and-lists/multi-key-list[A='a'][B='B']"  # [B='b']"
        self.subject.set(xpath,  None, sr.SR_LIST_T)

        xpath = "/integrationtest:container-and-lists/multi-key-list[A='aa'][B='bb']/inner/C"  # [B='b']"
        self.subject.set(xpath,  'cc', sr.SR_STRING_T)

        xpath = "/integrationtest:container-and-lists/multi-key-list[A='xx'][B='xx']/inner/C"  # [B='b']"
        value = self.subject.get(xpath)
        self.assertEqual(value, None)

        # Missing key
        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError) as context:
            xpath = "/integrationtest:twokeylist[primary='true']"
            self.subject.set(xpath,  None, sr.SR_LIST_T)
        self.assertEqual(str(context.exception), '1 Errors occured\nError 0: Invalid argument (Path: None)\n')

        xpath = "/integrationtest:container-and-lists/multi-key-list"
        items = self.subject.gets_unsorted(xpath)
        self.assertNotEqual(items, None)

        expected = [
            ["/integrationtest:container-and-lists/multi-key-list[A='a'][B='B']", 'a', 'B', None],
            ["/integrationtest:container-and-lists/multi-key-list[A='aa'][B='bb']", 'aa', 'bb', 'cc']
        ]

        idx = 0
        for item in items:
            (expected_xpath, expected_a_val, expected_b_val, expected_c_val) = expected[idx]
            self.assertEqual(expected_xpath, item)

            item_xpath = item + "/A"
            self.assertEqual(self.subject.get(item_xpath), expected_a_val)

            item_xpath = item + "/B"
            self.assertEqual(self.subject.get(item_xpath), expected_b_val)

            item_xpath = item + "/inner/C"
            self.assertEqual(self.subject.get(item_xpath), expected_c_val)

            idx = idx + 1
        with self.assertRaises(StopIteration) as context:
            next(items)

        # this test case originally failed because the data did not exist not because it wsan't a list
        # gets() works on leaves.
        # with self.assertRaises(datalayer.NodeNotAList) as context:
        xpath = "/integrationtest:simpleleaf"
        items = self.subject.gets_unsorted(xpath)
        # However if we iterate around the answer we will get
        # each character of the string '/integrationtest:simpleleaf'
        # self.assertEqual(str(context.exception), "The path: /integrationtest:simpleleaf is not a list")

    def test_lists_ordering(self):

        xpath = "/integrationtest:simplelist[simplekey='A']"
        self.subject.create(xpath)

        xpath = "/integrationtest:simplelist[simplekey='Z']"
        self.subject.create(xpath)

        xpath = "/integrationtest:simplelist[simplekey='middle']"
        self.subject.create(xpath)

        xpath = "/integrationtest:simplelist[simplekey='M']"
        self.subject.create(xpath)

        xpath = "/integrationtest:simplelist"

        # GETS is based on user defined order
        items = self.subject.gets_unsorted(xpath)
        expected_results = ["/integrationtest:simplelist[simplekey='A']",
                            "/integrationtest:simplelist[simplekey='Z']",
                            "/integrationtest:simplelist[simplekey='middle']",
                            "/integrationtest:simplelist[simplekey='M']"]
        self.assertEqual(list(items), expected_results)

        # GETS_SORTED is based on xpath sorted order
        items = self.subject.gets_sorted(xpath)
        expected_results = ["/integrationtest:simplelist[simplekey='A']",
                            "/integrationtest:simplelist[simplekey='M']",
                            "/integrationtest:simplelist[simplekey='Z']",
                            "/integrationtest:simplelist[simplekey='middle']"]
        self.assertEqual(list(items), expected_results)