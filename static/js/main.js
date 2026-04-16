// ==================== CART MANAGEMENT ====================

let cart = JSON.parse(localStorage.getItem('cart')) || [];

function updateCartBadge() {
  const badge = document.querySelector('.cart-badge');
  const cartBtn = document.querySelector('.navbar-cart-btn');
  const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
  
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
  localStorage.setItem('cart', JSON.stringify(cart));
  updateCartBadge();
}

function addToCart(product) {
  const existingItem = cart.find(item => item.id === product.id);
  
  if (existingItem) {
    existingItem.quantity += 1;
  } else {
    cart.push({ ...product, quantity: 1 });
  }
  
  saveCart();
  showCartNotification('Added to cart!');
}

function removeFromCart(productId) {
  cart = cart.filter(item => item.id !== productId);
  saveCart();
  renderCartItems();
}

function updateQuantity(productId, change) {
  const item = cart.find(item => item.id === productId);
  if (item) {
    item.quantity = Math.max(1, item.quantity + change);
    saveCart();
    renderCartItems();
  }
}

function renderCartItems() {
  const cartItemsContainer = document.querySelector('.cart-items');
  
  if (!cartItemsContainer) return;
  
  if (cart.length === 0) {
    cartItemsContainer.innerHTML = `
      <div class="cart-empty">
        <p>Your cart is empty</p>
        <p style="font-size: 3rem;">🛒</p>
      </div>
    `;
    updateCartSummary();
    return;
  }
  
  cartItemsContainer.innerHTML = cart.map(item => `
    <div class="cart-item">
      <div class="cart-item-info">
        <div class="cart-item-name">${item.name}</div>
        <div class="cart-item-price">₹${item.price}</div>
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
  
  const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
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
  // Create simple notification
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

// ==================== NAVBAR ==================== 

document.addEventListener('DOMContentLoaded', () => {
  // Mobile menu toggle
  const navToggle = document.querySelector('.navbar-toggle');
  const navMobile = document.querySelector('.navbar-mobile');
  
  if (navToggle && navMobile) {
    navToggle.addEventListener('click', (event) => {
      event.stopPropagation();
      const isActive = navMobile.classList.toggle('active');
      navToggle.setAttribute('aria-expanded', isActive ? 'true' : 'false');
    });

    // Close mobile menu when clicking outside the menu
    document.addEventListener('click', (event) => {
      if (!navMobile.contains(event.target) && !navToggle.contains(event.target)) {
        navMobile.classList.remove('active');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }
  
  // Close mobile menu when clicking on links
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
  
  // Cart modal
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
  
  // Close modal when clicking outside
  if (cartModal) {
    cartModal.addEventListener('click', (e) => {
      if (e.target === cartModal) {
        cartModal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  }
  
  // Add to cart buttons
  const addToCartButtons = document.querySelectorAll('[data-add-to-cart]');
  addToCartButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const productId = parseInt(btn.getAttribute('data-product-id'));
      const productName = btn.getAttribute('data-product-name');
      const productPrice = parseFloat(btn.getAttribute('data-product-price'));
      
      addToCart({
        id: productId,
        name: productName,
        price: productPrice,
        emoji: btn.getAttribute('data-product-emoji')
      });
    });
  });
  
  // Initialize cart badge
  updateCartBadge();
});

document.addEventListener('DOMContentLoaded', () => {

  // ==================== SMOOTH SCROLL ====================
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

  // ==================== ANIMATIONS ====================
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