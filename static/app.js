(function () {
  const $ = (selector) => document.querySelector(selector);
  const searchInput = $('#search');
  const results = $('#results');
  const status = $('#status');
  const dialog = $('#add-dialog');
  const form = $('#add-form');
  const addError = $('#add-error');
  const saveButton = $('#add-save');
  const toast = $('#toast');
  const categories = new Set(['unsorted']);

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
    toast.hidden = false;
    clearTimeout(showToast.timer);
    showToast.timer = setTimeout(() => (toast.hidden = true), 3000);
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

  function renderResults(items) {
    results.replaceChildren();
    items.forEach((item) => {
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

      const remove = el('button', { class: 'remove', type: 'button', title: 'Remove bookmark', 'aria-label': 'Remove bookmark', text: '×' });
      remove.addEventListener('click', () => removeBookmark(item, remove));

      results.appendChild(el('li', { class: 'result' }, [
        el('div', { class: 'body' }, [title, el('span', { class: 'url', text: url }), meta.childElementCount ? meta : null]),
        item.id ? remove : null,
      ]));
    });
    updateCategoryList();
  }

  function updateCategoryList() {
    const list = $('#categories');
    list.replaceChildren(...[...categories].sort().map((c) => el('option', { value: c })));
  }

  async function search() {
    const query = searchInput.value.trim();
    const request = ++searchRequest;
    if (!query) {
      results.replaceChildren();
      status.textContent = 'Type to search your bookmarks.';
      return;
    }

    status.textContent = 'Searching…';
    try {
      const data = await api('/api/search?q=' + encodeURIComponent(query));
      if (request !== searchRequest) return;
      const items = Array.isArray(data) ? data : [];
      renderResults(items);
      status.textContent = items.length ? items.length + (items.length === 1 ? ' result' : ' results') : 'No bookmarks found.';
    } catch (e) {
      if (request !== searchRequest) return;
      results.replaceChildren();
      status.textContent = e.message;
    }
  }

  async function removeBookmark(item, button) {
    if (!confirm('Remove "' + (item.title || item.url) + '"?')) return;
    button.disabled = true;
    try {
      await api('/api/remove', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: item.id }),
      });
      showToast('Bookmark removed');
      search();
    } catch (e) {
      button.disabled = false;
      showToast(e.message);
    }
  }

  function openAddDialog(values) {
    form.reset();
    addError.textContent = '';
    const fields = Object.assign({ category: storageGet('bookmarks.category', 'unsorted') }, values);
    Object.entries(fields).forEach(([name, value]) => {
      if (form.elements[name] && value) form.elements[name].value = value;
    });
    dialog.showModal();
    (form.elements.url.value ? form.elements.title : form.elements.url).focus();
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
    addError.textContent = '';
    try {
      await api('/api/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      storageSet('bookmarks.category', data.category);
      categories.add(data.category);
      dialog.close();
      showToast('Bookmark saved');
      if (searchInput.value.trim()) search();
    } catch (e) {
      addError.textContent = e.message;
    } finally {
      saveButton.disabled = false;
    }
  });

  $('#add-cancel').addEventListener('click', () => dialog.close());
  $('#add-button').addEventListener('click', () => openAddDialog({}));

  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(search, 250);
  });

  searchInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      const first = results.querySelector('a.title');
      if (first) window.open(first.href, '_blank', 'noopener');
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
