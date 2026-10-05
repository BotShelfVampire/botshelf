# Fix: EN nav "Search / 検索" → i18n navSearch (2026-10-05)

Owner: remove 検索 from EN mobile menu.

## Change
- HTML: `<a href="/search/" …>Search / 検索</a>` → `data-i18n="navSearch"` with default text `Search` (keep `class="nav-search"` when present).
- i18n COMMON key `navSearch`: en Search / ja 検索 / es Buscar / zh 搜索 / ko 검색.
- Applied on live tree `bsv-live/stage88/site` (919 HTML) + all `js/i18n*.js`; not produced by a current repo generator (baked site HTML).

## Re-apply
`python3 ops/token-efficiency/fix_nav_search_i18n.py /path/to/site`
