import unittest
from tests.sample_pb2 import MessageOfTypes, extDouble, extString, NestedExtension
from protobuf_to_dict import protobuf_to_dict, dict_to_protobuf
from parameterized import parameterized
import base64
import nose.tools
import json

_CLASS_KEY='class_name'

class Test(unittest.TestCase):
    @parameterized.expand([
        [True], [False]
    ])
    def test_basics(self, add_class_metadata):
        m = self.populate_MessageOfTypes()
        d = protobuf_to_dict(m, add_class_metadata=add_class_metadata)
        self.compare(m, d, ['nestedRepeated'], add_class_metadata=add_class_metadata)

        m2 = dict_to_protobuf(MessageOfTypes, d)
        assert m == m2

    @parameterized.expand([
        [True], [False]
    ])
    def test_use_enum_labels(self, add_class_metadata):
        m = self.populate_MessageOfTypes()
        d = protobuf_to_dict(m, use_enum_labels=True, add_class_metadata=add_class_metadata)
        self.compare(m, d, ['enm', 'enmRepeated', 'nestedRepeated'], add_class_metadata=add_class_metadata)
        assert d['enm'] == 'C'
        assert d['enmRepeated'] == ['A', 'C']

        m2 = dict_to_protobuf(MessageOfTypes, d)
        assert m == m2

        d['enm'] = 'MEOW'
        with nose.tools.assert_raises(KeyError):
            dict_to_protobuf(MessageOfTypes, d)

        d['enm'] = 'A'
        d['enmRepeated'] = ['B']
        dict_to_protobuf(MessageOfTypes, d)

        d['enmRepeated'] = ['CAT']
        with nose.tools.assert_raises(KeyError):
            dict_to_protobuf(MessageOfTypes, d)

    @parameterized.expand([
        [True], [False]
    ])
    def test_repeated_enum(self, add_class_metadata):
        m = self.populate_MessageOfTypes()
        d = protobuf_to_dict(m, use_enum_labels=True, add_class_metadata=add_class_metadata)
        self.compare(m, d, ['enm', 'enmRepeated', 'nestedRepeated'], add_class_metadata=add_class_metadata)
        assert d['enmRepeated'] == ['A', 'C']

        m2 = dict_to_protobuf(MessageOfTypes, d)
        assert m == m2

        d['enmRepeated'] = ['MEOW']
        with nose.tools.assert_raises(KeyError):
            dict_to_protobuf(MessageOfTypes, d)

    @parameterized.expand([
        [True], [False]
    ])
    def test_nested_repeated(self, add_class_metadata):
        m = self.populate_MessageOfTypes()
        m.nestedRepeated.extend([MessageOfTypes.NestedType(req=str(i)) for i in range(10)])

        d = protobuf_to_dict(m, add_class_metadata=add_class_metadata)
        self.compare(m, d, exclude=['nestedRepeated'], add_class_metadata=add_class_metadata)
        if not add_class_metadata:
            assert d['nestedRepeated'] == [{'req': str(i)} for i in range(10)]
        else:
            assert d['nestedRepeated'] == [{'req': str(i),_CLASS_KEY:'NestedType'} for i in range(10)]

        m2 = dict_to_protobuf(MessageOfTypes, d)
        assert m == m2

    @parameterized.expand([
        [True], [False]
    ])
    def test_reverse(self, add_class_metadata):
        m = self.populate_MessageOfTypes()
        m2 = dict_to_protobuf(MessageOfTypes, protobuf_to_dict(m, add_class_metadata=add_class_metadata))
        assert m == m2
        m2.dubl = 0
        assert m2 != m

    @parameterized.expand([
        [True], [False]
    ])
    def test_incomplete(self, add_class_metadata):
        m = self.populate_MessageOfTypes()
        d = protobuf_to_dict(m, add_class_metadata=add_class_metadata)
        d.pop('dubl')
        m2 = dict_to_protobuf(MessageOfTypes, d)
        assert m2.dubl == 0
        assert m != m2

    @parameterized.expand([
        [True], [False]
    ])
    def test_pass_instance(self, add_class_metadata):
        m = self.populate_MessageOfTypes()
        d = protobuf_to_dict(m, add_class_metadata=add_class_metadata)
        d['dubl'] = 1
        m2 = dict_to_protobuf(m, d)
        assert m is m2
        assert m.dubl == 1

    @parameterized.expand([
        [True], [False]
    ])
    def test_strict(self, add_class_metadata):
        m = self.populate_MessageOfTypes()
        d = protobuf_to_dict(m, add_class_metadata=add_class_metadata)
        d['meow'] = 1
        with nose.tools.assert_raises(KeyError):
            m2 = dict_to_protobuf(MessageOfTypes, d)
        m2 = dict_to_protobuf(MessageOfTypes, d, strict=False)
        assert m == m2

    def populate_MessageOfTypes(self):
        m = MessageOfTypes()
        m.dubl = 1.7e+308
        m.flot = 3.4e+038
        m.i32 = 2 ** 31 - 1 # 2147483647 #
        m.i64 = 2 ** 63 - 1 #0x7FFFFFFFFFFFFFFF
        m.ui32 = 2 ** 32 - 1
        m.ui64 = 2 ** 64 - 1
        m.si32 = -1 * m.i32
        m.si64 = -1 * m.i64
        m.f32 = m.i32
        m.f64 = m.i64
        m.sf32 = m.si32
        m.sf64 = m.si64
        m.bol = True
        m.strng = "string"
        m.byts = b'\n\x14\x1e'
        assert len(m.byts) == 3, len(m.byts)
        m.nested.req = "req"
        m.enm = MessageOfTypes.C #@UndefinedVariable
        m.enmRepeated.extend([MessageOfTypes.A, MessageOfTypes.C])
        m.range.extend(range(10))
        return m

    def compare(self, m, d, exclude=None, add_class_metadata=False):
        i = 0
        exclude = ['byts', 'nested', _CLASS_KEY] + (exclude or [])
        for i, field in enumerate(MessageOfTypes.DESCRIPTOR.fields): #@UndefinedVariable
            if field.name not in exclude:
                assert field.name in d, field.name
                assert d[field.name] == getattr(m, field.name), (field.name, d[field.name])
        assert i > 0
        assert m.byts == base64.b64decode(d['byts'])
        print(d)
        if add_class_metadata:
            assert d['nested'] == {'req': m.nested.req, _CLASS_KEY : 'NestedType'}
        else:
            assert d['nested'] == {'req': m.nested.req}

    @parameterized.expand([
        [True], [False]
    ])
    def test_extensions(self, add_class_metadata):
        m = MessageOfTypes()

        primitives = {extDouble: 123.4, extString: "string", NestedExtension.extInt: 4}

        for key, value in primitives.items():
            m.Extensions[key] = value
        m.Extensions[NestedExtension.extNested].req = "nested"

        # Confirm compatibility with JSON serialization
        res = json.loads(json.dumps(protobuf_to_dict(m, add_class_metadata=add_class_metadata)))
        assert '___X' in res
        exts = res['___X']
        assert set(exts.keys()) == set([str(f.number) for f, _ in m.ListFields() if f.is_extension])
        for key, value in primitives.items():
            assert exts[str(key.number)] == value
        assert exts[str(NestedExtension.extNested.number)]['req'] == 'nested'

        deser = dict_to_protobuf(MessageOfTypes, res)
        assert deser
        for key, value in primitives.items():
            assert deser.Extensions[key] == m.Extensions[key]
        assert deser.Extensions[NestedExtension.extNested].req == m.Extensions[NestedExtension.extNested].req
