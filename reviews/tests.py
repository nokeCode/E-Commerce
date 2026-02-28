from django.test import TestCase
from django.urls import reverse
from accounts.models import Users
from products.models import Product, Brand, Category
from reviews.models import Review


class ReviewTests(TestCase):
	def setUp(self):
		# Create category and brand
		self.cat = Category.objects.create(name='Catégorie', slug='cat')
		self.brand = Brand.objects.create(name='Marque', category=self.cat)

		# Create product
		self.product = Product.objects.create(
			name='ProdTest', slug='prodtest', description='desc', price=10.00, stock=5,
			category=self.cat, brand=self.brand
		)

		# Create a user
		self.user = Users.objects.create_user(username='testuser', email='test@example.com', password='pass1234')

	def test_create_review(self):
		self.client.login(username='testuser', password='pass1234')
		url = reverse('product', args=[self.product.slug])
		response = self.client.post(url, {'rating': '5', 'comment': 'Super produit'}, follow=True)
		self.assertEqual(Review.objects.filter(user=self.user, product=self.product).count(), 1)
		rev = Review.objects.get(user=self.user, product=self.product)
		self.assertEqual(rev.rating, 5)
		self.assertEqual(rev.comment, 'Super produit')

	def test_update_review(self):
		Review.objects.create(user=self.user, product=self.product, rating=3, comment='ok')
		self.client.login(username='testuser', password='pass1234')
		url = reverse('product', args=[self.product.slug])
		response = self.client.post(url, {'rating': '4', 'comment': 'Meilleur'}, follow=True)
		self.assertEqual(Review.objects.filter(user=self.user, product=self.product).count(), 1)
		rev = Review.objects.get(user=self.user, product=self.product)
		self.assertEqual(rev.rating, 4)
		self.assertEqual(rev.comment, 'Meilleur')

	def test_reviews_pagination(self):
		# Create multiple reviews by different users
		for i in range(12):
			u = Users.objects.create_user(username=f'u{i}', email=f'u{i}@ex.com', password='pw')
			Review.objects.create(user=u, product=self.product, rating=(i % 5) + 1, comment=f'c{i}')

		url = reverse('product', args=[self.product.slug])
		response = self.client.get(url)
		self.assertIn('reviews_page_obj', response.context)
		page_obj = response.context['reviews_page_obj']
		paginator = response.context['reviews_paginator']
		self.assertEqual(paginator.count, 12)
		# default per page is 5
		self.assertEqual(len(page_obj.object_list), 5)

		# check page 3 has 2 items (12 -> pages: 5,5,2)
		response2 = self.client.get(url + '?rpage=3')
		page_obj2 = response2.context['reviews_page_obj']
		self.assertEqual(page_obj2.number, 3)
		self.assertEqual(len(page_obj2.object_list), 2)
