"""Firebase outages must not be mistaken for invalid session credentials."""
import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask, session
from app.services import firebase_service as service


class FirebaseSessionErrorsTests(unittest.TestCase):
    def test_session_error_classification(self):
        app = Flask(__name__)
        app.secret_key = 'isolated-test-session-signing-key'
        timestamp = service.now()
        user = SimpleNamespace(id=1, session_version=1, firebase_uid='test-uid', email='test@example.com')
        record = SimpleNamespace(user_id=1, user_version=1,
            expires_at=timestamp + timedelta(days=1),
            token_expires_at=timestamp + timedelta(hours=1),
            checked_at=timestamp - timedelta(minutes=6),
            authenticated_at=timestamp, encrypted_tokens='test-ciphertext')
        errors = [service.FirebaseError('Unavailable', status=503),
                  service.FirebaseError('Revoked', status=401), ValueError('Malformed'),
                  service.InvalidToken(), KeyError('missing'), TypeError('Invalid')]
        for error in errors:
            with self.subTest(error=type(error).__name__, status=getattr(error, 'status', None)):
                database = MagicMock()
                database.session.get.return_value = record
                database.session.execute.return_value.scalar_one_or_none.return_value = record
                cipher = MagicMock()
                cipher.decrypt.return_value = b'test-id-token'
                with app.test_request_context(), patch.object(service, 'db', database), \
                        patch.object(service, '_cipher', return_value=cipher), \
                        patch.object(service, 'account_record', side_effect=error):
                    session['firebase_session_id'] = 'test-session'
                    if isinstance(error, service.FirebaseError) and error.status == 503:
                        with self.assertRaises(service.FirebaseError):
                            service.session_valid(user)
                    else:
                        self.assertFalse(service.session_valid(user))
                    database.session.commit.assert_not_called()
