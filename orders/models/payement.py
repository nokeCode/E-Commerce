from django.db import models
from django.utils import timezone


class Payment(models.Model):
    METHOD_CARD = 'card'
    METHOD_PAYPAL = 'paypal'

    PAYMENT_METHODS = [
        (METHOD_CARD, 'Carte bancaire'),
        (METHOD_PAYPAL, 'PayPal'),
    ]

    PROVIDER_STRIPE = 'stripe'
    PROVIDER_PAYPAL = 'paypal'

    PROVIDERS = [
        (PROVIDER_STRIPE, 'Stripe'),
        (PROVIDER_PAYPAL, 'PayPal'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_PAID, 'Payé'),
        (STATUS_FAILED, 'Échoué'),
        (STATUS_REFUNDED, 'Remboursé'),
    ]

    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default=METHOD_CARD)

    provider = models.CharField(max_length=20, choices=PROVIDERS, blank=True, null=True)

    amount = models.DecimalField( max_digits=10, decimal_places=2)

    status = models.CharField( max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    transaction_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID de transaction Stripe / PayPal")
    card_brand = models.CharField(max_length=50, blank=True, null=True)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_exp_month = models.PositiveSmallIntegerField( blank=True, null=True)
    card_exp_year = models.PositiveSmallIntegerField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['provider']),
        ]

    def __str__(self):
        return f"Payment #{self.id} | {self.provider} | {self.status} | {self.amount}"

    def mark_paid(self, transaction_id=None, metadata=None):
        self.status = self.STATUS_PAID
        self.paid_at = timezone.now()

        if transaction_id:
            self.transaction_id = transaction_id

        if metadata:
            self.metadata = metadata

        self.save(update_fields=[
            'status',
            'paid_at',
            'transaction_id',
            'metadata',
            'updated_at'
        ])

    def mark_failed(self, transaction_id=None, metadata=None):
        self.status = self.STATUS_FAILED

        if transaction_id:
            self.transaction_id = transaction_id

        if metadata:
            self.metadata = metadata

        self.save(update_fields=[
            'status',
            'transaction_id',
            'metadata',
            'updated_at'
        ])

    def mark_refunded(self, transaction_id=None, metadata=None):
        self.status = self.STATUS_REFUNDED

        if transaction_id:
            self.transaction_id = transaction_id

        if metadata:
            self.metadata = metadata

        self.save(update_fields=[
            'status',
            'transaction_id',
            'metadata',
            'updated_at'
        ])
