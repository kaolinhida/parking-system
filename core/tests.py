from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.permissions import GATE_OPERATOR_GROUP, PARKING_ADMIN_GROUP


class SmokePageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='regular',
            password='pass12345',
        )

    def test_public_pages_open(self):
        urls = [
            reverse('core:home'),
            reverse('parkings:parking_list'),
            reverse('parkings:global_search'),
            reverse('accounts:login'),
            reverse('accounts:register'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_authenticated_user_pages_open(self):
        self.client.force_login(self.user)

        urls = [
            reverse('vehicles:vehicle_list'),
            reverse('accounts:profile'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)


class StaffRoleAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.regular_user = User.objects.create_user(
            username='regular',
            password='pass12345',
        )

        self.operator_group = Group.objects.create(name=GATE_OPERATOR_GROUP)
        self.operator = User.objects.create_user(
            username='operator',
            password='pass12345',
            is_staff=True,
        )
        self.operator.groups.add(self.operator_group)

        self.admin_group = Group.objects.create(name=PARKING_ADMIN_GROUP)
        self.admin = User.objects.create_user(
            username='parking_admin',
            password='pass12345',
            is_staff=True,
        )
        self.admin.groups.add(self.admin_group)

    def assert_login_redirect(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_regular_user_cannot_open_staff_pages(self):
        self.client.force_login(self.regular_user)

        urls = [
            reverse('dashboard:home'),
            reverse('reports:home'),
            reverse('access_control:home'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assert_login_redirect(response)

    def test_gate_operator_can_open_access_control_pages(self):
        self.client.force_login(self.operator)

        urls = [
            reverse('access_control:home'),
            reverse('access_control:logs'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_gate_operator_cannot_open_admin_pages(self):
        self.client.force_login(self.operator)

        urls = [
            reverse('dashboard:home'),
            reverse('reports:home'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assert_login_redirect(response)

    def test_parking_admin_can_open_admin_and_access_control_pages(self):
        self.client.force_login(self.admin)

        urls = [
            reverse('dashboard:home'),
            reverse('reports:home'),
            reverse('access_control:home'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
