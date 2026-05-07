const STORAGE_KEYS = {
  cart: 'congo_cart_v2',
  guess: 'congo_guess_state_v2',
};

const relRoot = window.CONGO_REL_ROOT || './';
const pageType = document.body.dataset.page || 'index';
const fallbackSite = window.CONGO_SITE || {};

function money(value, currency = fallbackSite.currency || 'USD') {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

function withBase(path = '') {
  if (!path) return `${relRoot}assets/placeholder.png`;
  if (/^https?:\/\//.test(path)) return path;
  return `${relRoot}${path.replace(/^\/+/, '')}`;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function getStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
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
  return state[itemId] || { attempts: 0, success: false, lastGuess: null, offerPrice: null };
}

function updateGuessEntry(itemId, next) {
  const state = getGuessState();
  state[itemId] = next;
  setStorage(STORAGE_KEYS.guess, state);
}

function hydrateCartCount() {
  const cart = getCart();
  const count = Object.values(cart).reduce((sum, row) => sum + Number(row.qty || 0), 0);
  document.querySelectorAll('[data-cart-count]').forEach((node) => {
    node.textContent = String(count);
  });
}

function normalizePrice(value) {
  return Math.round(Number(value || 0) * 100) / 100;
}

function itemReadyForGuessing(item) {
  return item?.status === 'available' && item?.actualPrice !== null && item?.actualPrice !== undefined && Number(item.actualPrice) > 0;
}

function computeOfferPrice(item, guess, site) {
  const actual = Number(item.actualPrice || 0);
  const factor = Number(site.discountFactor ?? 0.8);
  if (guess <= actual) return normalizePrice(actual);
  return normalizePrice(actual + (guess - actual) * factor);
}

async function fetchCatalog() {
  const response = await fetch(`${relRoot}data/catalog.json`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Could not load catalog.json');
  return response.json();
}

function slugToPath(id) {
  return `${relRoot}item/${encodeURIComponent(id)}/`;
}

function buildIndexUrl({ query = '', category = '' } = {}) {
  const url = new URL(`${window.location.origin}${relRoot}`);
  if (query) url.searchParams.set('q', query);
  if (category && category !== 'All') url.searchParams.set('category', category);
  return `${url.pathname}${url.search}`;
}

function renderCategoryChips(items, activeCategory = 'All') {
  const host = document.getElementById('category-chips');
  if (!host) return;
  const categories = ['All', ...Array.from(new Set(items.map((item) => item.category))).sort()];
  host.innerHTML = categories
    .map((category) => {
      const active = category === activeCategory ? 'active' : '';
      const href = buildIndexUrl({
        query: new URLSearchParams(window.location.search).get('q') || '',
        category,
      });
      const tag = pageType === 'index' ? 'button' : 'a';
      const extra = pageType === 'index'
        ? `type="button" data-category="${escapeHtml(category)}"`
        : `href="${escapeHtml(href)}"`;
      return `<${tag} class="category-chip ${active}" ${extra}>${escapeHtml(category)}</${tag}>`;
    })
    .join('');
}

function attachGlobalSearch() {
  const input = document.getElementById('global-search');
  const button = document.getElementById('global-search-button');
  if (!input || !button) return;

  const runSearch = () => {
    const query = input.value.trim();
    if (pageType === 'index') {
      input.dispatchEvent(new Event('input', { bubbles: true }));
      return;
    }
    window.location.href = buildIndexUrl({ query });
  };

  button.addEventListener('click', runSearch);
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      runSearch();
    }
  });
}

function getItemPrimaryImage(item) {
  if (Array.isArray(item?.images) && item.images.length) return item.images[0];
  return item?.image || '';
}

function productCard(item, site) {
  const guessEntry = getGuessEntry(item.id);
  const unlocked = guessEntry.success;
  const sold = !itemReadyForGuessing(item);
  const unlockedText = unlocked
    ? `Unlocked offer: ${money(guessEntry.offerPrice ?? item.actualPrice, site.currency)}`
    : 'Price hidden until you guess high enough';
  return `
    <article class="product-card ${sold ? 'is-sold' : ''}">
      <a class="product-card-link" href="${slugToPath(item.id)}" aria-label="View ${escapeHtml(item.name)} deal">
        <div class="card-image-wrap">
          <div class="badge-row">
            <span class="badge gold">${escapeHtml(item.category)}</span>
            <span class="badge ${sold ? '' : 'green'}">${sold ? 'Unavailable' : '3 chances'}</span>
          </div>
          <img src="${withBase(getItemPrimaryImage(item))}" alt="${escapeHtml(item.name)}" loading="lazy" onerror="this.src='${relRoot}assets/placeholder.png'"/>
        </div>
        <div class="product-card-body">
          <div class="eyebrow">${escapeHtml(item.condition || 'Used')}</div>
          <h3>${escapeHtml(item.name)}</h3>
          <div class="price-stack">
            <div class="hidden-price">${escapeHtml(unlockedText)}</div>
          </div>
          <div class="small-note">${escapeHtml(item.description || '')}</div>
        </div>
      </a>
    </article>
  `;
}

function renderIndex(catalog) {
  const site = catalog.site;
  const items = catalog.items || [];
  const grid = document.getElementById('catalog-grid');
  const searchInput = document.getElementById('global-search');
  const freeDeliveryNode = document.getElementById('delivery-threshold-copy');
  const activeFilters = {
    category: new URLSearchParams(window.location.search).get('category') || 'All',
    query: new URLSearchParams(window.location.search).get('q') || '',
  };

  if (searchInput) searchInput.value = activeFilters.query;
  if (freeDeliveryNode) freeDeliveryNode.textContent = money(site.freeDeliveryThreshold, site.currency);

  function draw(pushState = false) {
    renderCategoryChips(items, activeFilters.category);
    const filtered = items.filter((item) => {
      const matchCategory = activeFilters.category === 'All' || item.category === activeFilters.category;
      const needle = activeFilters.query.trim().toLowerCase();
      const hay = [item.name, item.category, item.description, item.condition].join(' ').toLowerCase();
      const matchQuery = !needle || hay.includes(needle);
      return matchCategory && matchQuery;
    });

    if (pushState) {
      const url = buildIndexUrl({ query: activeFilters.query, category: activeFilters.category });
      window.history.replaceState({}, '', url);
    }

    if (!grid) return;

    if (!filtered.length) {
      grid.innerHTML = `
        <div class="empty-state">
          <h3>No items matched that search.</h3>
          <p class="muted">Try another keyword or another category.</p>
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
    draw(true);
  });

  if (searchInput) {
    searchInput.addEventListener('input', (event) => {
      activeFilters.query = event.target.value;
      draw(true);
    });
  }
}

function addToCart(item, quantity = 1) {
  const guessEntry = getGuessEntry(item.id);
  const cart = getCart();
  cart[item.id] = {
    qty: Math.min((cart[item.id]?.qty || 0) + quantity, item.quantity || 1),
    offerPrice: normalizePrice(guessEntry.offerPrice ?? item.actualPrice),
    guess: guessEntry.lastGuess,
  };
  setCart(cart);
}

function removeFromCart(itemId) {
  const cart = getCart();
  delete cart[itemId];
  setCart(cart);
}

function setItemUnlockedUI(item, site, offerPrice) {
  const reveal = document.getElementById('reveal-price');
  const actionBlock = document.getElementById('unlock-actions');
  const status = document.getElementById('guess-status');
  const remaining = document.getElementById('remaining-guesses');
  const hiddenHint = document.getElementById('hidden-price-hint');
  const factor = Number(site.discountFactor ?? 0.8);

  if (reveal) {
    reveal.classList.remove('hide');
    reveal.querySelector('[data-offer-price]').textContent = money(offerPrice, site.currency);
  }
  if (actionBlock) actionBlock.classList.remove('hide');
  if (hiddenHint) {
    hiddenHint.textContent = offerPrice > Number(item.actualPrice)
      ? `Unlocked from an above-target guess using discount factor ${factor}.`
      : 'Unlocked at the seller price.';
  }
  if (status) {
    status.className = 'status-box good';
    status.textContent = 'Yes — that guess works. The unlocked checkout price is shown below.';
  }
  if (remaining) remaining.textContent = 'Unlocked';
}

function renderItemPage(catalog) {
  const site = catalog.site;
  const current = window.CONGO_CURRENT_ITEM;
  if (!current) return;

  const galleryButtons = Array.from(document.querySelectorAll('[data-gallery-image]'));
  const mainImage = document.getElementById('item-main-image');
  if (galleryButtons.length && mainImage) {
    galleryButtons.forEach((button) => {
      button.addEventListener('click', () => {
        const nextSrc = button.dataset.galleryImage;
        if (!nextSrc) return;
        mainImage.src = withBase(nextSrc);
        galleryButtons.forEach((node) => node.classList.remove('active'));
        button.classList.add('active');
      });
    });
  }

  const input = document.getElementById('guess-input');
  const button = document.getElementById('guess-button');
  const addButton = document.getElementById('add-to-cart');
  const buyButton = document.getElementById('buy-now');
  const remaining = document.getElementById('remaining-guesses');
  const status = document.getElementById('guess-status');
  const hiddenHint = document.getElementById('hidden-price-hint');

  function refreshState() {
    const entry = getGuessEntry(current.id);
    if (!itemReadyForGuessing(current)) {
      if (status) {
        status.className = 'status-box warn';
        status.textContent = 'This item is not ready for offers yet.';
      }
      if (hiddenHint) hiddenHint.textContent = 'Seller has not enabled guessing for this item yet.';
      if (input) input.disabled = true;
      if (button) button.disabled = true;
      return;
    }

    if (entry.success) {
      setItemUnlockedUI(current, site, entry.offerPrice ?? current.actualPrice);
      if (input) input.disabled = true;
      if (button) button.disabled = true;
      return;
    }

    const attemptsLeft = Math.max(0, 3 - entry.attempts);
    if (remaining) remaining.textContent = String(attemptsLeft);
    if (attemptsLeft === 0) {
      if (status) {
        status.className = 'status-box bad';
        status.textContent = 'That was the last try from this browser. If you still want it, email the seller directly.';
      }
      if (hiddenHint) hiddenHint.textContent = 'No guesses left on this browser.';
      if (input) input.disabled = true;
      if (button) button.disabled = true;
    }
  }

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
        const offerPrice = computeOfferPrice(current, value, site);
        updateGuessEntry(current.id, {
          attempts: entry.attempts + 1,
          success: true,
          lastGuess: value,
          offerPrice,
        });
        setItemUnlockedUI(current, site, offerPrice);
        if (input) input.disabled = true;
        if (button) button.disabled = true;
      } else {
        const nextAttempts = entry.attempts + 1;
        updateGuessEntry(current.id, {
          attempts: nextAttempts,
          success: false,
          lastGuess: value,
          offerPrice: null,
        });
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
    ...cartRows.map((row) => `- ${row.name} — ${money(row.offerPrice, site.currency)}${row.guess ? ` (guessed ${money(row.guess, site.currency)})` : ''}`),
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
      .map(([id, cartRow]) => {
        const item = itemMap.get(id);
        if (!item || !itemReadyForGuessing(item)) return null;
        return {
          ...item,
          qty: Number(cartRow.qty || 1),
          offerPrice: normalizePrice(cartRow.offerPrice ?? item.actualPrice),
          guess: cartRow.guess ?? null,
        };
      })
      .filter(Boolean);

    const total = rows.reduce((sum, row) => sum + Number(row.offerPrice) * Number(row.qty || 1), 0);
    const count = rows.reduce((sum, row) => sum + Number(row.qty || 1), 0);
    const threshold = Number(site.freeDeliveryThreshold || 0);
    const progress = threshold > 0 ? Math.min(100, Math.round((total / threshold) * 100)) : 100;

    if (summaryTotal) summaryTotal.textContent = money(total, site.currency);
    if (summaryCount) summaryCount.textContent = String(count);
    if (summaryMessage) {
      summaryMessage.className = total >= threshold ? 'status-box good' : 'status-box info';
      summaryMessage.textContent = total >= threshold
        ? 'Free local delivery unlocked on this order.'
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
            <img src="${withBase(getItemPrimaryImage(row))}" alt="${escapeHtml(row.name)}" onerror="this.src='${relRoot}assets/placeholder.png'"/>
          </div>
          <div>
            <h3 style="margin:0 0 6px">${escapeHtml(row.name)}</h3>
            <div class="muted">${escapeHtml(row.category)} · ${escapeHtml(row.condition || 'Used')}</div>
            <div class="small-note" style="margin-top:8px">${row.guess ? `Unlocked from guess ${money(row.guess, site.currency)}.` : 'Unlocked price ready.'}</div>
          </div>
          <div style="display:grid;gap:10px;justify-items:end">
            <div class="price-line">${money(row.offerPrice, site.currency)}</div>
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
    if (!form) return '';
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
      } catch {
        copyButton.textContent = 'Copy failed';
      }
    });
  }

  writeEmailTargets();
}

function boot() {
  hydrateCartCount();
  attachGlobalSearch();
  fetchCatalog()
    .then((catalog) => {
      renderCategoryChips(catalog.items || [], new URLSearchParams(window.location.search).get('category') || 'All');
      if (pageType === 'index') renderIndex(catalog);
      if (pageType === 'item') renderItemPage(catalog);
      if (pageType === 'checkout') renderCheckout(catalog);
    })
    .catch((error) => {
      const host = document.getElementById('page-error');
      if (host) {
        host.classList.remove('hide');
        host.textContent = `Failed to load the catalog: ${error.message}`;
      }
    });
}

boot();
