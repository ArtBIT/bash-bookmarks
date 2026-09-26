(function () {
  const $ = (selector) => document.querySelector(selector);
  const searchInput = $('#search');
  const searchClear = $('#search-clear');
  const results = $('#results');
  const status = $('#status');
  const empty = $('#empty');
  const dialog = $('#add-dialog');
  const form = $('#add-form');
  const addError = $('#add-error');
  const saveButton = $('#add-save');
  const toast = $('#toast');
  const categories = new Set(['unsorted']);
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  let searchTimer = null;
  let searchRequest = 0;

  function storageGet(key, fallback) {
    try {
      return localStorage.getItem(key) || fallback;
    } catch (e) {
      return fallback;
    }
  }

  function storageSet(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (e) {}
  }

  function showToast(message) {
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(showToast.timer);
    showToast.timer = setTimeout(() => toast.classList.remove('show'), 3000);
  }

  // Runs done() after the element's CSS animation ends (or right away when motion is reduced)
  function afterAnimation(node, done) {
    if (reducedMotion.matches) return done();
    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      done();
    };
    node.addEventListener('animationend', finish, { once: true });
    setTimeout(finish, 400);
  }

  async function api(path, options) {
    const response = await fetch(path, options);
    let data = null;
    try {
      data = await response.json();
    } catch (e) {}
    if (!response.ok || (data && data.error)) {
      const message = data && (data.message || data.error);
      throw new Error(Array.isArray(message) ? message.join(' ') : message || 'Request failed (' + response.status + ')');
    }
    return data;
  }

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([key, value]) => {
      if (key === 'text') node.textContent = value;
      else if (key === 'html') node.innerHTML = value;
      else node.setAttribute(key, value);
    });
    (children || []).forEach((child) => child && node.appendChild(child));
    return node;
  }

  function toTags(tags) {
    if (Array.isArray(tags)) return tags.map(String).filter(Boolean);
    if (!tags) return [];
    return String(tags).replace(/^\[|\]$/g, '').split(',').map((t) => t.trim().replace(/^["']|["']$/g, '')).filter(Boolean);
  }

  function isWebUrl(url) {
    return /^https?:\/\//i.test(url);
  }

  function hostname(url) {
    try {
      return new URL(url).hostname.replace(/^www\./, '');
    } catch (e) {
      return '';
    }
  }

  function displayUrl(url) {
    try {
      const parsed = new URL(url);
      return parsed.hostname.replace(/^www\./, '') + (parsed.pathname + parsed.search).replace(/\/$/, '');
    } catch (e) {
      return url;
    }
  }

  function hue(text) {
    let hash = 0;
    for (const char of text) hash = (hash * 31 + char.charCodeAt(0)) % 360;
    return hash;
  }

  const FOLDER_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /></svg>';
  const REMOVE_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3" /></svg>';

  function avatar(url) {
    const host = hostname(url);
    if (!isWebUrl(url)) return el('span', { class: 'avatar', html: FOLDER_ICON, style: '--hue: 250' });
    return el('span', { class: 'avatar', text: (host[0] || '?'), style: '--hue: ' + hue(host), 'aria-hidden': 'true' });
  }

  function showEmpty(title, text) {
    $('#empty-title').textContent = title;
    $('#empty-text').textContent = text;
    empty.hidden = false;
  }

  function renderResults(items) {
    empty.hidden = true;
    results.classList.remove('loading');
    results.replaceChildren();
    items.forEach((item, index) => {
      const url = item.url || '';
      const category = item.category || item.project;
      if (category) categories.add(category);

      const title = isWebUrl(url)
        ? el('a', { class: 'title', href: url, target: '_blank', rel: 'noopener noreferrer', text: item.title || url })
        : el('span', { class: 'title', text: item.title || url });

      const meta = el('div', { class: 'meta' }, [
        category ? el('span', { class: 'chip category', text: category }) : null,
        ...toTags(item.tags).map((tag) => el('span', { class: 'chip', text: '#' + tag })),
      ]);

      const remove = el('button', { class: 'icon-button remove', type: 'button', title: 'Remove bookmark', 'aria-label': 'Remove bookmark', html: REMOVE_ICON });
      const row = el('li', { class: 'result', style: '--i: ' + Math.min(index, 10) }, [
        avatar(url),
        el('div', { class: 'body' }, [title, el('span', { class: 'url', text: isWebUrl(url) ? displayUrl(url) : url }), meta.childElementCount ? meta : null]),
        item.id ? remove : null,
      ]);
      remove.addEventListener('click', () => removeBookmark(item, row, remove));
      results.appendChild(row);
    });
    updateCategoryList();
  }

  function renderSkeleton() {
    results.replaceChildren(...[0, 1, 2].map(() => el('li', { class: 'result skeleton', 'aria-hidden': 'true' }, [
      el('span', { class: 'avatar' }),
      el('div', { class: 'body' }, [el('span', { class: 'line long' }), el('span', { class: 'line short' })]),
    ])));
  }

  function updateCategoryList() {
    const list = $('#categories');
    list.replaceChildren(...[...categories].sort().map((c) => el('option', { value: c })));
  }

  async function search() {
    const query = searchInput.value.trim();
    const request = ++searchRequest;
    searchClear.hidden = !searchInput.value;
    if (!query) {
      results.replaceChildren();
      status.textContent = '';
      showEmpty('Search your bookmarks', 'Type to search by title, URL, category or tag. Share links from any app to save them here.');
      return;
    }

    // The bookmarks server ignores queries shorter than 3 characters
    if (query.length < 3) {
      results.replaceChildren();
      status.textContent = '';
      showEmpty('Keep typing', 'Type at least 3 characters to search.');
      return;
    }

    empty.hidden = true;
    status.textContent = 'Searching…';
    if (results.querySelector('.result:not(.skeleton)')) results.classList.add('loading');
    else renderSkeleton();

    try {
      const data = await api('/api/search?q=' + encodeURIComponent(query));
      if (request !== searchRequest) return;
      const items = Array.isArray(data) ? data : [];
      renderResults(items);
      if (items.length) {
        status.textContent = items.length + (items.length === 1 ? ' result' : ' results');
      } else {
        status.textContent = '';
        showEmpty('No bookmarks found', 'Nothing matches “' + query + '”. Try a different word or tag.');
      }
    } catch (e) {
      if (request !== searchRequest) return;
      results.classList.remove('loading');
      results.replaceChildren();
      status.textContent = '';
      showEmpty('Could not search', e.message);
    }
  }

  async function removeBookmark(item, row, button) {
    if (!confirm('Remove “' + (item.title || item.url) + '”?')) return;
    button.disabled = true;
    try {
      await api('/api/remove', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: item.id }),
      });
      showToast('Bookmark removed');
      row.classList.add('removing');
      afterAnimation(row, () => {
        row.remove();
        const count = results.querySelectorAll('.result').length;
        status.textContent = count ? count + (count === 1 ? ' result' : ' results') : '';
        if (!count) showEmpty('No bookmarks found', 'Nothing left for this search.');
      });
    } catch (e) {
      button.disabled = false;
      showToast(e.message);
    }
  }

  function openAddDialog(values) {
    form.reset();
    addError.textContent = '';
    dialog.classList.remove('closing');
    const fields = Object.assign({ category: storageGet('bookmarks.category', 'unsorted') }, values);
    Object.entries(fields).forEach(([name, value]) => {
      if (form.elements[name] && value) form.elements[name].value = value;
    });
    dialog.showModal();
    (form.elements.url.value ? form.elements.title : form.elements.url).focus();
  }

  function closeAddDialog() {
    if (!dialog.open || dialog.classList.contains('closing')) return;
    dialog.classList.add('closing');
    afterAnimation(dialog, () => {
      dialog.classList.remove('closing');
      dialog.close();
    });
  }

  // Android apps often share the link inside the text field, e.g. "Some title https://..."
  function fromShare(params) {
    const text = params.get('text') || '';
    let url = params.get('url') || '';
    let title = params.get('title') || '';
    const match = text.match(/https?:\/\/\S+/);
    if (!url && match) url = match[0];
    if (!title) title = text.replace(url, '').trim();
    return { url, title };
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    data.category = data.category.trim() || 'unsorted';
    saveButton.disabled = true;
    saveButton.classList.add('busy');
    addError.textContent = '';
    try {
      await api('/api/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      storageSet('bookmarks.category', data.category);
      categories.add(data.category);
      closeAddDialog();
      showToast('Bookmark saved');
      if (searchInput.value.trim()) search();
    } catch (e) {
      addError.textContent = e.message;
    } finally {
      saveButton.disabled = false;
      saveButton.classList.remove('busy');
    }
  });

  // Animate Escape and backdrop taps the same way as Cancel
  dialog.addEventListener('cancel', (event) => {
    event.preventDefault();
    closeAddDialog();
  });
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) closeAddDialog();
  });

  $('#add-cancel').addEventListener('click', closeAddDialog);
  $('#add-button').addEventListener('click', () => openAddDialog({}));

  searchInput.addEventListener('input', () => {
    searchClear.hidden = !searchInput.value;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(search, 250);
  });

  searchClear.addEventListener('click', () => {
    searchInput.value = '';
    searchInput.focus();
    search();
  });

  searchInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      const first = results.querySelector('a.title');
      if (first) window.open(first.href, '_blank', 'noopener');
    } else if (event.key === 'Escape' && searchInput.value) {
      searchClear.click();
    }
  });

  // Launched from the Android share sheet (PWA share_target)
  if (location.pathname === '/share') {
    const shared = fromShare(new URLSearchParams(location.search));
    history.replaceState(null, '', '/');
    openAddDialog(shared);
  }

  search();

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js').catch(() => {});
  }
})();
