from django.test import TestCase
from django.urls import reverse
from accounts.models import Users
from products.models import Product, Brand, Category, Favorite


class FavoriteTests(TestCase):
	def setUp(self):
		self.cat = Category.objects.create(name='Cat', slug='cat')
		self.brand = Brand.objects.create(name='Brand', category=self.cat)
		self.product = Product.objects.create(name='P', slug='p', description='d', price=1.0, stock=5, category=self.cat, brand=self.brand)
		self.user = Users.objects.create_user(username='u', email='u@example.com', password='pw')

	def test_toggle_favorite_add_and_remove(self):
		url = reverse('product_favorite', args=[self.product.slug])
		# unauthenticated -> 403
		resp = self.client.post(url)
		self.assertEqual(resp.status_code, 403)

		# login
		self.client.login(username='u', password='pw')
		resp = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertEqual(data['status'], 'added')
		self.assertEqual(Favorite.objects.filter(user=self.user, product=self.product).count(), 1)

		# toggle off
		resp2 = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		self.assertEqual(resp2.status_code, 200)
		data2 = resp2.json()
		self.assertEqual(data2['status'], 'removed')
		self.assertEqual(Favorite.objects.filter(user=self.user, product=self.product).count(), 0)

	def test_favorites_shown_in_account(self):
		Favorite.objects.create(user=self.user, product=self.product)
		self.client.login(username='u', password='pw')
		resp = self.client.get(reverse('account'))
		self.assertContains(resp, 'Mes produits favoris')
		# ensure product name is in wishlist
		self.assertContains(resp, self.product.name)
