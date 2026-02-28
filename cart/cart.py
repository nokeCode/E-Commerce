from decimal import Decimal
from products.models.Product import Product
from django.conf import settings
from cart.models.CartItem import CartItem
from cart.models.Cart import Cart 


class Cart:
    def __init__(self, request):
        """
        Initialisation du panier.
        """
        self.session = request.session
        cart = self.session.get('cart')

        if not cart:
            cart = self.session['cart'] = {}

        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Ajouter un produit au panier ou mettre à jour la quantité.
        """
        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    def remove(self, product):
        """
        Supprimer un produit du panier.
        """
        product_id = str(product.id)

        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        """
        Marquer la session comme modifiée.
        """
        self.session.modified = True

    def __iter__(self):
        """
        Permet d’itérer sur les items du panier dans les templates.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Nombre total d’articles.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Total du panier.
        """
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def clear(self):
        """
        Vider le panier.
        """
        self.session.pop('cart', None)
        self.save()
