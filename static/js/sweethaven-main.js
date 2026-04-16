// ==================== CART MANAGEMENT ====================

let cart = { items: [], total_price: 0 };

function updateCartBadge() {
  const badge = document.querySelector('.cart-badge');
  const cartBtn = document.querySelector('.navbar-cart-btn');
  const totalItems = cart.items.reduce((sum, item) => sum + item.quantity, 0);
  
  if (totalItems > 0) {
    if (!badge) {
      const newBadge = document.createElement('span');
      newBadge.className = 'cart-badge';
      newBadge.textContent = totalItems;
      cartBtn.appendChild(newBadge);
    } else {
      badge.textContent = totalItems;
    }
  } else if (badge) {
    badge.remove();
  }
}

function saveCart() {
  updateCartBadge();
}

async function loadCart() {
  if (!window.API_CART_URL) return;

  try {
    const response = await fetch(window.API_CART_URL, {
      method: 'GET',
      credentials: 'same-origin',
    });
    const data = await response.json();
    if (response.ok && data.cart) {
      cart = data.cart;
      renderCartItems();
      saveCart();
    } else {
      console.error('Failed to load cart', data);
      if (response.status === 401) {
        cart = { items: [], total_price: 0 };
        renderCartItems();
        saveCart();
      }
    }
  } catch (error) {
    console.error('Cart load failed', error);
  }
}

async function addToCart(product) {
  if (!isAuthenticated()) {
    showCartNotification('Login required to add items to cart.');
    setTimeout(() => {
      window.location.href = window.LOGIN_URL;
    }, 1200);
    return;
  }

  const success = await addToCartBackend(product);
  if (success) {
    await loadCart();
    showCartNotification('Added to cart!');
  }
}

async function removeFromCart(cartItemId) {
  if (!cartItemId) return;

  const removed = await removeCartItemBackend(cartItemId);
  if (removed) {
    await loadCart();
    showCartNotification('Item removed from cart.');
  }
}

async function updateQuantity(cartItemId, change) {
  const item = cart.items.find(i => i.id === cartItemId);
  if (!item) return;
  const newQuantity = Math.max(1, item.quantity + change);
  const updated = await updateCartItemBackend(cartItemId, newQuantity);
  if (updated) {
    await loadCart();
    showCartNotification('Cart updated.');
  }
}

function renderCartItems() {
  const cartItemsContainer = document.querySelector('.cart-items');
  
  if (!cartItemsContainer) return;
  
  if (!cart.items || cart.items.length === 0) {
    cartItemsContainer.innerHTML = `
      <div class="cart-empty">
        <p>Your cart is empty</p>
        <p style="font-size: 3rem;">🛒</p>
      </div>
    `;
    updateCartSummary();
    return;
  }
  
  cartItemsContainer.innerHTML = cart.items.map(item => `
    <div class="cart-item">
      <div class="cart-item-info">
        <div class="cart-item-name">${item.name}</div>
        <div class="cart-item-price">₹${item.unit_price.toFixed(2)}</div>
        <div class="cart-item-quantity">
          <button class="quantity-btn" onclick="updateQuantity(${item.id}, -1)">−</button>
          <span>${item.quantity}</span>
          <button class="quantity-btn" onclick="updateQuantity(${item.id}, 1)">+</button>
        </div>
      </div>
      <button class="cart-item-remove" onclick="removeFromCart(${item.id})">✕</button>
    </div>
  `).join('');
  
  updateCartSummary();
}

function updateCartSummary() {
  const summaryContainer = document.querySelector('.cart-summary');
  if (!summaryContainer) return;
  
 const subtotal = cart.items.reduce((sum, item) => 
  sum + (item.unit_price * item.quantity), 0
);
  const tax = subtotal * 0.1;
  const total = subtotal + tax;
  
  summaryContainer.innerHTML = `
    <div class="summary-row">
      <span>Subtotal:</span>
      <span>₹${subtotal.toFixed(2)}</span>
    </div>
    <div class="summary-row">
      <span>Tax (10%):</span>
      <span>₹${tax.toFixed(2)}</span>
    </div>
    <div class="summary-row summary-total">
      <span>Amount Payable:</span>
      <span>₹${total.toFixed(2)}</span>
    </div>
  `;
}

function showCartNotification(message) {
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background-color: var(--primary);
    color: var(--primary-foreground);
    padding: 1rem 1.5rem;
    border-radius: var(--radius-lg);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 100;
    animation: slideDown 300ms ease-out;
  `;
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideUp 300ms ease-out';
    setTimeout(() => notification.remove(), 300);
  }, 2000);
}

async function sendJson(url, payload) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken') || '',
    },
    credentials: 'same-origin',
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({ error: 'Invalid JSON response' }));
  return { status: response.status, data };
}

async function addToCartBackend(product) {
  if (!window.API_ADD_TO_CART_URL) return false;

  const payload = {
    product_type: product.type,
    product_id: product.id,
    quantity: 1,
  };

  const { status, data } = await sendJson(window.API_ADD_TO_CART_URL, payload);
  if (status === 200 && data.status === 'ok') {
    return true;
  }

  const errorMessage = (data && data.error) || (data && data.detail) || 'Unable to add product to cart.';
  showCartNotification(errorMessage);
  return false;
}

async function updateCartItemBackend(cartItemId, quantity) {
  if (!window.API_CART_UPDATE_URL) return false;
  const { status, data } = await sendJson(window.API_CART_UPDATE_URL, { cart_item_id: cartItemId, quantity });
  if (status === 200 && data.status === 'ok') {
    return true;
  }
  const errorMessage = (data && data.error) || 'Unable to update cart item.';
  showCartNotification(errorMessage);
  return false;
}

async function removeCartItemBackend(cartItemId) {
  if (!window.API_CART_REMOVE_URL) return false;
  const { status, data } = await sendJson(window.API_CART_REMOVE_URL, { cart_item_id: cartItemId });
  if (status === 200 && data.status === 'ok') {
    return true;
  }
  const errorMessage = (data && data.error) || 'Unable to remove cart item.';
  showCartNotification(errorMessage);
  return false;
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function isAuthenticated() {
  return window.USER_AUTHENTICATED === true || window.USER_AUTHENTICATED === 'true';
}

function setButtonLoading(button, loadingText = 'Please wait...') {
  if (!button) return;
  button.disabled = true;
  button.dataset.originalText = button.textContent;
  button.textContent = loadingText;
}

function clearButtonLoading(button) {
  if (!button) return;
  if (button.dataset.originalText) {
    button.textContent = button.dataset.originalText;
    delete button.dataset.originalText;
  }
  button.disabled = false;
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken') || '',
    },
    credentials: 'same-origin',
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({ error: 'Invalid JSON response' }));
  return { status: response.status, data };
}

async function handleCheckout() {
  if (!cart.items || cart.items.length === 0) {
    showCartNotification('Your cart is empty.');
    return;
  }

  if (!isAuthenticated()) {
    showCartNotification('Please log in before checkout.');
    setTimeout(() => {
      window.location.href = window.LOGIN_URL;
    }, 1200);
    return;
  }

  if (!window.API_CHECKOUT_URL) {
    showCartNotification('Checkout is not configured.');
    return;
  }

  let status, data;
  try {
    ({ status, data } = await postJson(window.API_CHECKOUT_URL, { payment_method: 'cash' }));
  } catch (error) {
    showCartNotification('Checkout request failed. Please refresh and try again.');
    console.error('Checkout request error:', error);
    return;
  }

  if (status === 401) {
    showCartNotification('Please log in to complete checkout.');
    setTimeout(() => {
      window.location.href = window.LOGIN_URL;
    }, 1200);
    return;
  }

  if (status === 200 && data.status === 'confirmed') {
    cart = { items: [], total_price: 0 };
    saveCart();
    renderCartItems();
    showCartNotification('Order confirmed! Thank you.');
    return;
  }

  if (status === 200 && data.status === 'payment_required' && data.payment_url) {
    showCartNotification('Redirecting to payment gateway...');
    window.location.href = data.payment_url;
    return;
  }

  const errorMessage = (data && data.error) || (data && data.detail) || 'Checkout failed. Please try again.';
  showCartNotification(errorMessage);
}

function showCheckoutForm() {
  const checkoutPhase = document.querySelector('#checkout-phase');
  const checkoutButton = document.querySelector('#checkout-button');
  const placeOrderButton = document.querySelector('#place-order-button');
  const paymentMethod = document.querySelector('input[name="payment_method"]:checked')?.value;

  if (checkoutPhase) {
    checkoutPhase.style.display = 'block';
  }
  if (checkoutButton) {
    checkoutButton.style.display = 'none';
  }
  if (placeOrderButton) {
    placeOrderButton.style.display = 'inline-flex';
    placeOrderButton.textContent = paymentMethod === 'online' ? 'Pay Online & Place Order' : 'Place Order';
  }
}

async function placeOrder() {
  if (!isAuthenticated()) {
    showCartNotification('Login required to place order.');
    setTimeout(() => {
      window.location.href = window.LOGIN_URL;
    }, 1200);
    return;
  }

  const addressLine1 = document.querySelector('#address-line1')?.value.trim();
  const addressLine2 = document.querySelector('#address-line2')?.value.trim();
  const city = document.querySelector('#address-city')?.value.trim();
  const state = document.querySelector('#address-state')?.value.trim();
  const postalCode = document.querySelector('#address-postal-code')?.value.trim();
  const country = document.querySelector('#address-country')?.value.trim();
  const paymentMethod = document.querySelector('input[name="payment_method"]:checked')?.value;
  const deliveryNotes = document.querySelector('#delivery-notes')?.value.trim();

  if (!addressLine1 || !city || !postalCode || !country || !paymentMethod) {
    showCartNotification('Please complete the shipping address and payment method.');
    return;
  }

  const placeOrderButton = document.querySelector('#place-order-button');
  setButtonLoading(placeOrderButton, 'Processing payment...');

  let status, data;
  try {
    ({ status, data } = await sendJson(window.API_CHECKOUT_URL, {
      payment_method: paymentMethod,
      shipping_address_line1: addressLine1,
      shipping_address_line2: addressLine2,
      shipping_city: city,
      shipping_state: state,
      shipping_postal_code: postalCode,
      shipping_country: country,
      delivery_notes: deliveryNotes,
    }));
  } catch (error) {
    showCartNotification('Checkout request failed. Please refresh and try again.');
    console.error('Checkout request error:', error);
    clearButtonLoading(placeOrderButton);
    return;
  }

  if (status === 401) {
    showCartNotification('Please log in to complete checkout.');
    clearButtonLoading(placeOrderButton);
    setTimeout(() => {
      window.location.href = window.LOGIN_URL;
    }, 1200);
    return;
  }

  if (status === 200 && data.status === 'confirmed') {
    await loadCart();
    clearButtonLoading(placeOrderButton);
    showCartNotification('Order confirmed! Thank you.');
    return;
  }

  if (status === 200 && data.status === 'payment_required' && data.payment_url) {
    showCartNotification('Redirecting to payment gateway...');
    clearButtonLoading(placeOrderButton);
    window.location.href = data.payment_url;
    return;
  }

  const errorMessage = (data && data.error) || (data && data.detail) || 'Checkout failed. Please try again.';
  showCartNotification(errorMessage);
  clearButtonLoading(placeOrderButton);
}

// ==================== NAVBAR ==================== 

document.addEventListener('DOMContentLoaded', () => {
  const navToggle = document.querySelector('.navbar-toggle');
  const navMobile = document.querySelector('.navbar-mobile');
  
  if (navToggle && navMobile) {
    navToggle.addEventListener('click', (event) => {
      event.stopPropagation();
      const isActive = navMobile.classList.toggle('active');
      navToggle.setAttribute('aria-expanded', isActive ? 'true' : 'false');
    });

    document.addEventListener('click', (event) => {
      if (!navMobile.contains(event.target) && !navToggle.contains(event.target)) {
        navMobile.classList.remove('active');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }
  
  const mobileLinks = document.querySelectorAll('.navbar-mobile a');
  mobileLinks.forEach(link => {
    link.addEventListener('click', () => {
      if (navMobile) {
        navMobile.classList.remove('active');
      }
      if (navToggle) {
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });
  });
  
  const cartBtn = document.querySelector('.navbar-cart-btn');
  const cartModal = document.querySelector('#cart-modal');
  const modalClose = document.querySelector('.modal-close');
  
  if (cartBtn && cartModal) {
    cartBtn.addEventListener('click', (event) => {
      event.stopPropagation();
      cartModal.classList.add('active');
      document.body.style.overflow = 'hidden';
      renderCartItems();
    });
  }
  
  if (modalClose && cartModal) {
    modalClose.addEventListener('click', () => {
      cartModal.classList.remove('active');
      document.body.style.overflow = '';
    });
  }
  
  if (cartModal) {
    cartModal.addEventListener('click', (e) => {
      if (e.target === cartModal) {
        cartModal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  }
  
  const addToCartButtons = document.querySelectorAll('[data-add-to-cart]');
  addToCartButtons.forEach(btn => {
    btn.addEventListener('click', async () => {
      const productId = parseInt(btn.getAttribute('data-product-id'));
      const productType = btn.getAttribute('data-product-type') || 'item';
      const productName = btn.getAttribute('data-product-name');
      const productPrice = parseFloat(btn.getAttribute('data-product-price'));
      
      await addToCart({
        id: productId,
        type: productType,
        name: productName,
        price: productPrice,
        emoji: btn.getAttribute('data-product-emoji')
      });
    });
  });

  const checkoutButton = document.querySelector('#checkout-button');
  if (checkoutButton) {
    checkoutButton.addEventListener('click', (event) => {
      event.preventDefault();
      showCheckoutForm();
    });
  }

  const placeOrderButton = document.querySelector('#place-order-button');
  if (placeOrderButton) {
    placeOrderButton.addEventListener('click', (event) => {
      event.preventDefault();
      placeOrder();
    });
  }

  const paymentRadios = document.querySelectorAll('input[name="payment_method"]');
  paymentRadios.forEach(radio => {
    radio.addEventListener('change', () => {
      const selectedMethod = document.querySelector('input[name="payment_method"]:checked')?.value;
      if (placeOrderButton) {
        placeOrderButton.textContent = selectedMethod === 'online' ? 'Pay Online & Place Order' : 'Place Order';
      }
    });
  });
  
  updateCartBadge();
  loadCart();
});

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href !== '#') {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
          target.scrollIntoView({ behavior: 'smooth' });
        }
      }
    });
  });

  const elements = document.querySelectorAll('.product-card, .testimonial-card, .category-card');

  if (elements.length > 0) {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
        }
      });
    }, observerOptions);

    elements.forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity 600ms ease-out, transform 600ms ease-out';
      observer.observe(el);
    });
  }
});
