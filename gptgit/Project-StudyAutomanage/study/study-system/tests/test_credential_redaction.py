import unittest

from analyzer.render import redact


class CredentialRedactionTests(unittest.TestCase):
    def test_abbreviated_password_commands_hide_arguments(self):
        for command in ('en sec', 'enable sec', 'en secret', 'enable secret',
                        'pass', 'pw', 'password', 'passwd', 'vtp password'):
            with self.subTest(command=command):
                self.assertEqual(redact(command+' test-value'), command+' [인증값 숨김]')

    def test_noncredential_configuration_is_preserved(self):
        value = 'line vty 0 2\nlogin\ninterface fa0/0\nip address 192.168.1.1 255.255.255.0'
        self.assertEqual(redact(value), value)
