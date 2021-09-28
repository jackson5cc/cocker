from store.models import CartItem, Collection, Customer, Order, OrderItem, Product, Cart
from django.urls import reverse
from rest_framework import status
from model_bakery import baker
import pytest
from core.models import User


@pytest.mark.django_db
class TestPlaceOrder:
    def test_if_user_isnt_authenticated_returns_401(self, api_client):
        response = api_client.post(reverse('order-list'))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_cart_not_provided_returns_400(self, api_client, login):
        login()

        response = api_client.post(reverse('order-list'))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['cart_id'] is not None

    def test_if_cart_doesnt_exist_returns_400(self, api_client, login):
        cart = baker.make(Cart)
        cart.delete()

        login()

        response = api_client.post(
            reverse('order-list'), {'cart_id': str(cart.id)})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['cart_id'] is not None

    def test_if_cart_is_empty_returns_400(self, api_client, login):
        cart = baker.make(Cart)

        login()

        response = api_client.post(
            reverse('order-list'), {'cart_id': str(cart.id)})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['cart_id'] is not None

    def test_if_data_is_valid_an_order_is_created(self, api_client, login):
        cart = baker.make(Cart)
        cart_item = baker.make(CartItem, cart_id=cart.id)

        user = login()

        response = api_client.post(
            reverse('order-list'), {'cart_id': str(cart.id)})

        assert response.status_code == status.HTTP_201_CREATED

        assert response.data['id'] is not None

        customer = Customer.objects.get(user_id=user.id)
        assert Order.objects.filter(
            pk=response.data['id'],
            customer_id=customer.id,
            payment_status=Order.PAYMENT_STATUS_PENDING).exists()

        assert OrderItem.objects.filter(
            order_id=response.data['id'],
            product_id=cart_item.product_id,
            quantity=cart_item.quantity).exists()

    def test_if_data_is_valid_cart_is_deleted(self, api_client, login):
        cart = baker.make(Cart)
        baker.make(CartItem, cart_id=cart.id)

        login()

        api_client.post(
            reverse('order-list'), {'cart_id': str(cart.id)})

        assert not Cart.objects.filter(pk=cart.id).exists()


@pytest.mark.django_db
class TestRetrieveOrder:
    def test_if_user_isnt_authenticated_returns_401(self, api_client):
        response = api_client.get(reverse('order-detail', args=[1]))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_order_doesnt_belong_to_authenticated_user_returns_403(self, api_client, login):
        user = baker.make(User)
        order = baker.make(Order, customer_id=user.customer.id)

        login()

        response = api_client.get(reverse('order-detail', args=[order.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_order_belongs_to_authenticated_user_it_is_returned(self, api_client, login):
        user = login()
        order = baker.make(Order, customer_id=user.customer.id)

        response = api_client.get(reverse('order-detail', args=[order.id]))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == order.id

    def test_if_current_user_is_admin_can_view_other_users_order(self, api_client, login):
        user = baker.make(User)
        order = baker.make(Order, customer_id=user.customer.id)

        login(is_admin=True)

        response = api_client.get(reverse('order-detail', args=[order.id]))

        assert response.status_code == status.HTTP_200_OK
