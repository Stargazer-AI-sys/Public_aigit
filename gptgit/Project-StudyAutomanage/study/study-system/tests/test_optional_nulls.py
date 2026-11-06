import copy
import unittest

from analyzer.openai_provider import omit_optional_nulls


class OptionalNullTests(unittest.TestCase):
    def setUp(self):
        self.schema = {'type': 'object', 'required': ['required_block'], 'properties': {
            'theory': {'type': 'object', 'minProperties': 1, 'properties': {
                'definitions': {'type': 'array', 'minItems': 1},
                'principles': {'type': 'array', 'minItems': 1}}},
            'required_block': {'type': 'object', 'minProperties': 1,
                               'properties': {'optional': {'type': 'string'}}}}}

    def normalize(self, value):
        return omit_optional_nulls(value, self.schema, self.schema)

    def test_optional_container_with_only_null_descendants_is_omitted(self):
        value = {'theory': {'definitions': None, 'principles': None}}
        original = copy.deepcopy(value)
        self.assertEqual(self.normalize(value), {})
        self.assertEqual(value, original)

    def test_real_content_is_retained(self):
        self.assertEqual(self.normalize({'theory': {'definitions': ['definition'], 'principles': None}}),
                         {'theory': {'definitions': ['definition']}})

    def test_explicit_empty_objects_and_lists_are_not_hidden(self):
        self.assertEqual(self.normalize({'theory': {}}), {'theory': {}})
        self.assertEqual(self.normalize({'theory': {'definitions': []}}), {'theory': {'definitions': []}})

    def test_required_container_and_unknown_null_are_not_hidden(self):
        self.assertEqual(self.normalize({'required_block': {'optional': None}}), {'required_block': {}})
        self.assertEqual(self.normalize({'theory': {'unknown': None}}), {'theory': {'unknown': None}})

    def test_nested_optional_null_container_is_omitted(self):
        self.schema['properties']['nested'] = {'type': 'object', 'properties': {'theory': self.schema['properties']['theory']}}
        self.assertEqual(self.normalize({'nested': {'theory': {'definitions': None}}}), {})
