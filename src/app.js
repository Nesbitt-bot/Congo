const STORAGE_KEYS = {
  cart: 'congo_cart_v3',
  guess: 'congo_guess_state_v3',
};

const assetRoot = window.CONGO_ASSET_ROOT || './';
const pageRoot = window.CONGO_PAGE_ROOT || './';
const dataUrl = window.CONGO_DATA_URL || `${pageRoot}data/catalog.json`;
const pageType = document.body.dataset.page || 'index';
const fallbackSite = window.CONGO_SITE || {};
const STRINGS = fallbackSite.strings || {};

const requestMode = new URLSearchParams(window.location.search).get('mode');
const siteGuessEnabled = fallbackSite.priceGuessEnabled !== false;

function currentMode() {
  if (!siteGuessEnabled) return 'plain';
  return requestMode === 'guess' ? 'guess' : 'plain';
}

function isGuessMode() {
  return currentMode() === 'guess';
}

function appendMode(url) {
  const parsed = new URL(url, window.location.href);
  parsed.searchParams.set('mode', currentMode());
  return `${parsed.pathname}${parsed.search}`;
}

function t(key, fallback, vars = {}) {
  const template = STRINGS[key] ?? fallback;
  return String(template).replace(/\{(\w+)\}/g, (_, name) => String(vars[name] ?? `{${name}}`));
}

function money(value, currency = fallbackSite.currency || 'USD') {
  return new Intl.NumberFormat(fallbackSite.numberLocale || 'en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

function withBase(path = '') {
  if (!path) return `${assetRoot}assets/placeholder.png`;
  if (/^https?:\/\//.test(path)) return path;
  return `${assetRoot}${path.replace(/^\/+/, '')}`;
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
  const response = await fetch(dataUrl, { cache: 'no-store' });
  if (!response.ok) throw new Error('Could not load catalog.json');
  return response.json();
}

function slugToPath(id) {
  return appendMode(`${pageRoot}item/${encodeURIComponent(id)}/`);
}

function buildIndexUrl({ query = '', category = '' } = {}) {
  const url = new URL(pageRoot, window.location.href);
  if (query) url.searchParams.set('q', query);
  if (category && category !== t('allCategory', 'All')) url.searchParams.set('category', category);
  url.searchParams.set('mode', currentMode());
  return `${url.pathname}${url.search}`;
}

function getItemPrimaryImage(item) {
  if (Array.isArray(item?.images) && item.images.length) return item.images[0];
  return item?.image || '';
}

function getPublicNegotiablePrice(item) {
  if (item?.generatedPrice !== null && item?.generatedPrice !== undefined) return Number(item.generatedPrice);
  if (!itemReadyForGuessing(item)) return Number(item?.referencePrice || 0);
  const actual = Number(item.actualPrice || 0);
  const reference = Number(item.referencePrice || actual);
  if (reference <= actual) return actual;
  let hash = 0;
  const key = `public-price::${item.id || ''}`;
  for (let i = 0; i < key.length; i += 1) {
    hash = ((hash << 5) - hash + key.charCodeAt(i)) >>> 0;
  }
  const ratio = hash / 0xFFFFFFFF;
  return Math.round(actual + (reference - actual) * ratio);
}

function renderCategoryChips(items, activeCategory = t('allCategory', 'All')) {
  const host = document.getElementById('category-chips');
  if (!host) return;
  const categories = [t('allCategory', 'All'), ...Array.from(new Set(items.map((item) => item.category))).sort()];
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


function attachLanguageSwitch() {
  const select = document.querySelector('[data-language-switch]');
  if (!select) return;
  select.addEventListener('change', () => {
    if (select.value) window.location.href = select.value;
  });
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

function productCard(item, site) {
  const guessEntry = getGuessEntry(item.id);
  const unlocked = guessEntry.success;
  const sold = !itemReadyForGuessing(item);
  const badgeText = item.status === 'pending'
    ? t('statusPending', 'pending')
    : sold
      ? t('statusUnavailable', 'Unavailable')
      : t('threeChances', '3 chances');
  const unlockedText = !isGuessMode()
    ? `${t('listedPrice', 'Listed price')}: ${money(item.actualPrice ?? getPublicNegotiablePrice(item), site.currency)}`
    : unlocked
      ? t('unlockedOffer', 'Unlocked offer: {price}', { price: money(guessEntry.offerPrice ?? item.actualPrice, site.currency) })
      : t('generatedNegotiablePrice', '{price} (negotiable)', { price: money(getPublicNegotiablePrice(item), site.currency) });
  return `
    <article class="product-card ${sold ? 'is-sold' : ''}">
      <a class="product-card-link" href="${slugToPath(item.id)}" aria-label="View ${escapeHtml(item.name)} deal">
        <div class="card-image-wrap">
          <div class="badge-row">
            <span class="badge gold">${escapeHtml(item.category)}</span>
            <span class="badge ${itemReadyForGuessing(item) ? 'green' : ''}">${escapeHtml(badgeText)}</span>
          </div>
          <img src="${withBase(getItemPrimaryImage(item))}" alt="${escapeHtml(item.name)}" loading="lazy" onerror="this.src='${assetRoot}assets/placeholder.png'"/>
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

function renderModeChooser() {
  const guess = document.getElementById('mode-guess-link');
  const plain = document.getElementById('mode-plain-link');
  if (!guess || !plain) return;
  const guessUrl = new URL(pageRoot, window.location.href);
  guessUrl.searchParams.set('mode', 'guess');
  const plainUrl = new URL(pageRoot, window.location.href);
  plainUrl.searchParams.set('mode', 'plain');
  guess.href = `${guessUrl.pathname}${guessUrl.search}`;
  plain.href = `${plainUrl.pathname}${plainUrl.search}`;
  if (currentMode() === 'guess') {
    guess.classList.add('active-mode');
    plain.classList.remove('active-mode');
  } else {
    plain.classList.add('active-mode');
    guess.classList.remove('active-mode');
  }
}

function renderIndex(catalog) {
  const site = catalog.site;
  const items = catalog.items || [];
  const grid = document.getElementById('catalog-grid');
  const searchInput = document.getElementById('global-search');
  const activeFilters = {
    category: new URLSearchParams(window.location.search).get('category') || t('allCategory', 'All'),
    query: new URLSearchParams(window.location.search).get('q') || '',
  };

  if (searchInput) searchInput.value = activeFilters.query;
  renderModeChooser();

  function draw(pushState = false) {
    renderCategoryChips(items, activeFilters.category);
    const filtered = items.filter((item) => {
      const matchCategory = activeFilters.category === t('allCategory', 'All') || item.category === activeFilters.category;
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
          <h3>${escapeHtml(t('noMatchTitle', 'No items matched that search.'))}</h3>
          <p class="muted">${escapeHtml(t('noMatchDesc', 'Try another keyword or another category.'))}</p>
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
  const offerPrice = isGuessMode()
    ? normalizePrice(guessEntry.offerPrice ?? item.actualPrice)
    : normalizePrice(item.actualPrice);
  cart[item.id] = {
    qty: Math.min((cart[item.id]?.qty || 0) + quantity, item.quantity || 1),
    offerPrice,
    guess: isGuessMode() ? guessEntry.lastGuess : null,
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

  if (reveal) {
    reveal.classList.remove('hide');
    reveal.querySelector('[data-offer-price]').textContent = money(offerPrice, site.currency);
  }
  if (actionBlock) actionBlock.classList.remove('hide');
  if (hiddenHint) {
    hiddenHint.textContent = offerPrice > Number(item.actualPrice)
      ? t('unlockAboveTarget', 'Unlocked from an above-target guess.')
      : t('unlockAtSellerPrice', 'Unlocked at the seller price.');
  }
  if (status) {
    status.className = 'status-box good';
    status.textContent = t('guessSuccess', 'Yes — that guess works. The unlocked checkout price is shown below.');
  }
  if (remaining) remaining.textContent = t('added', 'Added');
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


  if (!isGuessMode()) {
    const plainBox = document.getElementById('plain-price-box');
    const plainPrice = document.querySelector('[data-plain-price]');
    if (plainBox) plainBox.classList.remove('hide');
    if (plainPrice) plainPrice.textContent = money(current.actualPrice || 0, site.currency);
    if (status) {
      status.className = 'status-box good';
      status.textContent = t('plainModeNotice', 'Plain version — actual price shown directly.');
    }
    if (hiddenHint) hiddenHint.classList.add('hide');
    const inputRow = document.querySelector('.guess-input-row');
    if (inputRow) inputRow.classList.add('hide');
    const actionBlock = document.getElementById('unlock-actions');
    if (actionBlock) actionBlock.classList.remove('hide');
    return attachPlainActions();
  }

  function attachPlainActions() {
    if (addButton) {
      addButton.addEventListener('click', () => {
        addToCart({ ...current, actualPrice: current.actualPrice }, 1);
        addButton.textContent = t('added', 'Added');
        addButton.disabled = true;
      });
    }
    if (buyButton) {
      buyButton.addEventListener('click', () => {
        addToCart({ ...current, actualPrice: current.actualPrice }, 1);
        window.location.href = appendMode(`${pageRoot}checkout/`);
      });
    }
  }

  function refreshState() {
    const entry = getGuessEntry(current.id);
    if (!itemReadyForGuessing(current)) {
      if (status) {
        status.className = 'status-box warn';
        status.textContent = t('pendingItemMessage', 'This item is not ready for offers yet.');
      }
      if (hiddenHint) hiddenHint.textContent = t('pendingItemHint', 'Seller has not enabled guessing for this item yet.');
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
    if (status) status.textContent = t('offersLeft', 'Offers left: {count}', { count: attemptsLeft });
    if (attemptsLeft === 0) {
      if (status) {
        status.className = 'status-box bad';
        status.textContent = t('lastTryMessage', 'That was the last try from this browser. If you still want it, email the seller directly.');
      }
      if (hiddenHint) hiddenHint.textContent = t('noGuessesLeft', 'No guesses left on this browser.');
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
        status.textContent = t('enterValidAmount', 'Enter a valid dollar amount first.');
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
          ? t('guessTooLow', 'Too low. Try again — {count} chance{suffix} left.', {
              count: attemptsLeft,
              suffix: attemptsLeft === 1 ? '' : 's',
            })
          : t('guessTooLowFinal', 'Too low, and that was the last chance on this browser.');
        if (hiddenHint) hiddenHint.textContent = t('generatedNegotiablePrice', '{price} (negotiable)', { price: money(getPublicNegotiablePrice(current), site.currency) });
        refreshState();
      }
    });
  }

  if (addButton) {
    addButton.addEventListener('click', () => {
      addToCart(current, 1);
      addButton.textContent = t('added', 'Added');
      addButton.disabled = true;
    });
  }

  if (buyButton) {
    buyButton.addEventListener('click', () => {
      addToCart(current, 1);
      window.location.href = appendMode(`${pageRoot}checkout/`);
    });
  }
}

function buildCheckoutEmail({ cartRows, total, site, form }) {
  const deliveryEligible = total >= Number(site.freeDeliveryThreshold || 0);
  const lines = [
    t('emailGreeting', 'Hi {name},', { name: site.ownerName || 'seller' }),
    '',
    t('emailIntro', 'I would like to buy these items from Congo:'),
    '',
    ...cartRows.map((row) => `- ${row.name} — ${money(row.offerPrice, site.currency)}${row.guess ? ` (${t('unlockedFromGuess', 'Unlocked from guess {guess}.', { guess: money(row.guess, site.currency) })})` : ''}`),
    '',
    t('emailTotal', 'Total: {total}', { total: money(total, site.currency) }),
    deliveryEligible
      ? t('emailDeliveryUnlocked', 'This order is above {threshold}, so it qualifies for free local delivery.', { threshold: money(site.freeDeliveryThreshold, site.currency) })
      : t('emailDeliveryNeedMore', 'This order is below {threshold}. Pickup is fine, or we can discuss delivery.', { threshold: money(site.freeDeliveryThreshold, site.currency) }),
    '',
    t('emailPreferredOption', 'Preferred option: {value}', { value: form.deliveryMode }),
    t('emailPreferredTime', 'Preferred time: {value}', { value: form.when || t('none', 'None') }),
    t('emailName', 'Name: {value}', { value: form.name || '' }),
    t('emailEmail', 'Email: {value}', { value: form.email || '' }),
    t('emailPhone', 'Phone: {value}', { value: form.phone || '' }),
    t('emailAddress', 'Address / meeting point: {value}', { value: form.address || '' }),
    '',
    t('emailNotes', 'Notes:'),
    form.notes || t('none', 'None'),
    '',
    t('thanks', 'Thanks!'),
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
        ? t('deliveryUnlocked', 'Free local delivery unlocked on this order.')
        : t('deliveryNeedMore', 'Add {amount} more to reach free local delivery.', { amount: money(Math.max(0, threshold - total), site.currency) });
    }
    if (progressFill) progressFill.style.width = `${progress}%`;

    if (!cartList) return { rows, total };
    if (!rows.length) {
      cartList.innerHTML = `
        <div class="empty-state">
          <h3>${escapeHtml(t('cartEmptyTitle', 'Your cart is empty.'))}</h3>
          <p class="muted">${escapeHtml(t('cartEmptyDesc', 'Unlock an item first, then add it to cart.'))}</p>
          <p><a class="btn-amazon" href="${pageRoot}">${escapeHtml(t('backToCatalog', 'Back to the catalog'))}</a></p>
        </div>
      `;
      return { rows, total };
    }

    cartList.innerHTML = rows
      .map((row) => `
        <article class="cart-item">
          <div class="cart-thumb">
            <img src="${withBase(getItemPrimaryImage(row))}" alt="${escapeHtml(row.name)}" onerror="this.src='${assetRoot}assets/placeholder.png'"/>
          </div>
          <div>
            <h3 style="margin:0 0 6px">${escapeHtml(row.name)}</h3>
            <div class="muted">${escapeHtml(row.category)} · ${escapeHtml(row.condition || 'Used')}</div>
            <div class="small-note" style="margin-top:8px">${row.guess ? escapeHtml(t('unlockedFromGuess', 'Unlocked from guess {guess}.', { guess: money(row.guess, site.currency) })) : escapeHtml(t('unlockedPriceReady', 'Unlocked price ready.'))}</div>
          </div>
          <div style="display:grid;gap:10px;justify-items:end">
            <div class="price-line">${money(row.offerPrice, site.currency)}</div>
            <button class="btn-ghost" data-remove-item="${escapeHtml(row.id)}">${escapeHtml(t('remove', 'Remove'))}</button>
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
      deliveryMode: fd.get('deliveryMode')?.toString().trim() || t('pickupOption', 'Pickup'),
      address: fd.get('address')?.toString().trim(),
      notes: fd.get('notes')?.toString().trim(),
    };
  }

  function writeEmailTargets() {
    state = draw();
    if (!form) return '';
    const formData = getFormData();
    const body = buildCheckoutEmail({ cartRows: state.rows, total: state.total, site, form: formData });
    const subject = t('mailSubject', 'Congo order request ({count} item{suffix})', {
      count: state.rows.length,
      suffix: state.rows.length === 1 ? '' : 's',
    });
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
        copyButton.textContent = t('copied', 'Copied');
        setTimeout(() => (copyButton.textContent = t('copyEmailText', 'Copy email text')), 1800);
      } catch {
        copyButton.textContent = t('copyFailed', 'Copy failed');
      }
    });
  }

  writeEmailTargets();
}

function boot() {
  hydrateCartCount();
  attachGlobalSearch();
  attachLanguageSwitch();
  fetchCatalog()
    .then((catalog) => {
      renderCategoryChips(catalog.items || [], new URLSearchParams(window.location.search).get('category') || t('allCategory', 'All'));
      if (pageType === 'index') renderIndex(catalog);
      if (pageType === 'item') renderItemPage(catalog);
      if (pageType === 'checkout') renderCheckout(catalog);
    })
    .catch((error) => {
      const host = document.getElementById('page-error');
      if (host) {
        host.classList.remove('hide');
        host.textContent = t('failedLoadCatalog', 'Failed to load the catalog: {message}', { message: error.message });
      }
    });
}

boot();
