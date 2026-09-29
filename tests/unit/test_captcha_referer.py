"""Fallback metadata uses HTTPS; real local request metadata stays unchanged."""
import io
import json
import unittest
from unittest.mock import patch
from flask import Flask
from app.services.captcha_service import verify


class CaptchaRefererTests(unittest.TestCase):
    def test_fallback_and_local_request(self):
        app = Flask(__name__)
        app.config.update(RECAPTCHA_SITE_KEY='test-site', RECAPTCHA_PROJECT_ID='test-project',
                          RECAPTCHA_API_KEY='test-key', RECAPTCHA_ALLOWED_HOSTS=['localhost'])
        for local_request in (False, True):
            with self.subTest(local_request=local_request):
                context = app.test_request_context(base_url='http://localhost:5000/') if local_request else app.app_context()
                response = io.BytesIO(json.dumps({'tokenProperties': {'valid': True, 'hostname': 'localhost'}}).encode())
                with context, patch('app.services.captcha_service.urlopen', return_value=response) as request:
                    verify('test-token')
                    sent = request.call_args.args[0]
                    self.assertTrue(sent.full_url.startswith('https://recaptchaenterprise.googleapis.com/'))
                    self.assertEqual(sent.get_header('Referer'), 'http://localhost:5000/' if local_request else 'https://localhost/')
