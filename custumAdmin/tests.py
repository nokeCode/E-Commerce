from django.test import TestCase
from django.urls import reverse
from products.models import Category, Brand, Product, ProductImage
from orders.models import Order, OrderItem, ShippingAddress
from django.core.files.uploadedfile import SimpleUploadedFile


class AdminProductEditTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Cat", slug="test-cat", description="desc")
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")
        self.product = Product.objects.create(
            name="Original",
            slug="original",
            description="orig desc",
            price=1.23,
            stock=5,
            category=self.category,
            brand=self.brand,
        )
        # add an image
        self.img = ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile("img.jpg", b"content", content_type="image/jpeg"),
            is_main=True,
        )

    def test_edit_product_fields_and_delete_image(self):
        url = reverse('product_edit', args=[self.product.id])
        # post new data with deletion of the existing image
        with open(self.img.image.path, 'rb') as f:
            pass  # ensure file exists
        response = self.client.post(url, {
            'name': 'Updated',
            'description': 'new desc',
            'price': '9.99',
            'stock': '10',
            'category': str(self.category.id),
            'brand': str(self.brand.id),
            'delete_images': str(self.img.id),
        })
        # after post should redirect to product list
        self.assertEqual(response.status_code, 302)
        prod = Product.objects.get(id=self.product.id)
        self.assertEqual(prod.name, 'Updated')
        self.assertEqual(prod.price, 9.99)
        self.assertEqual(prod.stock, 10)
        # image should be removed
        self.assertFalse(ProductImage.objects.filter(id=self.img.id).exists())

    def test_order_list_and_detail(self):
        # create a user and order with item
        from accounts.models.Users import Users
        user = Users.objects.create(username='u1', email='u1@example.com', password='pass')
        order = Order.objects.create(user=user, total=0)
        item = OrderItem.objects.create(order=order, product=self.product, quantity=2, price=5.0)
        # shipping address
        ShippingAddress.objects.create(order=order, address='123 St', city='City', postal_code='00000', country='Country')
        order.recalculate_total()
        # login and fetch pages
        self.client.force_login(user)
        list_url = reverse('order_list')
        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, f'{order.order_number or order.id}')
        # detail view
        detail_url = reverse('order_detail', args=[order.id])
        resp2 = self.client.get(detail_url)
        self.assertEqual(resp2.status_code, 200)
        self.assertContains(resp2, user.email)
        self.assertContains(resp2, self.product.name)
