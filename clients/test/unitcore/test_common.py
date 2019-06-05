import libyang
from yangvoodoo.Common import Utils, PlainIterator, PlainObject
from mock import Mock
import unittest


class test_common(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

    def test_regex(self):

        expected_match_result = [('/', 'integrationtest:sf', "[abcABC='val1'][abc='sdf']")]

        input = ("/integrationtest:sf/integrationtest:sf/abc:asd[abcABC='val1'][abc='sdf']/"
                 "integrationtest:sf/integrationtest:sf/integrationtest:sf[abcABC='val1'][abc='sdf']")
        result = Utils.LAST_LEAF_AND_PREDICTAES.findall(input)
        self.assertEqual(result[0][1], expected_match_result[0][1])
        self.assertEqual(result[0][2], expected_match_result[0][2])

        input = "/integrationtest:sf[abcABC='val1'][abc='sdf']"
        self.assertEqual(Utils.LAST_LEAF_AND_PREDICTAES.findall(input), expected_match_result)

        # Invalid silly inputs
        expected_no_match_result = []

        input = "/integratio\"ntest:sf[abcABC='val1'][abc='sdf']"
        self.assertEqual(Utils.LAST_LEAF_AND_PREDICTAES.findall(input), expected_no_match_result)

        input = "/inte]gratio[ntest:sf[abcABC='val1'][abc='sdf']"
        self.assertEqual(Utils.LAST_LEAF_AND_PREDICTAES.findall(input), expected_no_match_result)

        input = "[key1=\"va'''][]][][][][][sadasdl1\"]"
        result = Utils.PREDICATE_KEY_VALUES_DOUBLE.findall(input)
        self.assertEqual(result, [('key1', "va'''][]][][][][][sadasdl1")])

        input = '[key1="val1"][key2="val2"]'
        result = Utils.PREDICATE_KEY_VALUES_DOUBLE.findall(input)
        self.assertEqual(result, [('key1', 'val1'), ('key2', 'val2')])

        input = '[key1="val1"][key2="val2"]'
        result = Utils.PREDICATE_KEY_VALUES_SINGLE.findall(input)
        self.assertEqual(result, [])

        input = "[KEY1='val1'][key2='val2']"
        result = Utils.PREDICATE_KEY_VALUES_SINGLE.findall(input)
        self.assertEqual(result, [('KEY1', 'val1'), ('key2', 'val2')])

        input = "[KeY1='val1'][abc=\"sdf\"][abc3ABC='val3']"
        result = Utils.PREDICATE_KEY_VALUES_SINGLE.findall(input)
        self.assertEqual(result, [('KeY1', 'val1'), ('abc3ABC', 'val3')])

        result = Utils.PREDICATE_KEY_VALUES_DOUBLE.findall(input)
        self.assertEqual(result, [('abc', 'sdf')])

        input = "[KeY1='val1'][abc=\"sdf\"][abc3ABC='val3']"
        result = Utils.FIND_KEYS.findall(input)
        self.assertEqual(result, ['KeY1', 'abc', 'abc3ABC'])

        input = "/integrationtest:web/bands[name='Longpigs']/gigs[year='1999'][month='9'][day='1'][venue='SHU Nelson Mandella'][location='Sheffield']"
        expected_match_result = [("/integrationtest:web/bands[name='Longpigs']/",
                                  'gigs',
                                  "[year='1999'][month='9'][day='1'][venue='SHU Nelson "
                                  "Mandella'][location='Sheffield']")]
        self.assertEqual(Utils.LAST_LEAF_AND_PREDICTAES.findall(input), expected_match_result)

    def test_decoding_xpath(self):
        input = "/abc:xyz/abc:abc[KeY1='val1'][abc=\"sdf\"][abc3ABC='val3']"

        # Act
        result = Utils.decode_xpath_predicate(input)

        # Assert
        expected_result = ("/abc:xyz/abc:abc",
                           ('KeY1', 'abc', 'abc3ABC'),
                           ('val1', 'sdf', 'val3')
                           )

        self.assertEqual(result, expected_result)

        input = "/abc:abc[KeY1='val1']"

        # Act
        result = Utils.decode_xpath_predicate(input)

        # Assert
        expected_result = ("/abc:abc",
                           ('KeY1',),
                           ('val1',)
                           )

        self.assertEqual(result, expected_result)

        # Act
        input = "/integrationtest:web/bands[name='Longpigs']/gigs[year='1999'][month='9'][day='1'][venue='SHU Nelson Mandella'][location='Sheffield']"
        result = Utils.decode_xpath_predicate(input)

        # Assert
        expected_result = ("/integrationtest:web/bands[name='Longpigs']/gigs", ('year', 'month', 'day',
                                                                                'venue', 'location'), ('1999', '9', '1', 'SHU Nelson Mandella', 'Sheffield'))
        self.assertEqual(result, expected_result)

    def test_encode_xpath_predciates(self):
        result = Utils.encode_xpath_predicates('attri-bute', keys=['k1', 'k2'], values=[('v1', 10), ('v2', 10)])
        self.assertEqual(result, "attri-bute[k1='v1'][k2='v2']")

    def test_get_original_name(self):
        # Setup
        context = PlainObject()
        context.module = "module"
        context.schemactx = Mock()
        context.schemactx.find_path = Mock()

        result = Utils.get_original_name('', context, 'attribute')
        self.assertEqual(result, 'attribute')
        context.schemactx.find_path.assert_not_called()

    def test_get_original_name_with_underscore(self):
        # Setup
        node = Mock()
        node.name.return_value = 'attribute-here'
        context = PlainObject()
        context.module = "module"
        context.schemactx = Mock()
        context.schemactx.find_path = Mock()
        context.schemactx.find_path.return_value = PlainIterator([node])

        result = Utils.get_original_name('', context, 'attribute_here')
        self.assertEqual(result, 'attribute-here')

    def test_convert_path_to_schema_path(self):
        result = Utils.convert_path_to_schema_path("/path/abc/def[g='sdf']/xyz/sdf[fdsf='fg']/zzz", 'module')
        expected_result = ("/module:path/module:abc/module:def/module:xyz/module:sdf/module:zzz",
                           "/module:path/module:abc/module:def/module:xyz/module:sdf")
        self.assertEqual(result, expected_result)

        result = Utils.convert_path_to_schema_path("/path/abc/def[g='sdf']", 'module')
        expected_result = ("/module:path/module:abc/module:def", "/module:path/module:abc")
        self.assertEqual(result, expected_result)

        result = Utils.convert_path_to_schema_path("/path/abc", 'module')
        expected_result = ("/module:path/module:abc", "/module:path")
        self.assertEqual(result, expected_result)

        with self.assertRaises(ValueError) as context:
            result = Utils.convert_path_to_schema_path("/path/abc/", 'module')
        self.assertEqual(str(context.exception), "Path is not valid as it ends with a trailing slash. (/path/abc/)")

    def test_convert_path_to_value_path(self):
        result = Utils.convert_path_to_value_path("/path/abc/def[g='sdf']/xyz/sdf[fdsf='fg'][hhhh='hh']/zzz", 'module')
        expected_result = ("/module:path/abc/def[g='sdf']/xyz/sdf[fdsf='fg'][hhhh='hh']/zzz", "/module:path/abc/def[g='sdf']/xyz/sdf")

        self.assertEqual(result, expected_result)

        result = Utils.convert_path_to_value_path("/path/abc/def[g='sdf'][h='sdf']/sdsd", 'module')
        expected_result = ("/module:path/abc/def[g='sdf'][h='sdf']/sdsd", '/module:path/abc/def')
        self.assertEqual(result, expected_result)

        result = Utils.convert_path_to_value_path("/path/abc", 'module')
        expected_result = ("/module:path/abc", "/module:path")
        self.assertEqual(result, expected_result)

        with self.assertRaises(ValueError) as context:
            result = Utils.convert_path_to_value_path("/path/abc/", 'module')
        self.assertEqual(str(context.exception), "Path is not valid as it ends with a trailing slash. (/path/abc/)")
