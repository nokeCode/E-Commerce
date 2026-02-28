def get_cart_total(request):
    cart = request.session.get("cart", {})
    total = 0

    for item in cart.values():
        total += float(item["price"]) * int(item["quantity"])

    return total
