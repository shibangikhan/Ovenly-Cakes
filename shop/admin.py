from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import AuthEvent, Cart, CartItem, Category, Item, Order, OrderItem, Product, User, Testimonial


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'mobile')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'mobile', 'is_active', 'is_staff')


class CustomUserAdmin(DjangoUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ('email', 'first_name', 'last_name', 'mobile', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'mobile')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'mobile')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'mobile', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )


@admin.register(User)
class UserAdmin(CustomUserAdmin):
    pass


@admin.register(AuthEvent)
class AuthEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'ip_address', 'created_at')
    list_filter = ('event_type',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'ip_address')
    readonly_fields = ('created_at',)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'description')
    ordering = ('category', 'name')

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('author', 'occupation', 'rating', 'is_active', 'created_at')
    list_filter = ('is_active', 'rating')
    search_fields = ('author', 'occupation', 'quote')
    ordering = ('-created_at',)
    fields = ('quote', 'author', 'occupation', 'image', 'rating', 'is_active')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__email',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product_type', 'product_id', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('product_type',)
    search_fields = ('product_id', 'cart__user__email')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'total_price',
        'payment_method',
        'payment_status',
        'order_status',
        'delivery_destination',
        'created_at',
    )
    list_filter = ('payment_method', 'payment_status', 'order_status')
    search_fields = (
        'user__email',
        'payment_reference',
        'shipping_address_line1',
        'shipping_city',
        'shipping_postal_code',
    )
    readonly_fields = (
        'payment_status',
        'order_status',
        'shipping_address_line1',
        'shipping_address_line2',
        'shipping_city',
        'shipping_state',
        'shipping_postal_code',
        'shipping_country',
        'delivery_notes',
    )

    def delivery_destination(self, obj):
        address_parts = [
            obj.shipping_address_line1,
            obj.shipping_address_line2,
            obj.shipping_city,
            obj.shipping_state,
            obj.shipping_postal_code,
            obj.shipping_country,
        ]
        return ', '.join([part for part in address_parts if part])
    delivery_destination.short_description = 'Delivery Address'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'name', 'product_type', 'product_id', 'quantity', 'price')
    search_fields = ('order__id', 'name')
