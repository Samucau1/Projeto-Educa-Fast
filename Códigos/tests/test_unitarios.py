"""Unit tests: no app factory, engine connection or installation database."""
import io
import tempfile
import unittest
from pathlib import Path
from datetime import date
from unittest.mock import patch

from ambiente_teste import configurar_banco_testes
configurar_banco_testes()
from cryptography.fernet import InvalidToken
from flask import Flask
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge
from app.auth import normalize_role
from app.crypto import cipher, encrypt, decrypt, cpf_index, EncryptedDate, FILE_PREFIX
from app.security import local_return_path, save_upload, StorageFull


class UnitariosTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def test_role_normalization(self):
        self.assertEqual(normalize_role('  PROFESSOR '), 'professor')
        self.assertEqual(normalize_role(None), '')

    def test_encryption_randomized_roundtrip_and_tampering(self):
        value = 'Dado pessoal: ação e educação'
        one, two = encrypt(value), encrypt(value)
        self.assertNotEqual(one, two)
        self.assertNotIn(value, one)
        self.assertEqual(decrypt(one), value)
        raw = bytearray(one.encode('ascii')); raw[-10] ^= 1
        with self.assertRaises((InvalidToken, ValueError)):
            decrypt(raw.decode('ascii'))

    def test_cpf_index_normalizes_format_without_exposing_digits(self):
        self.assertEqual(cpf_index('123.456.789-00'), cpf_index('12345678900'))
        self.assertNotEqual(cpf_index('12345678900'), cpf_index('12345678901'))
        self.assertNotIn('12345678900', cpf_index('12345678900'))
        self.assertIsNone(cpf_index(None))

    def test_date_storage_roundtrip_and_null(self):
        column = EncryptedDate()
        value = date(2010, 2, 3)
        encrypted = column.process_bind_param(value, None)
        self.assertEqual(column.process_result_value(encrypted, None), value)
        self.assertIsNone(column.process_result_value(None, None))

    def test_local_redirects_preserve_query(self):
        with self.app.test_request_context():
            self.assertEqual(local_return_path('/aluno?aba=documentos#recentes'), '/aluno?aba=documentos#recentes')
            self.assertIsNone(local_return_path(''))

    def test_external_and_malformed_redirects_rejected(self):
        with self.app.test_request_context():
            for value in ('//evil.example', '//[', '/%2Fevil.example', '/%5cevil.example', '/x%0a', 'https://evil.example'):
                with self.subTest(value=value), self.assertRaises(BadRequest):
                    local_return_path(value)

    def test_upload_stream_encryption_size_and_quota_cleanup(self):
        with tempfile.TemporaryDirectory() as folder, self.app.app_context():
            self.app.config.update(UPLOAD_FOLDER=folder, MAX_UPLOAD_BYTES=8, UPLOAD_QUOTA_BYTES=1024)
            path = Path(folder)/'ok.bin'
            save_upload(FileStorage(stream=io.BytesIO(b'12345678')), str(path))
            self.assertEqual(cipher().decrypt(path.read_bytes()[len(FILE_PREFIX):]), b'12345678')
            for content, expected in ((b'123456789', RequestEntityTooLarge), (b'x', StorageFull)):
                target = Path(folder)/'rejected.bin'
                if expected is StorageFull:
                    self.app.config['UPLOAD_QUOTA_BYTES'] = 1
                with self.assertRaises(expected):
                    save_upload(FileStorage(stream=io.BytesIO(content)), str(target))
                self.assertFalse(target.exists())

    def test_concurrent_photo_removal_during_quota_scan(self):
        import os
        with tempfile.TemporaryDirectory() as folder, self.app.app_context():
            self.app.config.update(UPLOAD_FOLDER=folder, MAX_UPLOAD_BYTES=8, UPLOAD_QUOTA_BYTES=1024)
            old = Path(folder)/'old-photo.png'
            old.write_bytes(b'old')
            original = os.path.getsize
            def removed_between_list_and_stat(path):
                if Path(path) == old:
                    old.unlink()
                    raise FileNotFoundError(path)
                return original(path)
            with patch('app.security.os.path.getsize',side_effect=removed_between_list_and_stat):
                target=Path(folder)/'new-photo.png'
                save_upload(FileStorage(stream=io.BytesIO(b'new')),str(target))
            self.assertEqual(cipher().decrypt(target.read_bytes()[len(FILE_PREFIX):]), b'new')


if __name__ == '__main__':
    unittest.main()
