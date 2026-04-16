import json
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import LoginForm, RegistrationForm
from .models import (
    AuthEvent,
    Cart,
    CartItem,
    Category,
    Item,
    Order,
    OrderItem,
    Product,
    Testimonial,
    User,
)
from .payments import create_razorpay_payment_link, verify_razorpay_payment
from .supabase_client import get_supabase_client


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _json_error(message, status=400):
    return JsonResponse({'error': message}, status=status)


def _parse_json_body(request):
    if request.content_type == 'application/json':
        try:
            return json.loads(request.body.decode('utf-8'))
        except Exception:
            return {}
    return request.POST.dict()


def _require_login_json(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {
                    'detail': 'Authentication required',
                    'login_url': reverse('login'),
                },
                status=401,
            )
        return view_func(request, *args, **kwargs)

    return wrapper


def _get_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def _serialize_cart_item(item):
    return {
        'id': item.id,
        'product_type': item.product_type,
        'product_id': item.product_id,
        'quantity': item.quantity,
        'unit_price': float(item.unit_price),
        'subtotal': float(item.subtotal),
        'name': item.get_snapshot_name(),
        'currency': settings.DEFAULT_CURRENCY,
        'currency_symbol': settings.CURRENCY_SYMBOL,
    }


def _serialize_cart(cart):
    return {
        'cart_id': cart.id,
        'total_price': float(cart.total_price),
        'currency': settings.DEFAULT_CURRENCY,
        'currency_symbol': settings.CURRENCY_SYMBOL,
        'items': [_serialize_cart_item(item) for item in cart.items.all()],
    }


def index_view(request):
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)
    testimonials = Testimonial.objects.filter(is_active=True)
    return render(
        request,
        'index.html',
        {
            'categories': categories,
            'products': products,
            'testimonials': testimonials,
            'currency': settings.DEFAULT_CURRENCY,
            'currency_symbol': settings.CURRENCY_SYMBOL,
        },
    )


def category_detail_view(request, category_id):
    category = get_object_or_404(Category, id=category_id, is_active=True)
    items = category.items.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)
    return render(
        request,
        'category_detail.html',
        {
            'category': category,
            'items': items,
            'categories': categories,
            'currency': settings.DEFAULT_CURRENCY,
            'currency_symbol': settings.CURRENCY_SYMBOL,
        },
    )


def register_view(request):
    form = RegistrationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        password = form.cleaned_data['password1']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        mobile = form.cleaned_data.get('mobile', '')

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'A user with this email already exists.')
        else:
            try:
                supabase = get_supabase_client()
            except Exception as exc:
                messages.error(request, f'Registration failed: {exc}')
                return render(request, 'register.html', {'form': form})

            try:
                response = supabase.auth.sign_up(email=email, password=password)
            except TypeError:
                try:
                    response = supabase.auth.sign_up({'email': email, 'password': password})
                except Exception as exc:
                    messages.error(request, f'Registration failed: {exc}')
                    return render(request, 'register.html', {'form': form})
            except Exception as exc:
                messages.error(request, f'Registration failed: {exc}')
                return render(request, 'register.html', {'form': form})

            error = None
            if isinstance(response, dict):
                error = response.get('error') or response.get('message')
            else:
                error = getattr(response, 'error', None) or getattr(response, 'message', None)

            if error:
                messages.error(request, str(error))
                return render(request, 'register.html', {'form': form})

            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                mobile=mobile,
                is_active=True,
            )

            AuthEvent.objects.create(
                user=user,
                event_type='register',
                ip_address=get_client_ip(request),
            )

            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')

    return render(request, 'register.html', {'form': form})


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        password = form.cleaned_data['password']

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            AuthEvent.objects.create(
                user=user,
                event_type='login',
                ip_address=get_client_ip(request),
            )
            return redirect('index')

        messages.error(request, 'Invalid email or password.')

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@_require_login_json
def add_to_cart_api(request):
    if request.method != 'POST':
        return _json_error('POST method required', status=405)

    data = _parse_json_body(request)
    product_type = data.get('product_type')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if product_type not in (CartItem.PRODUCT, CartItem.ITEM):
        return _json_error('product_type must be product or item')

    try:
        product_id = int(product_id)
        quantity = int(quantity)
    except (TypeError, ValueError):
        return _json_error('product_id and quantity must be integers')

    if quantity < 1:
        return _json_error('quantity must be at least 1')

    cart = _get_cart(request.user)
    try:
        cart_item = cart.add_item(product_type, product_id, quantity)
    except ValueError as exc:
        return _json_error(str(exc), status=404)

    return JsonResponse(
        {
            'status': 'ok',
            'cart': _serialize_cart(cart),
            'added_item': _serialize_cart_item(cart_item),
        }
    )


@_require_login_json
def update_cart_item_api(request):
    if request.method != 'POST':
        return _json_error('POST method required', status=405)

    data = _parse_json_body(request)
    cart_item_id = data.get('cart_item_id')
    product_type = data.get('product_type')
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    try:
        if cart_item_id is not None:
            cart_item_id = int(cart_item_id)
        elif product_type and product_id is not None:
            product_id = int(product_id)
        else:
            raise ValueError('cart_item_id or product_type/product_id required')
        quantity = int(quantity)
    except (TypeError, ValueError):
        return _json_error('Invalid cart_item_id/product_id or quantity', status=400)

    if quantity < 1:
        return _json_error('quantity must be at least 1', status=400)

    cart = _get_cart(request.user)
    cart_item = None
    if cart_item_id is not None:
        cart_item = cart.items.filter(id=cart_item_id).first()
    else:
        cart_item = cart.items.filter(product_type=product_type, product_id=product_id).first()

    if not cart_item:
        return _json_error('Cart item not found', status=404)

    cart_item.quantity = quantity
    cart_item.save()

    return JsonResponse(
        {
            'status': 'ok',
            'cart': _serialize_cart(cart),
            'updated_item': _serialize_cart_item(cart_item),
        }
    )


@_require_login_json
def remove_cart_item_api(request):
    if request.method != 'POST':
        return _json_error('POST method required', status=405)

    data = _parse_json_body(request)
    cart_item_id = data.get('cart_item_id')
    product_type = data.get('product_type')
    product_id = data.get('product_id')

    try:
        if cart_item_id is not None:
            cart_item_id = int(cart_item_id)
        elif product_type and product_id is not None:
            product_id = int(product_id)
        else:
            raise ValueError('cart_item_id or product_type/product_id required')
    except (TypeError, ValueError):
        return _json_error('Invalid cart_item_id or product_id', status=400)

    cart = _get_cart(request.user)
    cart_item = None
    if cart_item_id is not None:
        cart_item = cart.items.filter(id=cart_item_id).first()
    else:
        cart_item = cart.items.filter(product_type=product_type, product_id=product_id).first()

    if not cart_item:
        return _json_error('Cart item not found', status=404)

    cart_item.delete()

    return JsonResponse(
        {
            'status': 'ok',
            'cart': _serialize_cart(cart),
        }
    )


@_require_login_json
def api_cart_view(request):
    if request.method != 'GET':
        return _json_error('GET method required', status=405)

    cart = _get_cart(request.user)
    return JsonResponse({'cart': _serialize_cart(cart)})


@_require_login_json
def api_checkout(request):
    if request.method != 'POST':
        return _json_error('POST method required', status=405)

    data = _parse_json_body(request)
    payment_method = data.get('payment_method')
    shipping_address_line1 = (data.get('shipping_address_line1') or '').strip()
    shipping_address_line2 = (data.get('shipping_address_line2') or '').strip()
    shipping_city = (data.get('shipping_city') or '').strip()
    shipping_state = (data.get('shipping_state') or '').strip()
    shipping_postal_code = (data.get('shipping_postal_code') or '').strip()
    shipping_country = (data.get('shipping_country') or '').strip()
    delivery_notes = (data.get('delivery_notes') or '').strip()

    if payment_method not in (Order.PAYMENT_CASH, Order.PAYMENT_ONLINE):
        return _json_error('payment_method must be cash or online')

    if not shipping_address_line1 or not shipping_city or not shipping_postal_code or not shipping_country:
        return _json_error('Shipping address is required for checkout', status=400)

    cart = _get_cart(request.user)
    if not cart.items.exists():
        return _json_error('Cart is empty', status=400)

    order = Order.objects.create(
        user=request.user,
        total_price=cart.total_price,
        payment_method=payment_method,
        payment_status=Order.PAYMENT_PENDING,
        order_status=Order.ORDER_PENDING,
        shipping_address_line1=shipping_address_line1,
        shipping_address_line2=shipping_address_line2,
        shipping_city=shipping_city,
        shipping_state=shipping_state,
        shipping_postal_code=shipping_postal_code,
        shipping_country=shipping_country,
        delivery_notes=delivery_notes,
    )

    for item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product_type=item.product_type,
            product_id=item.product_id,
            name=item.get_snapshot_name(),
            price=item.unit_price,
            quantity=item.quantity,
        )

    if payment_method == Order.PAYMENT_CASH:
        order.payment_status = Order.PAYMENT_FAILED if cart.total_price == 0 else 'unpaid'
        order.payment_status = 'unpaid'
        order.order_status = Order.ORDER_CONFIRMED
        order.save(update_fields=['payment_status', 'order_status'])
        cart.clear()
        return JsonResponse(
            {
                'status': 'confirmed',
                'payment_method': 'cash',
                'order_id': order.id,
                'order_status': order.order_status,
                'payment_status': order.payment_status,
            }
        )

    try:
        payment_url = create_razorpay_payment_link(order, request)
    except Exception as exc:
        order.payment_status = Order.PAYMENT_FAILED
        order.order_status = Order.ORDER_PENDING
        order.save(update_fields=['payment_status', 'order_status'])
        return _json_error(f'Unable to create Razorpay payment link: {exc}', status=500)

    return JsonResponse(
        {
            'status': 'payment_required',
            'payment_method': 'online',
            'order_id': order.id,
            'payment_url': payment_url,
        }
    )


@_require_login_json
def order_list_api(request):
    if request.method != 'GET':
        return _json_error('GET method required', status=405)

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    order_data = []
    for order in orders:
        order_data.append(
            {
                'order_id': order.id,
                'total_price': float(order.total_price),
                'currency': settings.DEFAULT_CURRENCY,
                'currency_symbol': settings.CURRENCY_SYMBOL,
                'payment_method': order.payment_method,
                'payment_status': order.payment_status,
                'order_status': order.order_status,
                'created_at': order.created_at.isoformat(),
                'items': [
                    {
                        'product_type': item.product_type,
                        'product_id': item.product_id,
                        'name': item.name,
                        'price': float(item.price),
                        'quantity': item.quantity,
                        'currency': settings.DEFAULT_CURRENCY,
                        'currency_symbol': settings.CURRENCY_SYMBOL,
                    }
                    for item in order.items.all()
                ],
            }
        )
    return JsonResponse({'orders': order_data})


@csrf_exempt
def payment_callback(request):
    data = request.GET.dict() if request.GET else request.POST.dict()
    razorpay_link_id = data.get('razorpay_payment_link_id')
    if not razorpay_link_id:
        return _json_error('Missing Razorpay payment link identifier', status=400)

    order = Order.objects.filter(payment_reference=razorpay_link_id).first()
    if not order:
        return _json_error('Order not found for payment callback', status=404)

    if order.payment_status == Order.PAYMENT_PAID:
        return JsonResponse({'status': 'already_paid'})

    if order.payment_method != Order.PAYMENT_ONLINE:
        return _json_error('Payment callback does not match order payment method', status=400)

    verified = verify_razorpay_payment(data)

    if verified:
        order.payment_status = Order.PAYMENT_PAID
        order.order_status = Order.ORDER_CONFIRMED
        order.payment_data = data
        order.save(update_fields=['payment_status', 'order_status', 'payment_data'])

        cart = getattr(order.user, 'cart', None)
        if cart:
            cart.clear()

        return JsonResponse({'status': 'paid', 'order_id': order.id})

    order.payment_status = Order.PAYMENT_FAILED
    order.order_status = Order.ORDER_FAILED
    order.payment_data = data
    order.save(update_fields=['payment_status', 'order_status', 'payment_data'])
    return JsonResponse({'status': 'failed', 'order_id': order.id}, status=400)
