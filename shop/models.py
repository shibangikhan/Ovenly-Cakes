from decimal import Decimal

from django.conf import settings
from cloudinary_storage.storage import MediaCloudinaryStorage
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import Sum


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field is required')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=20, blank=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class AuthEvent(models.Model):
    EVENT_TYPES = [
        ('register', 'Register'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auth_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} - {self.event_type} @ {self.created_at}'

class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', storage=MediaCloudinaryStorage())
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', storage=MediaCloudinaryStorage())
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='items/', storage=MediaCloudinaryStorage())
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Testimonial(models.Model):
    quote = models.TextField()
    author = models.CharField(max_length=200)
    occupation = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='testimonials/', storage=MediaCloudinaryStorage(), blank=True, null=True)
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return f'{self.author} — {self.occupation or "Testimonial"}'

    @property
    def star_range(self):
        return range(self.rating)

class CartItem(models.Model):
    PRODUCT = 'product'
    ITEM = 'item'

    PRODUCT_TYPE_CHOICES = [
        (PRODUCT, 'Product'),
        (ITEM, 'Item'),
    ]

    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name='items')
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES)
    product_id = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('cart', 'product_type', 'product_id')]
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if self.quantity < 1:
            self.quantity = 1
        self.subtotal = self.unit_price * Decimal(self.quantity)
        super().save(*args, **kwargs)

    def get_product(self):
        if self.product_type == self.PRODUCT:
            return Product.objects.filter(id=self.product_id).first()
        if self.product_type == self.ITEM:
            return Item.objects.filter(id=self.product_id).first()
        return None

    def get_snapshot_name(self):
        product = self.get_product()
        return product.name if product else f'{self.product_type}#{self.product_id}'


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Cart({self.user.email})'

    @property
    def total_price(self):
        total = self.items.aggregate(total=Sum('subtotal'))['total']
        return total or Decimal('0.00')

    def add_item(self, product_type, product_id, quantity=1):
        product = self.fetch_product(product_type, product_id)
        if not product or not getattr(product, 'is_active', False):
            raise ValueError('Product not found or inactive')

        unit_price = product.price
        cart_item, created = CartItem.objects.get_or_create(
            cart=self,
            product_type=product_type,
            product_id=product_id,
            defaults={
                'quantity': quantity,
                'unit_price': unit_price,
            },
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.unit_price = unit_price
            cart_item.save()
        return cart_item

    @staticmethod
    def fetch_product(product_type, product_id):
        if product_type == CartItem.PRODUCT:
            return Product.objects.filter(id=product_id, is_active=True).first()
        if product_type == CartItem.ITEM:
            return Item.objects.filter(id=product_id, is_active=True).first()
        return None

    def clear(self):
        self.items.all().delete()


class Order(models.Model):
    PAYMENT_CASH = 'cash'
    PAYMENT_ONLINE = 'online'

    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_CASH, 'Cash on Delivery'),
        (PAYMENT_ONLINE, 'Online Payment'),
    ]

    PAYMENT_PENDING = 'pending'
    PAYMENT_UNPAID = 'unpaid'
    PAYMENT_PAID = 'paid'
    PAYMENT_FAILED = 'failed'

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, 'Pending'),
        (PAYMENT_UNPAID, 'Unpaid'),
        (PAYMENT_PAID, 'Paid'),
        (PAYMENT_FAILED, 'Failed'),
    ]

    ORDER_PENDING = 'pending'
    ORDER_CONFIRMED = 'confirmed'
    ORDER_SHIPPED = 'shipped'
    ORDER_DELIVERED = 'delivered'
    ORDER_CANCELLED = 'cancelled'
    ORDER_FAILED = 'failed'

    ORDER_STATUS_CHOICES = [
        (ORDER_PENDING, 'Pending'),
        (ORDER_CONFIRMED, 'Confirmed'),
        (ORDER_SHIPPED, 'Shipped'),
        (ORDER_DELIVERED, 'Delivered'),
        (ORDER_CANCELLED, 'Cancelled'),
        (ORDER_FAILED, 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING)
    order_status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default=ORDER_PENDING)
    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    payment_data = models.JSONField(blank=True, null=True)
    shipping_address_line1 = models.CharField(max_length=255, blank=True, null=True)
    shipping_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    shipping_city = models.CharField(max_length=100, blank=True, null=True)
    shipping_state = models.CharField(max_length=100, blank=True, null=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True, null=True)
    shipping_country = models.CharField(max_length=100, blank=True, null=True)
    delivery_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order({self.id}) - {self.user.email}'


class OrderItem(models.Model):
    product_type = models.CharField(max_length=10, choices=CartItem.PRODUCT_TYPE_CHOICES)
    product_id = models.PositiveIntegerField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'OrderItem({self.name})'



