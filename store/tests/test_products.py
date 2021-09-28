from decimal import Decimal
from store.models import Collection, Order, OrderItem, Product
from django.urls import reverse
from rest_framework import status
from model_bakery import baker
import pytest


class TestRetrieveProduct:
    @pytest.mark.django_db
    def test_if_product_doesnt_exist_returns_404(self, api_client):
        response = api_client.get(reverse('product-detail', args=[1]))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_if_product_exists_it_is_returned(self, api_client):
        product = baker.make(Product)

        response = api_client.get(reverse('product-detail', args=[product.id]))

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'id': product.id,
            'title': product.title,
            'slug': product.slug,
            'description': product.description,
            'inventory': product.inventory,
            'unit_price': product.unit_price,
            'price_with_tax': product.unit_price * Decimal(1.1),
            'collection': product.collection_id,
        }


class TestListProducts:
    @pytest.mark.django_db
    def test_returns_paged_products(self, api_client):
        total_products = 20
        page_size = 10
        baker.make(Product, _quantity=total_products)

        response = api_client.get(reverse('product-list'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == total_products
        assert len(response.data['results']) == page_size

    @pytest.mark.django_db
    def test_if_filtered_by_collection_only_returns_products_in_that_collection(self, api_client):
        collection1 = baker.make(Collection)
        baker.make(Product, collection=collection1, _quantity=2)
        collection2 = baker.make(Collection)
        baker.make(Product, collection=collection2, _quantity=2)

        url = reverse('product-list') + f'?collection_id={collection1.id}'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert all([product['collection'] ==
                   collection1.id for product in response.data['results']])
    
    @pytest.mark.django_db
    def test_if_search_filter_applied_only_returns_products_matching_search_phrase(self, api_client):
        baker.make(Product, title='coffee')
        baker.make(Product, title='tea')

        url = reverse('product-list') + f'?search=coffee'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'coffee'
    
    
    @pytest.mark.django_db
    def test_if_filtered_by_price_only_returns_products_in_price_range(self, api_client):
        baker.make(Product, unit_price=1)
        baker.make(Product, unit_price=2)
        baker.make(Product, unit_price=3)

        url = reverse('product-list') + '?unit_price__gt=1&unit_price__lt=3'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['unit_price'] == 2


class TestCreateProduct:
    @pytest.mark.django_db
    def test_if_user_is_not_authenticated_returns_401(self, api_client):
        response = api_client.post(reverse('product-list'), {'title': 'a'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_user_is_not_admin_returns_403(self, api_client, login):
        login(is_admin=False)

        response = api_client.post(reverse('product-list'), {'title': 'a'})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_if_product_is_invalid_returns_400(self, api_client, login):
        login(is_admin=True)

        response = api_client.post(reverse('product-list'), {
            'title': 'a',
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['slug'] is not None
        assert response.data['unit_price'] is not None
        assert response.data['inventory'] is not None
        assert response.data['collection'] is not None

    @pytest.mark.django_db
    def test_if_collection_is_invalid_returns_400(self, api_client, login):
        login(is_admin=True)

        response = api_client.post(reverse('product-list'), {
            'title': 'a',
            'slug': 'b',
            'unit_price': 1,
            'inventory': 2,
            'collection': 0
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['collection'] is not None

    @pytest.mark.django_db
    def test_if_product_is_valid_returns_200(self, api_client, login):
        login(is_admin=True)

        response = api_client.post(reverse('product-list'), {
            'title': 'a',
            'slug': 'b',
            'unit_price': 1,
            'inventory': 2,
            'collection': 1
        })

        assert response.status_code == status.HTTP_201_CREATED

        saved_product = Product.objects.get(pk=response.data['id'])
        assert saved_product.title == 'a'
        assert saved_product.slug == 'b'
        assert saved_product.unit_price == 1
        assert saved_product.inventory == 2
        assert saved_product.collection_id == 1


class TestDeleteProduct:
    @pytest.mark.django_db
    def test_if_user_is_not_authenticated_returns_401(self, api_client):
        endpoint = reverse('product-detail', args=[1])
        response = api_client.delete(endpoint)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_user_is_not_admin_returns_403(self, login, api_client):
        login(is_admin=False)

        endpoint = reverse('product-detail', args=[1])
        response = api_client.delete(endpoint)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_if_product_is_ordered_before_returns_405(self, login, api_client):
        user = login(is_admin=True)

        product = baker.make(Product)
        order = baker.make(Order, customer=user.customer)
        order_item = baker.make(OrderItem, order=order, product=product)

        endpoint = reverse('product-detail', args=[product.id])
        response = api_client.delete(endpoint)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.data['error'] != ''

    @pytest.mark.django_db
    def test_if_product_successfully_deleted_returns_204_(self, login, api_client):
        login(is_admin=True)

        product = baker.make(Product)

        endpoint = reverse('product-detail', args=[product.id])
        response = api_client.delete(endpoint)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Product.objects.filter(pk=product.id).exists()
