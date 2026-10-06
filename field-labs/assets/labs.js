/* BSV Field Labs: local interaction only, no network or paid services. */
(() => {
  'use strict';
  const query = new URLSearchParams(location.search);
  let language = query.get('lang') === 'ja' ? 'ja' : 'en';
  if (!query.has('lang')) {
    try { language = localStorage.getItem('bsv-labs-lang') === 'ja' ? 'ja' : 'en'; } catch (_) {}
  }
  window.BSVLabs = { lang: () => language, text: (en, ja) => language === 'ja' ? ja : en };
  function setLanguage(value) {
    language = value === 'ja' ? 'ja' : 'en';
    document.documentElement.lang = language;
    document.querySelectorAll('[data-lang]').forEach(el => { el.hidden = el.dataset.lang !== language; });
    document.querySelectorAll('[data-set-lang]').forEach(el => { el.setAttribute('aria-pressed', String(el.dataset.setLang === language)); });
    document.querySelectorAll('a[data-lab-link]').forEach(el => { const url = new URL(el.href); url.searchParams.set('lang', language); el.href = url.href; });
    try { localStorage.setItem('bsv-labs-lang', language); } catch (_) {}
    const url = new URL(location.href); url.searchParams.set('lang', language);
    history.replaceState(null, '', url);
    document.dispatchEvent(new CustomEvent('bsv:language', {detail:{lang:language}}));
  }
  document.querySelectorAll('[data-set-lang]').forEach(el => el.addEventListener('click', () => setLanguage(el.dataset.setLang)));
  setLanguage(language);
})();
