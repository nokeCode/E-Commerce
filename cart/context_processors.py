from .cart import Cart


def cart_context(request):
    """
    Rend le panier disponible globalement dans les templates.
    """
    return {
        'cart': Cart(request)
    }
