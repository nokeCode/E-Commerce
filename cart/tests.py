from django.test import TestCase
from django.urls import reverse
from products.models import Product, Brand, Category

class CartAjaxTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Cat', slug='cat')
        self.brand = Brand.objects.create(name='Brand', category=self.cat)
        self.product = Product.objects.create(name='P', slug='p', description='d', price=10.0, stock=5, category=self.cat, brand=self.brand)

    def test_add_ajax(self):
        url = reverse('cart_add_ajax')
        resp = self.client.post(url, {'product_id': self.product.id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['product']['name'], self.product.name)
        self.assertEqual(data['cart']['total_items'], 1)

    def test_update_ajax_set_quantity(self):
        url = reverse('cart_update_ajax')
        # set quantity to 3
        resp = self.client.post(url, {'product_id': self.product.id, 'quantity': 3}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['product']['quantity'], 3)
        self.assertEqual(data['cart']['total_items'], 3)

    def test_update_ajax_remove_when_zero(self):
        # first add one
        add_url = reverse('cart_add_ajax')
        self.client.post(add_url, {'product_id': self.product.id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        url = reverse('cart_update_ajax')
        resp = self.client.post(url, {'product_id': self.product.id, 'quantity': 0}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        # quantity should now be 0 and total items 0
        self.assertEqual(data['product']['quantity'], 0)
        self.assertEqual(data['cart']['total_items'], 0)

