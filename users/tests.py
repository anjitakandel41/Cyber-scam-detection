"""Tests for the "Remember Dashboard" (read-only view mode) flow."""

from datetime import timedelta

from allauth.socialaccount.models import SocialApp
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from chatbot.models import ChatMessage

from .models import RememberedDevice
from .remember import cookie_name

User = get_user_model()


class ViewModeTestCase(TestCase):

    def setUp(self):
        # The public templates render {% provider_login_url 'google' %}, which
        # needs a configured social app (present in the real database).
        app = SocialApp.objects.create(
            provider='google', name='Google', client_id='test', secret='test',
        )
        app.sites.add(Site.objects.get_current())

        self.password = 'Str0ng-P4ssw0rd!'
        self.user = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password=self.password,
        )

    def login(self):
        self.assertTrue(
            self.client.login(username=self.user.username, password=self.password)
        )

    def login_and_logout(self):
        """Reproduce the real browser flow so the device cookie gets set."""
        self.client.post(
            reverse('users:login'),
            {'username': self.user.username, 'password': self.password},
        )
        self.client.post(reverse('users:logout'))

    def assertRedirectsToLogin(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response['Location'])


class NewVisitorTests(ViewModeTestCase):
    """A never-seen browser gets the plain Home -> Register -> Login flow."""

    def test_home_page_is_not_a_dashboard(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_view_mode'])

    def test_dashboard_redirects_to_login(self):
        self.assertRedirectsToLogin(self.client.get(reverse('dashboard:user_dashboard')))

    def test_scanner_redirects_to_login(self):
        self.assertRedirectsToLogin(self.client.get(reverse('scanner:url_scan')))


class RememberedDeviceTests(ViewModeTestCase):

    def test_logout_creates_device_and_cookie(self):
        self.login_and_logout()

        self.assertEqual(RememberedDevice.objects.filter(user=self.user).count(), 1)
        self.assertIn(cookie_name(), self.client.cookies)

    def test_any_login_backend_is_remembered(self):
        """Covers Google / allauth logins, which never reach CustomLoginView."""
        self.client.force_login(self.user)
        self.client.get(reverse('dashboard:user_dashboard'))

        self.assertEqual(RememberedDevice.objects.filter(user=self.user).count(), 1)

    def test_forget_device_while_logged_in_is_not_undone(self):
        self.login()
        self.client.get(reverse('dashboard:user_dashboard'))
        self.assertEqual(RememberedDevice.objects.count(), 1)

        self.client.post(reverse('users:forget_device'))
        self.client.get(reverse('dashboard:user_dashboard'))

        self.assertEqual(RememberedDevice.objects.count(), 0)

    def test_home_redirects_to_dashboard_once(self):
        self.login_and_logout()

        first = self.client.get(reverse('home'))
        self.assertRedirects(first, reverse('dashboard:user_dashboard'))

        # The marketing landing page stays reachable afterwards.
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)

    def test_dashboard_is_readable_but_not_authenticated(self):
        self.login_and_logout()

        response = self.client.get(reverse('dashboard:user_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_view_mode'])
        self.assertEqual(response.context['display_user'], self.user)
        # The critical invariant: view mode is NOT a login.
        self.assertFalse(response.context['user'].is_authenticated)

    def test_read_only_pages_are_available(self):
        self.login_and_logout()

        for name in ['reports:home', 'scan_history', 'quiz:home', 'chatbot:home', 'account_profile']:
            with self.subTest(url=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_restricted_features_require_a_session(self):
        self.login_and_logout()

        restricted = [
            reverse('scanner:url_scan'),
            reverse('scanner:email_scan'),
            reverse('scanner:sms_scan'),
            reverse('scanner:qr_upload'),
            reverse('scanner:gmail_inbox'),
            reverse('quiz:attempt'),
        ]

        for url in restricted:
            with self.subTest(url=url):
                self.assertRedirectsToLogin(self.client.get(url))

    def test_unsafe_methods_are_rejected_in_view_mode(self):
        self.login_and_logout()

        # The chatbot page renders read-only, but posting a message must not work.
        response = self.client.post(reverse('chatbot:home'), {'message': 'hello'})

        self.assertRedirectsToLogin(response)
        self.assertEqual(ChatMessage.objects.count(), 0)

    def test_forget_device_clears_memory(self):
        self.login_and_logout()

        response = self.client.post(reverse('users:forget_device'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(RememberedDevice.objects.count(), 0)
        self.assertRedirectsToLogin(self.client.get(reverse('dashboard:user_dashboard')))


class ViewModeSecurityTests(ViewModeTestCase):

    def test_forged_cookie_is_rejected(self):
        self.client.cookies[cookie_name()] = 'not-a-valid-signed-token'

        self.assertRedirectsToLogin(self.client.get(reverse('dashboard:user_dashboard')))

    def test_password_change_invalidates_remembered_device(self):
        self.login_and_logout()
        self.assertEqual(self.client.get(reverse('dashboard:user_dashboard')).status_code, 200)

        self.user.set_password('An0ther-P4ssw0rd!')
        self.user.save()

        self.assertRedirectsToLogin(self.client.get(reverse('dashboard:user_dashboard')))

    def test_expired_device_is_rejected(self):
        self.login_and_logout()

        RememberedDevice.objects.update(expires_at=timezone.now() - timedelta(days=1))

        self.assertRedirectsToLogin(self.client.get(reverse('dashboard:user_dashboard')))

    def test_inactive_user_is_not_remembered(self):
        self.login_and_logout()

        self.user.is_active = False
        self.user.save()

        self.assertRedirectsToLogin(self.client.get(reverse('dashboard:user_dashboard')))

    def test_admin_accounts_are_never_remembered(self):
        admin = User.objects.create_user(
            username='root',
            email='root@example.com',
            password=self.password,
            is_staff=True,
        )
        self.client.post(
            reverse('users:login'),
            {'username': admin.username, 'password': self.password},
        )
        self.client.post(reverse('users:logout'))

        self.assertEqual(RememberedDevice.objects.filter(user=admin).count(), 0)
        self.assertRedirectsToLogin(self.client.get(reverse('dashboard:user_dashboard')))

    def test_view_mode_never_exposes_another_user(self):
        """Logging in as a second user re-points the memory at that user only."""
        bob = User.objects.create_user(
            username='bob', email='bob@example.com', password=self.password,
        )

        self.login_and_logout()  # browser now remembers alice

        self.client.post(
            reverse('users:login'),
            {'username': bob.username, 'password': self.password},
        )
        self.client.post(reverse('users:logout'))

        self.assertEqual(RememberedDevice.objects.filter(user=self.user).count(), 0)
        self.assertEqual(RememberedDevice.objects.filter(user=bob).count(), 1)

        response = self.client.get(reverse('dashboard:user_dashboard'))
        self.assertEqual(response.context['display_user'], bob)

    def test_active_session_still_has_full_access(self):
        """The existing authenticated experience is unchanged."""
        self.login_and_logout()
        self.login()

        response = self.client.get(reverse('dashboard:user_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_view_mode'])

        self.assertEqual(self.client.get(reverse('scanner:url_scan')).status_code, 200)
