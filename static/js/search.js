// Dynamic search for Products, Shops, and Shop Products
(function(){
  const input = document.querySelector('.nav-search');
  if (!input) return;

  const path = window.location.pathname;
  const params = new URLSearchParams(window.location.search);

  const productsGrid = document.getElementById('products-grid');
  const shopsList = document.getElementById('shops-list');
  const shopProductsGrid = document.getElementById('shop-products-grid');

  // Extract shop id from path if on /viewShop/<id>
  let shopId = null;
  const m = path.match(/^\/viewShop\/(\d+)/);
  if (m) shopId = m[1];

  // Debounce to avoid spamming the server
  let timer = null;
  const debounce = (fn, delay=200) => {
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(null, args), delay);
    };
  };

  // Render helpers
  function renderProducts(items) {
    if (!productsGrid) return;
    if (!Array.isArray(items)) items = [];
    if (items.length === 0) {
      productsGrid.innerHTML = '<p style="grid-column: 1 / -1; color: #333;">No products found.</p>';
      return;
    }
    productsGrid.innerHTML = items.map(it => `
      <a href="${it.url}" style="text-decoration: none; color: inherit;">
        <div class="product">
          <img src="${it.image || ''}" alt="${escapeHtml(it.name)}">
          <div class="product-content">
            <div class="product-title-row">
              <p>${escapeHtml(it.name)}</p>
              <p>₱${fmtPrice(it.price)}/${escapeHtml(it.unit || 'kg')}</p>
            </div>
            <p class="product-seller">${escapeHtml(it.shop_name || '')}</p>
            <div class="shop-rating">
              <p style="color:#FFD700; margin:0;">${renderStars(it.rating)}</p>
              <p style="margin-left: 8px;">${Number(it.rating || 0).toFixed(1)}</p>
            </div>
          </div>
        </div>
      </a>
    `).join('');
  }

  function renderShops(items) {
    if (!shopsList) return;
    if (!Array.isArray(items)) items = [];
    if (items.length === 0) {
      shopsList.innerHTML = '<p style="grid-column: 1 / -1; color: #333;">No shops found.</p>';
      return;
    }
    shopsList.innerHTML = items.map(s => `
      <div class="shop-card">
        <img src="${s.image || ''}" alt="${escapeHtml(s.shop_name)}" style="width: 80px; height: 80px; border-radius: 50%; margin-right: 25px; border: 2px solid #E2F0D9; object-fit: cover;">
        <div class="shop-info">
          <h2 style="margin-bottom: 8px; color: #333;">${escapeHtml(s.shop_name)}</h2>
          <p style="margin-bottom: 10px; color: #666;">${escapeHtml(s.description || '')}</p>
          <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="color: #FFD700; font-size: 1.2em;">${renderStars(s.avg_rating)}</span>
            <span style="margin-left: 8px; color: #333;">${Number(s.avg_rating || 0).toFixed(1)}</span>
          </div>
          <a href="${s.url}" class="btn btn-primary shop-btn" style="background: #FF5722; color: #fff; padding: 7px 18px; border-radius: 8px; text-decoration: none; font-weight: bold;">View Shop</a>
        </div>
      </div>
    `).join('');
  }

  function renderShopProducts(items) {
    if (!shopProductsGrid) return;
    if (!Array.isArray(items)) items = [];
    if (items.length === 0) {
      shopProductsGrid.innerHTML = '<p style="grid-column: 1 / -1; color: #333;">No products found.</p>';
      return;
    }
    shopProductsGrid.innerHTML = items.map(it => `
      <a class="product-link" href="${it.url}">
        <div class="product-card" style="background: #fff; border-radius: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.07); padding: 12px; display: flex; flex-direction: column; align-items: center; border: 1px solid #e2e2e2;">
          <img src="${it.image || ''}" alt="${escapeHtml(it.name)}" style="width: 110px; height: 110px; object-fit: cover; border-radius: 10px; border: 1px solid #eee; margin-bottom: 10px;">
          <div style="width: 100%;">
            <div style="font-size: 1em; font-weight: 600; color: #333; margin-bottom: 2px;">${escapeHtml(it.name)}</div>
            <div style="font-size: 0.95em; color: #e74c3c; font-weight: bold;">₱${fmtPrice(it.price)}</div>
            <div style="font-size: 0.9em; color: #888; margin-bottom: 2px;">Available: ${Number(it.available || 0)} &nbsp;|&nbsp; Sold: ${Number(it.sold || 0)}</div>
            <div style="font-size: 0.9em; color: #FFD700; font-weight: bold;">★ ${Number(it.rating || 0).toFixed(1)}</div>
          </div>
        </div>
      </a>
    `).join('');
  }

  // Utility functions
  function renderStars(rating) {
    const r = Math.floor(Number(rating || 0));
    let stars = '';
    for (let i = 1; i <= 5; i++) stars += i <= r ? '&#9733;' : '&#9734;';
    return stars;
  }
  function fmtPrice(v){
    const n = Number(v || 0);
    return n.toLocaleString('en-PH', { maximumFractionDigits: 0 });
  }
  function escapeHtml(str){
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Decide which endpoint and renderer to use
  const isAllProducts = path === '/allProducts';
  const isShops = path.startsWith('/shops');
  const isViewShop = /^\/viewShop\//.test(path);

  function doSearch(q){
    const query = q == null ? '' : String(q);

    if (isAllProducts && productsGrid){
      const type = params.get('type') || '';
      const url = `/api/search/products?q=${encodeURIComponent(query)}${type ? `&type=${encodeURIComponent(type)}` : ''}`;
      fetch(url).then(r=>r.json()).then(data=>renderProducts(data.results || [])).catch(()=>{});
      return;
    }
    if (isShops && shopsList){
      const url = `/api/search/shops?q=${encodeURIComponent(query)}`;
      fetch(url).then(r=>r.json()).then(data=>renderShops(data.results || [])).catch(()=>{});
      return;
    }
    if (isViewShop && shopProductsGrid && shopId){
      const type = params.get('type') || '';
      const url = `/api/search/shop/${shopId}/products?q=${encodeURIComponent(query)}${type ? `&type=${encodeURIComponent(type)}` : ''}`;
      fetch(url).then(r=>r.json()).then(data=>renderShopProducts(data.results || [])).catch(()=>{});
      return;
    }
  }

  const debouncedSearch = debounce(doSearch, 250);

  input.addEventListener('input', (e)=>{
    debouncedSearch(e.target.value || '');
  });

  // If input starts with text (e.g., back-forward cache), trigger once
  if (input.value && input.value.trim().length){
    doSearch(input.value.trim());
  }
})();
