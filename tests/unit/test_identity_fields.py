"""Identity validation needs no database or external identity provider."""
import unittest

from app.services.auth_service import identity_fields


class IdentityFieldsTests(unittest.TestCase):
    def fields(self, email, **overrides):
        return {'email': email, 'name': '  Ana  ', 'password': 'valid-test-input-123', **overrides}

    def test_normalizes_names_and_addresses(self):
        name, email, _ = identity_fields(self.fields('  ANA+Cafe@Example.COM  '))
        self.assertEqual((name, email), ('Ana', 'ana+cafe@example.com'))

    def test_accepts_existing_email_formats(self):
        for address in ['a@b.c', 'a+b@sub.example.com', 'ñ@dominio.ec', 'a@b..c']:
            with self.subTest(address=address):
                self.assertEqual(identity_fields(self.fields(address))[1], address)

    def test_rejects_malformed_and_oversized_addresses(self):
        for address in ['', '@b.c', 'a@', 'a@b', 'a@.b', 'a@b.', 'a@@b.c',
                        'a b@c.ec', 'a@b\tc.ec', 'a@b\u2003c.ec',
                        'a@' + 'b' * 250 + '.ec', 'a@' + '.' * 10000]:
            with self.subTest(address=address[:30]):
                with self.assertRaisesRegex(ValueError, 'correo válido'):
                    identity_fields(self.fields(address))

    def test_address_length_boundary(self):
        address = 'a@' + 'b' * 250 + '.c'
        self.assertEqual(len(address), 254)
        self.assertEqual(identity_fields(self.fields(address))[1], address)

    def test_preserves_registration_and_login_requirements(self):
        for overrides in [{'password': 'short'}, {'password': None},
                          {'password': 'x' * 257}, {'name': ''}, {'name': 'x' * 121}]:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    identity_fields(self.fields('a@b.c', **overrides))
        self.assertEqual(identity_fields(self.fields('a@b.c', name='', password='short'),
                                         registration=False), ('', 'a@b.c', 'short'))
