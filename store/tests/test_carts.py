from store.models import CartItem, Collection, Order, OrderItem, Product, Cart
from django.urls import reverse
from rest_framework import status
from model_bakery import baker
import pytest


@pytest.fixture
def cart_id():
    return baker.make(Cart).id


@pytest.fixture
def get_cart(api_client):
    def action(cart_id):
        return api_client.get(reverse('cart-detail', args=[cart_id]))
    return action


@pytest.fixture
def add_to_cart(api_client):
    def action(cart_id, product_id, quantity):
        endpoint = reverse('cart-item-list', args=[cart_id])
        response = api_client.post(
            endpoint, {'product_id': product_id, 'quantity': quantity})
        return response
    return action


@pytest.fixture
def update_cart_item(api_client):
    def action(cart_id, item_id, quantity):
        endpoint = reverse('cart-item-detail', args=[cart_id, item_id])
        return api_client.patch(endpoint, {'quantity': quantity})
    return action


@pytest.fixture
def delete_cart_item(api_client):
    def action(cart_id, item_id):
        endpoint = reverse('cart-item-detail', args=[cart_id, item_id])
        return api_client.delete(endpoint)
    return action


class TestCarts:
    def test_get_is_not_allowed(self, api_client):
        response = api_client.get(reverse('cart-list'))

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.django_db
    def test_post_creates_a_cart(self, api_client):
        response = api_client.post(reverse('cart-list'))

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['id'] is not None
        assert Cart.objects.filter(pk=response.data['id']).exists()


class TestAddToCart:
    @pytest.mark.django_db
    @pytest.mark.parametrize('product_id', ['', 0])
    def test_if_product_is_invalid_returns_400(self, cart_id, add_to_cart, product_id):
        response = add_to_cart(cart_id, product_id, 1)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['product_id'] is not None

    @pytest.mark.django_db
    @pytest.mark.parametrize('quantity', ['', 0])
    def test_if_quantity_is_invalid_returns_400(self, cart_id, add_to_cart, quantity):
        product = baker.make(Product)
        response = add_to_cart(cart_id, product.id, quantity)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['quantity'] is not None

    @pytest.mark.django_db
    def test_if_data_is_valid_creates_a_cart_item(self, cart_id, add_to_cart):
        product = baker.make(Product)
        quantity = 1
        response = add_to_cart(cart_id, product.id, quantity)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['id'] is not None
        assert CartItem.objects.filter(pk=response.data['id']).exists()

    @pytest.mark.django_db
    def test_if_product_exists_in_cart_quantity_is_increased(self, cart_id, add_to_cart):
        product = baker.make(Product)
        response = add_to_cart(cart_id, product.id, 1)
        response = add_to_cart(cart_id, product.id, 1)

        cart_item = CartItem.objects.get(pk=response.data['id'])
        assert cart_item.quantity == 2


class TestUpdateCartItemQuantity:
    @pytest.mark.django_db
    def test_put_not_allowed(self, api_client):
        response = api_client.put(reverse('cart-item-detail', args=[1, 1]))

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.django_db
    def test_if_item_doesnt_exist_returns_404(self, update_cart_item):
        item = baker.make(CartItem)
        item.delete()

        response = update_cart_item(item.cart_id, item.id, 1)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    @pytest.mark.parametrize('quantity', ['', 0, -1])
    def test_if_quantity_is_invalid_returns_400(self, update_cart_item, quantity):
        item = baker.make(CartItem)

        response = update_cart_item(item.cart_id, item.id, quantity)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_if_quantity_is_valid_cart_item_is_updated(self, update_cart_item):
        item = baker.make(CartItem)

        response = update_cart_item(item.cart_id, item.id, 1)

        assert response.status_code == status.HTTP_200_OK
        item = CartItem.objects.get(pk=item.id)
        assert item.quantity == 1


class TestRemoveFromCart:
    @pytest.mark.django_db
    def test_if_item_doesnt_exist_returns_404(self, delete_cart_item):
        item = baker.make(CartItem)
        item.delete()

        response = delete_cart_item(item.cart_id, item.id)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_if_item_exists_it_is_deleted(self, delete_cart_item):
        item = baker.make(CartItem)

        response = delete_cart_item(item.cart_id, item.id)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CartItem.objects.filter(pk=item.id).exists()


class TestGetCart:
    @pytest.mark.django_db
    def test_if_cart_doesnt_exist_returns_404(self, get_cart):
        cart = baker.make(Cart)
        cart.delete()

        response = get_cart(cart.id)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_if_cart_exists_it_is_returned(self, get_cart):
        unit_price = 10
        quantity = 2

        cart = baker.make(Cart)
        product = baker.make(Product, unit_price=unit_price)
        item = baker.make(CartItem, cart_id=cart.id,
                          product_id=product.id, quantity=quantity)

        response = get_cart(cart.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'id': str(cart.id),
            'items': [
                {
                    'id': item.id,
                    'product': {
                        'id': product.id,
                        'title': product.title,
                        'unit_price': product.unit_price
                    },
                    'quantity': quantity,
                    'total_price': quantity*unit_price
                }
            ],
            'total_price': quantity*unit_price
        }
