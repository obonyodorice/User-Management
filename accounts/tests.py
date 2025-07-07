# accounts/tests.py

import uuid
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import override_settings
from datetime import date, datetime
from accounts.forms import UserRegistrationForm, UserProfileForm, AdminUserEditForm
from accounts.models import User


class UserModelTest(TestCase):
    """Test cases for the custom User model"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'regular',
            'phone': '1234567890',
            'bio': 'Test bio',
            'birth_date': date(1990, 1, 1)
        }
    
    def test_user_creation(self):
        """Test creating a new user"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.user_type, 'regular')
        self.assertFalse(user.is_verified)
        self.assertIsInstance(user.verification_token, uuid.UUID)
    
    def test_user_str_method(self):
        """Test the __str__ method returns email"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')
    
    def test_get_full_name(self):
        """Test the get_full_name method"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), 'Test User')
        
        # Test with no first/last name
        user_no_name = User.objects.create_user(
            username='noname',
            email='noname@example.com',
            password='test123'
        )
        self.assertEqual(user_no_name.get_full_name(), '')
    
    def test_is_admin_user(self):
        """Test the is_admin_user method"""
        # Regular user
        regular_user = User.objects.create_user(**self.user_data)
        self.assertFalse(regular_user.is_admin_user())
        
        # Admin user
        admin_data = self.user_data.copy()
        admin_data['user_type'] = 'admin'
        admin_data['email'] = 'admin@example.com'
        admin_data['username'] = 'adminuser'
        admin_user = User.objects.create_user(**admin_data)
        self.assertTrue(admin_user.is_admin_user())
        
        # Superuser
        superuser = User.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='superpass123'
        )
        self.assertTrue(superuser.is_admin_user())
    
    def test_email_unique_constraint(self):
        """Test that email field is unique"""
        User.objects.create_user(**self.user_data)
        
        # Try to create another user with same email
        duplicate_data = self.user_data.copy()
        duplicate_data['username'] = 'duplicate'
        
        with self.assertRaises(Exception):
            User.objects.create_user(**duplicate_data)
    
    def test_username_field_is_email(self):
        """Test that USERNAME_FIELD is set to email"""
        self.assertEqual(User.USERNAME_FIELD, 'email')
    
    def test_user_timestamps(self):
        """Test that created_at and updated_at are set automatically"""
        user = User.objects.create_user(**self.user_data)
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)
        
        # Test updated_at changes on save
        original_updated_at = user.updated_at
        user.bio = 'Updated bio'
        user.save()
        self.assertGreater(user.updated_at, original_updated_at)


class UserRegistrationFormTest(TestCase):
    """Test cases for UserRegistrationForm"""
    
    def test_valid_form(self):
        """Test form with valid data"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'regular',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_password_mismatch(self):
        """Test form with mismatched passwords"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'regular',
            'password1': 'testpass123',
            'password2': 'differentpass'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_duplicate_email(self):
        """Test form with duplicate email"""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='testpass123'
        )
        
        form_data = {
            'username': 'newuser',
            'email': 'test@example.com',  # Same email
            'first_name': 'New',
            'last_name': 'User',
            'user_type': 'regular',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_form_save(self):
        """Test that form saves user correctly"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'admin',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.user_type, 'admin')
        self.assertTrue(user.check_password('testpass123'))


class UserProfileFormTest(TestCase):
    """Test cases for UserProfileForm"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_valid_profile_form(self):
        """Test form with valid profile data"""
        form_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'phone': '9876543210',
            'bio': 'Updated bio',
            'birth_date': '1990-01-01'
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
    
    def test_profile_form_save(self):
        """Test that profile form saves correctly"""
        form_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'phone': '9876543210',
            'bio': 'Updated bio',
            'birth_date': '1990-01-01'
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.phone, '9876543210')


class UserViewsTest(TestCase):
    """Test cases for user views"""
    
    def setUp(self):
        self.client = Client()
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123',
            user_type='regular'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            user_type='admin'
        )
        self.superuser = User.objects.create_superuser(
            username='super',
            email='super@example.com',
            password='testpass123'
        )
    
    def test_registration_view_get(self):
        """Test registration view GET request"""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Register')
        self.assertIsInstance(response.context['form'], UserRegistrationForm)
    
    def test_registration_view_post_valid(self):
        """Test registration view POST with valid data"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'user_type': 'regular',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        response = self.client.post(reverse('accounts:register'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
        
        # Check that verification email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verify Your Account', mail.outbox[0].subject)
    
    def test_login_view(self):
        """Test login view"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
    
    def test_login_functionality(self):
        """Test user login functionality"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'regular@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_profile_view_authenticated(self):
        """Test profile view for authenticated user"""
        self.client.login(username='regular@example.com', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'regular@example.com')
    
    def test_profile_view_anonymous(self):
        """Test profile view redirects anonymous users"""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_edit_profile_view_get(self):
        """Test edit profile view GET request"""
        self.client.login(username='regular@example.com', password='testpass123')
        response = self.client.get(reverse('accounts:edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], UserProfileForm)
    
    def test_edit_profile_view_post(self):
        """Test edit profile view POST request"""
        self.client.login(username='regular@example.com', password='testpass123')
        form_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'regular@example.com',
            'phone': '9876543210',
            'bio': 'Updated bio',
            'birth_date': '1990-01-01'
        }
        response = self.client.post(reverse('accounts:edit_profile'), data=form_data)
        self.assertEqual(response.status_code, 302)
        
        # Check that user was updated
        updated_user = User.objects.get(email='regular@example.com')
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.phone, '9876543210')
    
    def test_email_verification_valid_token(self):
        """Test email verification with valid token"""
        user = User.objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='testpass123',
            is_verified=False
        )
        
        response = self.client.get(
            reverse('accounts:verify_email', kwargs={'token': user.verification_token})
        )
        self.assertEqual(response.status_code, 302)
        
        # Check that user is now verified
        user.refresh_from_db()
        self.assertTrue(user.is_verified)
    
    def test_email_verification_invalid_token(self):
        """Test email verification with invalid token"""
        invalid_token = uuid.uuid4()
        response = self.client.get(
            reverse('accounts:verify_email', kwargs={'token': invalid_token})
        )
        self.assertEqual(response.status_code, 302)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Invalid verification token' in str(m) for m in messages))


class AdminViewsTest(TestCase):
    """Test cases for admin views"""
    
    def setUp(self):
        self.client = Client()
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123',
            user_type='regular'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            user_type='admin'
        )
    
    def test_admin_users_view_permission_denied(self):
        """Test admin users view denies access to regular users"""
        self.client.login(username='regular@example.com', password='testpass123')
        response = self.client.get(reverse('accounts:admin_users'))
        self.assertEqual(response.status_code, 403)
    
    def test_admin_users_view_admin_access(self):
        """Test admin users view allows access to admin users"""
        self.client.login(username='admin@example.com', password='testpass123')
        response = self.client.get(reverse('accounts:admin_users'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Management')
    
    def test_admin_users_view_pagination(self):
        """Test admin users view pagination"""
        # Create multiple users
        for i in range(15):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
        
        self.client.login(username='admin@example.com', password='testpass123')
        response = self.client.get(reverse('accounts:admin_users'))
        self.assertEqual(response.status_code, 200)
        
        # Check pagination (10 users per page)
        self.assertTrue(response.context['page_obj'].has_next())
        self.assertEqual(len(response.context['page_obj']), 10)
    
    def test_admin_edit_user_view_permission_denied(self):
        """Test admin edit user view denies access to regular users"""
        self.client.login(username='regular@example.com', password='testpass123')
        response = self.client.get(
            reverse('accounts:admin_edit_user', kwargs={'user_id': self.regular_user.id})
        )
        self.assertEqual(response.status_code, 403)
    
    def test_admin_edit_user_view_admin_access(self):
        """Test admin edit user view allows access to admin users"""
        self.client.login(username='admin@example.com', password='testpass123')
        response = self.client.get(
            reverse('accounts:admin_edit_user', kwargs={'user_id': self.regular_user.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], AdminUserEditForm)
    
    def test_admin_edit_user_post(self):
        """Test admin edit user POST request"""
        self.client.login(username='admin@example.com', password='testpass123')
        form_data = {
            'username': 'regular',
            'email': 'regular@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'user_type': 'admin',
            'is_active': True,
            'is_verified': True
        }
        response = self.client.post(
            reverse('accounts:admin_edit_user', kwargs={'user_id': self.regular_user.id}),
            data=form_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Check that user was updated
        updated_user = User.objects.get(id=self.regular_user.id)
        self.assertEqual(updated_user.user_type, 'admin')
        self.assertTrue(updated_user.is_verified)
    
    def test_admin_delete_user_view_permission_denied(self):
        """Test admin delete user view denies access to regular users"""
        self.client.login(username='regular@example.com', password='testpass123')
        response = self.client.get(
            reverse('accounts:admin_delete_user', kwargs={'user_id': self.regular_user.id})
        )
        self.assertEqual(response.status_code, 403)
    
    def test_admin_delete_user_view_admin_access(self):
        """Test admin delete user view allows access to admin users"""
        self.client.login(username='admin@example.com', password='testpass123')
        response = self.client.get(
            reverse('accounts:admin_delete_user', kwargs={'user_id': self.regular_user.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Are you sure you want to delete this user?')
    
    def test_admin_delete_user_post(self):
        """Test admin delete user POST request"""
        self.client.login(username='admin@example.com', password='testpass123')
        user_id = self.regular_user.id
        
        response = self.client.post(
            reverse('accounts:admin_delete_user', kwargs={'user_id': user_id})
        )
        self.assertEqual(response.status_code, 302)
        
        # Check that user was deleted
        self.assertFalse(User.objects.filter(id=user_id).exists())
    
    def test_admin_delete_nonexistent_user(self):
        """Test admin delete view with non-existent user"""
        self.client.login(username='admin@example.com', password='testpass123')
        response = self.client.get(
            reverse('accounts:admin_delete_user', kwargs={'user_id': 99999})
        )
        self.assertEqual(response.status_code, 404)


class EmailVerificationTest(TestCase):
    """Test cases for email verification functionality"""
    
    def test_send_verification_email(self):
        """Test that verification email is sent"""
        from accounts.views import send_verification_email
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        send_verification_email(user)
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        self.assertIn('Verify Your Account', mail.outbox[0].subject)
        self.assertIn(str(user.verification_token), mail.outbox[0].body)


class SecurityTest(TestCase):
    """Test cases for security features"""
    
    def setUp(self):
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123',
            user_type='regular'
        )
    
    def test_login_required_decorators(self):
        """Test that login_required decorators work"""
        protected_urls = [
            reverse('accounts:profile'),
            reverse('accounts:edit_profile'),
            reverse('accounts:admin_users'),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login/', response.url)
    
    def test_admin_permission_checking(self):
        """Test that admin views check permissions properly"""
        self.client.login(username='regular@example.com', password='testpass123')
        
        admin_urls = [
            reverse('accounts:admin_users'),
            reverse('accounts:admin_edit_user', kwargs={'user_id': self.regular_user.id}),
            reverse('accounts:admin_delete_user', kwargs={'user_id': self.regular_user.id}),
        ]
        
        for url in admin_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)
    
    def test_csrf_protection(self):
        """Test CSRF protection on forms"""
        self.client.login(username='regular@example.com', password='testpass123')
        
        # Try to submit form without CSRF token
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'regular@example.com',
        }
        
        response = self.client.post(
            reverse('accounts:edit_profile'),
            data=form_data,
            HTTP_X_CSRFTOKEN='invalid'
        )
        # Should be rejected due to CSRF
        self.assertEqual(response.status_code, 403)


@override_settings(MEDIA_ROOT='/tmp/test_media')
class FileUploadTest(TestCase):
    """Test cases for file upload functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='test@example.com', password='testpass123')
    
    def test_profile_picture_upload(self):
        """Test profile picture upload"""
        # Create a simple image file
        image = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'profile_picture': image
        }
        
        response = self.client.post(
            reverse('accounts:edit_profile'),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_picture)