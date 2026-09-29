"""HTTP controller contracts with isolated persistence and provider doubles."""
import io
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from flask import Flask, g
from sqlalchemy.exc import IntegrityError
from app.controllers.web import account_controller as controller


class AccountControllerTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.app = Flask(__name__)
        self.app.secret_key = 'isolated-controller-test-signing-key'
        self.actor = None
        @self.app.before_request
        def identity():
            g.user = self.actor
        routes = [('/login','login',controller.access),('/registro','register',controller.access),
                  ('/recuperar-acceso','recover',controller.access),('/cuenta','account_preview',controller.account),
                  ('/logout','logout',controller.logout),('/admin','admin_preview',controller.admin),
                  ('/products/new','product_create',controller.product_edit),
                  ('/products/<int:product_id>','product_edit',controller.product_edit),
                  ('/products/<int:product_id>/delete','product_delete',controller.product_delete),
                  ('/users/<int:user_id>','user_update',controller.user_update),
                  ('/api/session','firebase_session',controller.firebase_session)]
        for path, endpoint, view in routes:
            self.app.add_url_rule(path, 'main.'+endpoint, view, methods=['GET','POST'])
        self.client = self.app.test_client()
        self.db = self.mock('db')
        self.render = self.mock('render_template', return_value='rendered')
        self.throttle = self.mock('throttle', return_value=True)
        self.captcha = self.mock('verify_captcha')
        self.audit = self.mock('audit')
        self.auth = self.mock('authenticate', return_value=None)
        self.save = self.mock('save_product')
        self.deactivate = self.mock('deactivate_product')
        self.image = self.mock('store_image', return_value='/image.webp')
        for name in ['Product','Category','User','AuditLog']:
            model = self.mock(name)
            model.query.filter.return_value.order_by.return_value.all.return_value = []
            model.query.order_by.return_value.all.return_value = []
            model.query.order_by.return_value.limit.return_value.all.return_value = []
        self.enabled = self.stack.enter_context(patch.object(controller.firebase,'enabled',return_value=False))
        self.register = self.stack.enter_context(patch.object(controller.firebase,'register'))
        self.login = self.stack.enter_context(patch.object(controller.firebase,'password_login'))
        self.reset = self.stack.enter_context(patch.object(controller.firebase,'send_reset'))
        self.establish = self.stack.enter_context(patch.object(controller.firebase,'establish_session'))
        self.end = self.stack.enter_context(patch.object(controller.firebase,'end_session'))
        self.stack.enter_context(patch('app.services.dashboard_service.dashboard_data',return_value={}))

    def mock(self, name, **kwargs):
        return self.stack.enter_context(patch.object(controller, name, **kwargs))

    def user(self, role='customer', id=1):
        return SimpleNamespace(id=id, name='Ana', whatsapp='', role=role, active=True,
                               profile_completed=False, session_version=1)

    def post(self, path, **data):
        return self.client.post(path, data=data)

    def test_access_local_registration_login_and_failures(self):
        data = dict(name='Ana',email='ana@example.com',password='test-long-password')
        self.assertEqual(self.client.get('/login').status_code,200)
        self.assertEqual(self.post('/registro',**data).status_code,303)
        self.db.session.commit.assert_called_once()
        self.assertEqual(controller.User.call_args.kwargs['role'],'customer')
        self.assertTrue(controller.User.call_args.kwargs['password_hash'].startswith('scrypt:'))
        self.assertEqual(self.post('/login',**data).status_code,401)
        for role, target in [('customer','/cuenta'),('staff','/admin'),('admin','/admin')]:
            self.auth.return_value=self.user(role)
            self.assertEqual(self.post('/login',**data).location,target)
        self.throttle.return_value=False
        self.assertEqual(self.post('/login',**data).status_code,429)
        self.throttle.return_value=True
        self.assertEqual(self.post('/registro',email='invalid').status_code,400)
        self.db.session.flush.side_effect=IntegrityError('insert',{},Exception())
        self.assertEqual(self.post('/registro',**data).status_code,400)
        self.db.session.rollback.assert_called()
        self.actor=self.user()
        self.assertEqual(self.client.get('/login').location,'/cuenta')

    def test_firebase_access_and_recovery(self):
        data=dict(name='Ana',email='ana@example.com',password='test-long-password')
        self.enabled.return_value=True
        self.assertEqual(self.post('/registro',**data).location,'/login')
        self.register.assert_called_once_with('Ana','ana@example.com','test-long-password')
        for role in ['customer','staff']:
            self.login.return_value=self.user(role)
            self.assertEqual(self.post('/login',**data).location,'/cuenta' if role=='customer' else '/admin')
        self.login.side_effect=controller.firebase.FirebaseError('offline',status=503)
        self.assertEqual(self.post('/login',**data).status_code,503)
        self.assertEqual(self.post('/recuperar-acceso',email='ana@example.com').location,'/login')
        self.reset.assert_called_once_with('ana@example.com')
        self.reset.side_effect=controller.firebase.FirebaseError('offline',status=503)
        self.assertEqual(self.post('/recuperar-acceso',email='ana@example.com').status_code,503)
        self.assertEqual(self.post('/recuperar-acceso',email='bad').status_code,400)
        self.enabled.return_value=False
        self.assertEqual(self.post('/recuperar-acceso',email='ana@example.com').status_code,503)
        self.throttle.return_value=False
        self.assertEqual(self.post('/recuperar-acceso',email='ana@example.com').status_code,429)

    def test_profile_normalization_validation_skip_and_logout(self):
        self.actor=self.user()
        self.assertEqual(self.client.get('/cuenta').status_code,200)
        for phone, expected in [('0988357638','+593988357638'),('988357638','+593988357638'),('+593 98-835-7638','+593988357638'),('','')]:
            self.assertEqual(self.post('/cuenta',name=' Ana   María ',whatsapp=phone).status_code,303)
            self.assertEqual(self.actor.name,'Ana María'); self.assertEqual(self.actor.whatsapp,expected)
            self.assertTrue(self.actor.profile_completed)
        for data in [dict(name=''),dict(name='x'*81),dict(name='A\x01'),dict(name='Ana',whatsapp='123')]:
            self.assertEqual(self.post('/cuenta',**data).status_code,400)
        self.assertEqual(self.post('/cuenta',action='skip').status_code,303)
        self.assertEqual(self.post('/logout').location,'/login'); self.end.assert_called_once()

    def test_permissions_and_admin_sections(self):
        self.assertEqual(self.client.get('/cuenta').location,'/login')
        self.actor=self.user()
        self.assertEqual(self.client.get('/admin').status_code,403)
        self.actor=self.user('staff')
        for section in ['users','activity']:
            self.assertEqual(self.client.get('/admin?section='+section).status_code,403)
        self.assertEqual(self.client.get('/admin?section=unknown').status_code,404)
        self.actor=self.user('admin')
        for section in ['dashboard','products','inventory','categories','users','activity']:
            self.assertEqual(self.client.get('/admin?section='+section).status_code,200)

    def test_product_edit_upload_preserve_image_errors_and_deactivation(self):
        self.actor=self.user('staff')
        item=SimpleNamespace(menu_id='coffee', image='/old.webp')
        self.db.get_or_404.return_value=item
        self.assertEqual(self.client.get('/products/new').status_code,200)
        self.assertEqual(self.post('/products/1',name='Café',active='on').status_code,303)
        self.assertEqual(self.save.call_args.args[0]['image'],'/old.webp')
        response=self.client.post('/products/1',data={'image_file':(io.BytesIO(b'fixture'),'photo.png')})
        self.assertEqual(response.status_code,303)
        self.assertEqual(self.save.call_args.args[0]['image'],'/image.webp')
        for error, status in [(ValueError('invalid'),400),(IntegrityError('insert',{},Exception()),409)]:
            self.save.side_effect=error
            self.assertEqual(self.post('/products/1').status_code,status)
        self.assertEqual(self.post('/products/1/delete').status_code,303)
        self.deactivate.assert_called_once_with(item)
        item.menu_id=None
        self.assertEqual(self.client.get('/products/1').status_code,404)
        self.assertEqual(self.post('/products/1/delete').status_code,404)

    def test_role_updates_preserve_admin_and_invalidate_sessions(self):
        self.actor=self.user('admin')
        self.db.get_or_404.return_value=self.actor
        self.assertEqual(self.post('/users/1',role='unknown').status_code,400)
        self.assertEqual(self.post('/users/1',role='customer').status_code,303)
        self.assertEqual(self.actor.role,'admin'); self.assertEqual(self.actor.session_version,1)
        other=self.user('admin',2); self.db.get_or_404.return_value=other
        controller.User.query.filter_by.return_value.count.return_value=1
        self.post('/users/2',role='staff',active='on')
        self.assertEqual(other.role,'admin')
        controller.User.query.filter_by.return_value.count.return_value=2
        self.post('/users/2',role='staff',active='on')
        self.assertEqual(other.role,'staff'); self.assertEqual(other.session_version,2)
        self.db.get_or_404.return_value=self.actor
        self.post('/users/1',role='admin',active='on')
        with self.client.session_transaction() as saved:
            self.assertEqual(saved['user_version'],2)
        self.db.session.execute.assert_called()

    def test_social_session_validation_redirects_and_errors(self):
        self.assertEqual(self.client.post('/api/session',json={}).status_code,503)
        self.enabled.return_value=True
        for data in [[],None,{'legacy_password':123},{'legacy_password':'x'*257}]:
            self.assertEqual(self.client.post('/api/session',json=data).status_code,400)
        self.throttle.return_value=False
        self.assertEqual(self.client.post('/api/session',json={}).status_code,429)
        self.throttle.return_value=True
        for role in ['customer','admin']:
            self.establish.return_value=self.user(role)
            response=self.client.post('/api/session',json={'id_token':'id','refresh_token':'refresh','captcha_token':'captcha'})
            self.assertEqual(response.json['redirect'],'/cuenta' if role=='customer' else '/admin')
            self.establish.assert_called_with('id','',refresh_token='refresh')
            self.captcha.assert_called_with('captcha')
        for error,status in [(controller.firebase.FirebaseError('offline',status=503),503),(IntegrityError('insert',{},Exception()),409)]:
            self.establish.side_effect=error
            self.assertEqual(self.client.post('/api/session',json={}).status_code,status)
            self.db.session.rollback.assert_called()
