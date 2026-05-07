const STORAGE_KEYS = {
  cart: 'congo_cart_v1',
  guess: 'congo_guess_state_v1',
};

const relRoot = window.CONGO_REL_ROOT || './';
const pageType = document.body.dataset.page || 'index';
const fallbackSite = window.CONGO_SITE || {};

function money(value, currency = fallbackSite.currency || 'USD') {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

function withBase(path = '') {
  if (!path) return `${relRoot}assets/placeholder.png`;
  if (/^https?:\/\//.test(path)) return path;
  return `${relRoot}${path.replace(/^\/+/, '')}`;
}

function getStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (error) {
    return fallback;
  }
}

function setStorage(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function getCart() {
  return getStorage(STORAGE_KEYS.cart, {});
}

function setCart(cart) {
  setStorage(STORAGE_KEYS.cart, cart);
  hydrateCartCount();
}

function getGuessState() {
  return getStorage(STORAGE_KEYS.guess, {});
}

function getGuessEntry(itemId) {
  const state = getGuessState();
  return state[itemId] || { attempts: 0, success: false, lastGuess: null };
}

function updateGuessEntry(itemId, next) {
  const state = getGuessState();
  state[itemId] = next;
  setStorage(STORAGE_KEYS.guess, state);
}

function hydrateCartCount() {
  const cart = getCart();
  const count = Object.values(cart).reduce((sum, qty) => sum + qty, 0);
  document.querySelectorAll('[data-cart-count]').forEach((node) => {
    node.textContent = String(count);
  });
}

async function fetchCatalog() {
  const response = await fetch(`${relRoot}data/catalog.json`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Could not load catalog.json');
  return response.json();
}

function slugToPath(id) {
  return `${relRoot}item/${encodeURIComponent(id)}/`;
}

function renderCategoryChips(items, activeCategory = 'All') {
  const host = document.getElementById('category-chips');
  if (!host) return;
  const categories = ['All', ...Array.from(new Set(items.map((item) => item.category))).sort()];
  host.innerHTML = categories
    .map((category) => `
      <button class="category-chip ${category === activeCategory ? 'active' : ''}" data-category="${escapeHtml(category)}">
        ${escapeHtml(category)}
      </button>
    `)
    .join('');
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function productCard(item, site) {
  const guessEntry = getGuessEntry(item.id);
  const unlocked = guessEntry.success;
  const sold = item.status !== 'available';
  return `
    <article class="product-card">
      <a class="card-image-wrap" href="${slugToPath(item.id)}">
        <div class="badge-row">
          <span class="badge gold">${escapeHtml(item.category)}</span>
          <span class="badge ${sold ? '' : 'green'}">${sold ? 'Unavailable' : '3 chances'}</span>
        </div>
        <img src="${withBase(item.image)}" alt="${escapeHtml(item.name)}" loading="lazy" onerror="this.src='${relRoot}assets/placeholder.png'"/>
      </a>
      <div class="product-card-body">
        <div class="eyebrow">${escapeHtml(item.condition || 'Used')}</div>
        <h3><a href="${slugToPath(item.id)}">${escapeHtml(item.name)}</a></h3>
        <div class="price-stack">
          <div class="reference">Reference online: ${money(item.referencePrice, site.currency)}</div>
          <div class="hidden-price">${unlocked ? `Unlocked price: ${money(item.actualPrice, site.currency)}` : 'Price hidden until you guess high enough'}</div>
        </div>
        <div class="small-note">${escapeHtml(item.description || '')}</div>
        <div class="card-actions">
          <a class="btn-amazon" href="${slugToPath(item.id)}">View deal</a>
          <a class="btn-ghost" href="${escapeHtml(item.referenceLink)}" target="_blank" rel="noreferrer">Reference</a>
        </div>
      </div>
    </article>
  `;
}

function renderIndex(catalog) {
  const site = catalog.site;
  const items = catalog.items || [];
  const grid = document.getElementById('catalog-grid');
  const searchInput = document.getElementById('global-search');
  const heroCount = document.getElementById('hero-item-count');
  const thresholdNode = document.getElementById('hero-threshold');
  const activeFilters = { category: 'All', query: '' };

  if (heroCount) heroCount.textContent = String(items.length);
  if (thresholdNode) thresholdNode.textContent = money(site.freeDeliveryThreshold, site.currency);

  function draw() {
    renderCategoryChips(items, activeFilters.category);
    const filtered = items.filter((item) => {
      const matchCategory = activeFilters.category === 'All' || item.category === activeFilters.category;
      const needle = activeFilters.query.trim().toLowerCase();
      const hay = [item.name, item.category, item.description, item.condition].join(' ').toLowerCase();
      const matchQuery = !needle || hay.includes(needle);
      return matchCategory && matchQuery;
    });

    if (!grid) return;

    if (!filtered.length) {
      grid.innerHTML = `
        <div class="empty-state">
          <h3>No items matched that search.</h3>
          <p class="muted">Try another keyword or switch the category filter.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = filtered.map((item) => productCard(item, site)).join('');
  }

  draw();

  document.addEventListener('click', (event) => {
    const button = event.target.closest('[data-category]');
    if (!button) return;
    activeFilters.category = button.dataset.category;
    draw();
  });

  if (searchInput) {
    searchInput.addEventListener('input', (event) => {
      activeFilters.query = event.target.value;
      draw();
    });
  }
}

function addToCart(item, quantity = 1) {
  const cart = getCart();
  cart[item.id] = Math.min((cart[item.id] || 0) + quantity, item.quantity || 1);
  setCart(cart);
}

function removeFromCart(itemId) {
  const cart = getCart();
  delete cart[itemId];
  setCart(cart);
}

function setItemUnlockedUI(item, site) {
  const reveal = document.getElementById('reveal-price');
  const actionBlock = document.getElementById('unlock-actions');
  const status = document.getElementById('guess-status');
  const remaining = document.getElementById('remaining-guesses');
  const hiddenHint = document.getElementById('hidden-price-hint');
  if (reveal) {
    reveal.classList.remove('hide');
    reveal.querySelector('[data-actual-price]').textContent = money(item.actualPrice, site.currency);
  }
  if (actionBlock) actionBlock.classList.remove('hide');
  if (hiddenHint) hiddenHint.textContent = 'Price unlocked.';
  if (status) {
    status.className = 'status-box good';
    status.textContent = 'Yes — that guess works. You can add the item to cart or go straight to checkout.';
  }
  if (remaining) remaining.textContent = 'Unlocked';
}

function renderItemPage(catalog) {
  const site = catalog.site;
  const current = window.CONGO_CURRENT_ITEM;
  if (!current) return;

  const input = document.getElementById('guess-input');
  const button = document.getElementById('guess-button');
  const addButton = document.getElementById('add-to-cart');
  const buyButton = document.getElementById('buy-now');
  const remaining = document.getElementById('remaining-guesses');
  const status = document.getElementById('guess-status');
  const hiddenHint = document.getElementById('hidden-price-hint');
  const guessEntry = getGuessEntry(current.id);

  function refreshState() {
    const entry = getGuessEntry(current.id);
    if (entry.success) {
      setItemUnlockedUI(current, site);
      if (input) input.disabled = true;
      if (button) button.disabled = true;
      return;
    }

    const attemptsLeft = Math.max(0, 3 - entry.attempts);
    if (remaining) remaining.textContent = String(attemptsLeft);
    if (attemptsLeft === 0) {
      if (status) {
        status.className = 'status-box bad';
        status.textContent = 'That was the last try from this browser. If you still want it, send an email from the checkout page or clear local storage and start over.';
      }
      if (hiddenHint) hiddenHint.textContent = 'No guesses left.';
      if (input) input.disabled = true;
      if (button) button.disabled = true;
    }
  }

  if (guessEntry.success) setItemUnlockedUI(current, site);
  refreshState();

  if (button) {
    button.addEventListener('click', () => {
      const entry = getGuessEntry(current.id);
      if (entry.success || entry.attempts >= 3) return;
      const value = Number(input.value);
      if (!Number.isFinite(value) || value < 0) {
        status.className = 'status-box warn';
        status.textContent = 'Enter a valid dollar amount first.';
        return;
      }

      if (value >= Number(current.actualPrice)) {
        updateGuessEntry(current.id, { attempts: entry.attempts + 1, success: true, lastGuess: value });
        setItemUnlockedUI(current, site);
        if (input) input.disabled = true;
        if (button) button.disabled = true;
      } else {
        const nextAttempts = entry.attempts + 1;
        updateGuessEntry(current.id, { attempts: nextAttempts, success: false, lastGuess: value });
        const attemptsLeft = Math.max(0, 3 - nextAttempts);
        status.className = attemptsLeft ? 'status-box info' : 'status-box bad';
        status.textContent = attemptsLeft
          ? `Too low. Try again — ${attemptsLeft} chance${attemptsLeft === 1 ? '' : 's'} left.`
          : 'Too low, and that was the last chance on this browser.';
        if (hiddenHint) hiddenHint.textContent = 'Still hidden — the guess needs to be higher.';
        refreshState();
      }
    });
  }

  if (addButton) {
    addButton.addEventListener('click', () => {
      addToCart(current, 1);
      addButton.textContent = 'Added';
      addButton.disabled = true;
      hydrateCartCount();
    });
  }

  if (buyButton) {
    buyButton.addEventListener('click', () => {
      addToCart(current, 1);
      window.location.href = `${relRoot}checkout/`;
    });
  }
}

function buildCheckoutEmail({ cartRows, total, site, form }) {
  const deliveryEligible = total >= Number(site.freeDeliveryThreshold || 0);
  const lines = [
    `Hi ${site.ownerName || 'seller'},`,
    '',
    'I would like to buy these items from Congo:',
    '',
    ...cartRows.map((row) => `- ${row.name} — ${money(row.actualPrice, site.currency)}`),
    '',
    `Total: ${money(total, site.currency)}`,
    deliveryEligible
      ? `This order is above ${money(site.freeDeliveryThreshold, site.currency)}, so it qualifies for free local delivery.`
      : `This order is below ${money(site.freeDeliveryThreshold, site.currency)}. Pickup is fine, or we can discuss delivery.`,
    '',
    `Preferred option: ${form.deliveryMode}`,
    `Preferred time: ${form.when || 'To be discussed'}`,
    `Name: ${form.name || ''}`,
    `Email: ${form.email || ''}`,
    `Phone: ${form.phone || ''}`,
    `Address / meeting point: ${form.address || ''}`,
    '',
    'Notes:',
    form.notes || 'None',
    '',
    'Thanks!',
  ];
  return lines.join('\n');
}

function renderCheckout(catalog) {
  const site = catalog.site;
  const items = catalog.items || [];
  const itemMap = new Map(items.map((item) => [item.id, item]));
  const cartList = document.getElementById('cart-list');
  const summaryTotal = document.getElementById('summary-total');
  const summaryCount = document.getElementById('summary-count');
  const summaryMessage = document.getElementById('delivery-message');
  const progressFill = document.getElementById('delivery-progress');
  const form = document.getElementById('checkout-form');
  const copyButton = document.getElementById('copy-email');
  const mailtoButton = document.getElementById('open-mailto');
  const clearButton = document.getElementById('clear-cart');

  function draw() {
    const rawCart = getCart();
    const rows = Object.entries(rawCart)
      .map(([id, qty]) => {
        const item = itemMap.get(id);
        if (!item) return null;
        return { ...item, qty };
      })
      .filter(Boolean);

    const total = rows.reduce((sum, row) => sum + Number(row.actualPrice) * Number(row.qty || 1), 0);
    const count = rows.reduce((sum, row) => sum + Number(row.qty || 1), 0);
    const threshold = Number(site.freeDeliveryThreshold || 0);
    const progress = threshold > 0 ? Math.min(100, Math.round((total / threshold) * 100)) : 100;

    if (summaryTotal) summaryTotal.textContent = money(total, site.currency);
    if (summaryCount) summaryCount.textContent = String(count);
    if (summaryMessage) {
      summaryMessage.className = total >= threshold ? 'status-box good' : 'status-box info';
      summaryMessage.textContent = total >= threshold
        ? `Free local delivery unlocked on this order.`
        : `Add ${money(Math.max(0, threshold - total), site.currency)} more to reach free local delivery.`;
    }
    if (progressFill) progressFill.style.width = `${progress}%`;

    if (!cartList) return { rows, total };

    if (!rows.length) {
      cartList.innerHTML = `
        <div class="empty-state">
          <h3>Your cart is empty.</h3>
          <p class="muted">Unlock an item first, then add it to cart.</p>
          <p><a class="btn-amazon" href="${relRoot}">Back to the catalog</a></p>
        </div>
      `;
      return { rows, total };
    }

    cartList.innerHTML = rows
      .map((row) => `
        <article class="cart-item">
          <div class="cart-thumb">
            <img src="${withBase(row.image)}" alt="${escapeHtml(row.name)}" onerror="this.src='${relRoot}assets/placeholder.png'"/>
          </div>
          <div>
            <h3 style="margin:0 0 6px">${escapeHtml(row.name)}</h3>
            <div class="muted">${escapeHtml(row.category)} · ${escapeHtml(row.condition || 'Used')}</div>
            <div class="small-note" style="margin-top:8px">Reference: <a class="reference-link" href="${escapeHtml(row.referenceLink)}" target="_blank" rel="noreferrer">${money(row.referencePrice, site.currency)}</a></div>
          </div>
          <div style="display:grid;gap:10px;justify-items:end">
            <div class="price-line">${money(row.actualPrice, site.currency)}</div>
            <button class="btn-ghost" data-remove-item="${escapeHtml(row.id)}">Remove</button>
          </div>
        </article>
      `)
      .join('');

    return { rows, total };
  }

  let state = draw();

  document.addEventListener('click', (event) => {
    const remove = event.target.closest('[data-remove-item]');
    if (remove) {
      removeFromCart(remove.dataset.removeItem);
      state = draw();
      return;
    }
  });

  if (clearButton) {
    clearButton.addEventListener('click', () => {
      setCart({});
      state = draw();
    });
  }

  function getFormData() {
    const fd = new FormData(form);
    return {
      name: fd.get('name')?.toString().trim(),
      email: fd.get('email')?.toString().trim(),
      phone: fd.get('phone')?.toString().trim(),
      when: fd.get('when')?.toString().trim(),
      deliveryMode: fd.get('deliveryMode')?.toString().trim() || 'Pickup',
      address: fd.get('address')?.toString().trim(),
      notes: fd.get('notes')?.toString().trim(),
    };
  }

  function writeEmailTargets() {
    state = draw();
    const formData = getFormData();
    const body = buildCheckoutEmail({ cartRows: state.rows, total: state.total, site, form: formData });
    const subject = `Congo order request (${state.rows.length} item${state.rows.length === 1 ? '' : 's'})`;
    if (mailtoButton) {
      mailtoButton.href = `mailto:${encodeURIComponent(site.contactEmail)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    }
    return body;
  }

  if (form) {
    form.addEventListener('input', writeEmailTargets);
    form.addEventListener('submit', (event) => event.preventDefault());
  }

  if (copyButton) {
    copyButton.addEventListener('click', async () => {
      const body = writeEmailTargets();
      try {
        await navigator.clipboard.writeText(body);
        copyButton.textContent = 'Copied';
        setTimeout(() => (copyButton.textContent = 'Copy email text'), 1800);
      } catch (error) {
        copyButton.textContent = 'Copy failed';
      }
    });
  }

  writeEmailTargets();
}

function attachQuickSearchJump() {
  const heroSearch = document.getElementById('hero-search');
  const globalSearch = document.getElementById('global-search');
  if (!heroSearch || !globalSearch) return;
  heroSearch.addEventListener('click', () => {
    globalSearch.focus();
    globalSearch.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
}

async function boot() {
  hydrateCartCount();
  attachQuickSearchJump();
  const catalog = await fetchCatalog();
  if (pageType === 'index') renderIndex(catalog);
  if (pageType === 'item') renderItemPage(catalog);
  if (pageType === 'checkout') renderCheckout(catalog);
}

boot().catch((error) => {
  const host = document.getElementById('page-error');
  if (host) {
    host.classList.remove('hide');
    host.textContent = `Failed to load the catalog: ${error.message}`;
  }
});
