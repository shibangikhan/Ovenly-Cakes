import hmac
import requests
from hashlib import sha256

from django.conf import settings
from django.urls import reverse


def _razorpay_auth():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise RuntimeError('Razorpay credentials are not configured.')
    return (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)


def create_razorpay_payment_link(order, request):
    payload = {
        'amount': int(order.total_price * 100),
        'currency': 'INR',
        'accept_partial': False,
        'reference_id': str(order.id),
        'description': f'Order {order.id}',
        'customer': {
            'name': order.user.first_name or order.user.email,
            'email': order.user.email,
            'contact': getattr(order.user, 'mobile', ''),
        },
        'notify': {'sms': False, 'email': True},
        'callback_url': request.build_absolute_uri(reverse('api_payment_callback')),
        'callback_method': 'get',
    }

    response = requests.post(
        'https://api.razorpay.com/v1/payment_links',
        auth=_razorpay_auth(),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    link_id = data.get('id')
    payment_url = data.get('short_url') or data.get('long_url')
    if not link_id or not payment_url:
        raise RuntimeError('Razorpay did not return a valid payment link.')

    order.payment_reference = link_id
    order.save(update_fields=['payment_reference'])
    return payment_url


def verify_razorpay_payment(request_data):
    payment_id = request_data.get('razorpay_payment_id')
    link_id = request_data.get('razorpay_payment_link_id')
    signature = request_data.get('razorpay_signature')
    if not payment_id or not link_id or not signature:
        return False

    payload = f'{link_id}|{payment_id}'.encode('utf-8')
    secret = settings.RAZORPAY_KEY_SECRET.encode('utf-8')
    generated_signature = hmac.new(secret, payload, sha256).hexdigest()
    return hmac.compare_digest(generated_signature, signature)
