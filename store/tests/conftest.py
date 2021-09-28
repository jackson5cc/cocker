from django.conf import settings
from model_bakery import baker
import pytest


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def login(api_client):
    def do_login(is_admin=False):
        user = baker.make(settings.AUTH_USER_MODEL, is_staff=is_admin)
        api_client.force_authenticate(user=user)
        return user
    return do_login


