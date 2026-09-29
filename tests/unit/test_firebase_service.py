"""Provider boundaries are simulated; cryptography and validation run unchanged."""
import io
import json
import unittest
from contextlib import ExitStack
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError
from flask import Flask, session
from app.services import firebase_service as service


class FirebaseServiceTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.app = Flask(__name__)
        self.app.config.update(SECRET_KEY='isolated-firebase-test-signing-key', AUTH_PROVIDER='firebase',
            FIREBASE_API_KEY='test-api', FIREBASE_PROJECT_ID='test-project', FIREBASE_AUTH_DOMAIN='test.example', FIREBASE_APP_ID='test-app')
        self.stack.enter_context(self.app.test_request_context())
        self.timestamp = service.now().replace(microsecond=0)
        self.mock('now', return_value=self.timestamp)
        self.db = self.mock('db')
        self.audit = self.mock('audit')
        self.profile = dict(uid='uid',email='ana@example.com',name='Ana',auth_time=self.timestamp.timestamp(),
                            expires=(self.timestamp+timedelta(hours=1)).timestamp(),photo='https://lh3.googleusercontent.com/photo')
        self.user = SimpleNamespace(id=1,session_version=2,active=True,email='ana@example.com',firebase_uid='uid',password_hash=None)

    def mock(self, name, **kwargs):
        return self.stack.enter_context(patch.object(service,name,**kwargs))

    def response(self, data):
        return io.BytesIO(json.dumps(data).encode())

    def error(self, fn, status):
        with self.assertRaises(service.FirebaseError) as caught:
            fn()
        self.assertEqual(caught.exception.status,status)
        return caught.exception

    def test_public_config_certificates_and_encryption(self):
        self.assertEqual(service.public_config()['projectId'],'test-project')
        self.app.config['AUTH_PROVIDER']='local'; self.assertIsNone(service.public_config())
        request=self.mock('_certificates',return_value='cert')
        self.assertEqual(service._certificate_request('url'),'cert')
        self.assertEqual(request.call_args.kwargs['timeout'],8)
        service._certificate_request('url',timeout=2); self.assertEqual(request.call_args.kwargs['timeout'],2)
        encrypted=service._cipher().encrypt(b'test-token')
        self.assertNotIn(b'test-token',encrypted)
        self.assertEqual(service._cipher().decrypt(encrypted),b'test-token')

    def test_api_success_transport_and_provider_errors(self):
        network=self.mock('urlopen',return_value=self.response({'ok':True}))
        self.assertEqual(service._api('lookup',{'idToken':'token'}),{'ok':True})
        sent=network.call_args.args[0]
        self.assertTrue(sent.full_url.startswith('https://identitytoolkit.googleapis.com/'))
        self.assertEqual(json.loads(sent.data),{'idToken':'token'})
        network.return_value=self.response([]); self.error(lambda:service._api('lookup',{}),502)
        for error in [URLError('offline'),TimeoutError(),OSError(),ValueError()]:
            network.side_effect=error; self.error(lambda:service._api('lookup',{}),503)
        for code,status in [('OPERATION_NOT_ALLOWED',503),('TOO_MANY_ATTEMPTS_TRY_LATER',429),('WEAK_PASSWORD',400),('UNKNOWN',401)]:
            network.side_effect=HTTPError('https://test',400,'bad',{},self.response({'error':{'message':code}}))
            self.assertEqual(self.error(lambda:service._api('lookup',{}),status).code,code)
        network.side_effect=HTTPError('https://test',400,'bad',{},io.BytesIO(b'not json'))
        self.error(lambda:service._api('lookup',{}),401)

    def test_identity_validates_claims_and_verified_google_email(self):
        claims=dict(sub='uid',iss='https://securetoken.google.com/test-project',auth_time=self.timestamp.timestamp(),
                    exp=self.profile['expires'],email='ana@example.com',email_verified=True,firebase={'sign_in_provider':'google.com'})
        verifier=self.mock('verify_firebase_token',return_value=claims)
        record=self.mock('account_record',return_value=dict(email='ana@example.com',emailVerified=True,displayName=' Ana ',photoUrl='photo'))
        self.assertEqual(service.identity('token')['uid'],'uid')
        verifier.assert_called_with('token',service._certificate_request,audience='test-project',clock_skew_in_seconds=30)
        for token in [None,'','x'*16385]: self.error(lambda:service.identity(token),401)
        for change in [dict(iss='other'),dict(sub=''),dict(auth_time='bad'),dict(auth_time=self.timestamp.timestamp()+60),
                       dict(auth_time=self.timestamp.timestamp()-400),dict(firebase={'sign_in_provider':'anonymous'}),dict(email_verified=False)]:
            verifier.return_value=claims|change; self.error(lambda:service.identity('token'),401)
        verifier.return_value=claims|dict(auth_time=self.timestamp.timestamp()-400)
        self.assertEqual(service.identity('token',fresh=False)['uid'],'uid')
        verifier.return_value=claims; record.return_value={'email':'other@example.com'}
        self.error(lambda:service.identity('token'),401)
        for error,status in [(service.TransportError('offline'),503),(ValueError(),401),(TypeError(),401)]:
            verifier.side_effect=error; self.error(lambda:service.identity('token'),status)

    def test_account_lookup_rejects_disabled_revoked_and_mismatched_users(self):
        api=self.mock('_api')
        for rows in [[],[{'localId':'other'}],[{'localId':'uid','disabled':True}],
                     [{'localId':'uid','validSince':'bad'}],[{'localId':'uid','validSince':200}]]:
            api.return_value={'users':rows}; self.error(lambda:service.account_record('token','uid',100),401)
        api.return_value={'users':[{'localId':'uid','validSince':'50'}]}
        self.assertEqual(service.account_record('token','uid',100)['localId'],'uid')

    def test_binding_never_inherits_privileges_without_legacy_password(self):
        model=self.mock('User'); query=model.query.filter_by.return_value
        query.first.return_value=self.user
        self.assertIs(service.bind_user(self.profile),self.user)
        self.user.active=False; self.error(lambda:service.bind_user(self.profile),403)
        self.user.active=True; query.first.return_value=None
        query.with_for_update.return_value.first.return_value=self.user
        self.error(lambda:service.bind_user(self.profile),403)
        self.user.firebase_uid=None; self.error(lambda:service.bind_user(self.profile),409)
        self.user.password_hash='hash'; check=self.mock('check_password_hash',return_value=False)
        self.error(lambda:service.bind_user(self.profile,'wrong'),409)
        check.return_value=True; service.bind_user(self.profile,'old')
        self.assertEqual(self.user.firebase_uid,'uid'); self.assertIsNone(self.user.password_hash)
        self.assertEqual(self.user.session_version,3)
        query.with_for_update.return_value.first.return_value=None
        service.bind_user(self.profile)
        self.assertEqual(model.call_args.kwargs['role'],'customer')
        self.assertIsNone(model.call_args.kwargs['password_hash'])

    def test_refresh_errors_and_uid_binding(self):
        network=self.mock('urlopen')
        identity=self.mock('identity',return_value=self.profile)
        for token in [None,'','x'*16385]: self.error(lambda:service.refresh_credentials(token,'uid'),401)
        network.return_value=self.response({'id_token':'new','refresh_token':'rotated'})
        self.assertEqual(service.refresh_credentials('refresh','uid')[:2],('new','rotated'))
        identity.assert_called_with('new',fresh=False)
        network.return_value=self.response({'id_token':'new'})
        self.assertEqual(service.refresh_credentials('refresh','uid')[1],'refresh')
        network.return_value=self.response({'id_token':'new'})
        self.error(lambda:service.refresh_credentials('refresh','other'),401)
        network.return_value=self.response([]); self.error(lambda:service.refresh_credentials('refresh','uid'),503)
        for code,status in [(400,401),(429,503),(500,503)]:
            network.side_effect=HTTPError('https://test',code,'error',{},None)
            self.error(lambda:service.refresh_credentials('refresh','uid'),status)
        network.side_effect=URLError('offline'); self.error(lambda:service.refresh_credentials('refresh','uid'),503)

    def test_session_establishment_encrypts_tokens_and_limits_lifetime(self):
        self.mock('identity',return_value=self.profile)
        self.mock('bind_user',return_value=self.user)
        refresh=self.mock('refresh_credentials',return_value=('new','rotated',self.profile))
        for renewable in [False,True]:
            session['old']='discard'
            service.establish_session('token',refresh_token='refresh' if renewable else None)
            record=self.db.session.add.call_args.args[0]
            self.assertEqual(record.expires_at,self.timestamp+timedelta(days=7) if renewable else self.timestamp+timedelta(hours=1))
            tokens=json.loads(service._cipher().decrypt(record.encrypted_tokens.encode()))
            self.assertEqual(tokens['id_token'],'new' if renewable else 'token')
            self.assertNotIn('old',session); self.assertTrue(session.permanent)
            self.assertNotIn('id_token',session); self.assertEqual(session['user_id'],1)
            self.assertEqual(session['profile_photo'],self.profile['photo'])
        refresh.return_value=('new','rotated',self.profile|{'auth_time':0})
        self.error(lambda:service.establish_session('token',refresh_token='refresh'),401)
        self.profile['photo']='https://evil.example/photo'
        service.establish_session('token'); self.assertNotIn('profile_photo',session)

    def test_session_validation_refreshes_and_checks_revocation(self):
        self.assertFalse(service.session_valid(self.user))
        session['firebase_session_id']='sid'
        self.db.session.get.return_value=None; self.assertFalse(service.session_valid(self.user))
        record=SimpleNamespace(user_id=1,user_version=2,expires_at=self.timestamp+timedelta(days=1),
            token_expires_at=self.timestamp+timedelta(hours=1),checked_at=self.timestamp,authenticated_at=self.timestamp,
            encrypted_tokens=service._cipher().encrypt(json.dumps({'id_token':'old','refresh_token':'refresh'}).encode()).decode())
        self.db.session.get.return_value=record
        self.assertTrue(service.session_valid(self.user))
        record.token_expires_at=self.timestamp
        locked=self.db.session.execute.return_value.scalar_one_or_none
        locked.return_value=None; self.assertFalse(service.session_valid(self.user))
        locked.return_value=record
        refresh=self.mock('refresh_credentials',return_value=('new','rotated',self.profile|{'auth_time':0}))
        self.assertFalse(service.session_valid(self.user))
        refresh.return_value=('new','rotated',self.profile)
        account=self.mock('account_record',return_value={'email':'other@example.com'})
        self.assertFalse(service.session_valid(self.user))
        record.checked_at=self.timestamp-timedelta(minutes=6); account.return_value={'email':self.user.email}
        self.assertTrue(service.session_valid(self.user)); self.assertEqual(record.checked_at,self.timestamp)
        self.db.session.commit.assert_called()
        self.assertEqual(json.loads(service._cipher().decrypt(record.encrypted_tokens.encode()))['refresh_token'],'rotated')
        session['user_id']=1; service.end_session(); self.assertEqual(dict(session),{})
        service.end_session(); self.assertEqual(dict(session),{})

    def test_password_migration_registration_and_reset(self):
        model=self.mock('User'); query=model.query.filter_by.return_value
        query.first.return_value=self.user
        self.user.active=False; self.error(lambda:service.password_login('email','password'),401)
        self.user.active=True; self.user.firebase_uid=None; self.user.password_hash='hash'
        self.mock('check_password_hash',return_value=True)
        api=self.mock('_api',return_value={'idToken':'id','refreshToken':'refresh'})
        establish=self.mock('establish_session',return_value=self.user)
        self.assertIs(service.password_login('email','password'),self.user)
        establish.assert_called_with('id','password',refresh_token='refresh')
        api.side_effect=[service.FirebaseError('missing','EMAIL_NOT_FOUND'),{'idToken':'id'}]
        service.password_login('email','password'); self.assertEqual(api.call_args.args[0],'signUp')
        for code,status in [('EMAIL_EXISTS',409),('OTHER',400)]:
            api.side_effect=[service.FirebaseError('missing','EMAIL_NOT_FOUND'),service.FirebaseError('failed',code)]
            self.error(lambda:service.password_login('email','password'),status)
        api.side_effect=service.FirebaseError('offline',status=503)
        self.error(lambda:service.password_login('email','password'),503)
        self.error(lambda:service.register('Ana','email','password'),409)
        query.first.return_value=None; api.side_effect=None; api.return_value={'idToken':'id'}
        self.mock('identity',return_value=self.profile); bind=self.mock('bind_user',return_value=self.user)
        self.assertIs(service.register('Ana','email','password'),self.user)
        bind.assert_called_with(self.profile,name='Ana')
        self.db.session.commit.assert_called()
        service.send_reset('email'); self.assertEqual(api.call_args.args[0],'sendOobCode')
        api.side_effect=service.FirebaseError('missing','EMAIL_NOT_FOUND'); service.send_reset('email')
        api.side_effect=service.FirebaseError('offline',status=503); self.error(lambda:service.send_reset('email'),503)
