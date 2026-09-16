# ZERO DAY — Phase 2

## Architecture and Railway

The existing application is Flask/Jinja, not React. This expansion keeps its server routes, application factory, WSGI entry point, original CSS/typography and lazy Three.js renderer. It adds no Node build, React Router dependency, rewrite rules or database migration. Direct URLs and refreshes are handled by Flask, including real HTTP 404 responses. Keep the existing Railway start command and environment configuration. Nothing was deployed by this change.

The brief's React Router / Framer Motion language is implemented with the existing architecture: native navigation, optional short cross-document View Transitions, the established reveal motion, and reduced-motion fallbacks. Switching runtimes would have rebuilt approved work.

| URL | Purpose |
| --- | --- |
| `/` | Approved composition; CTAs now connect to interior routes; supplied video added |
| `/menu` | Confirmed café menu, category navigation and quick add |
| `/producto/<slug>` | Customization, quantity and selection editing |
| `/carrito` | Persistent selection, authoritative prices and subtotal |
| `/catalogo` | Existing ten-object editorial 3D exhibition; no commerce |
| `/espacio` | Spatial composition and slots for authentic photography |
| `/experiencia` | Existing café philosophy; confirmed service blocks when supplied |
| `/visitanos` | Verified practical information only |
| `/origenes`, `/metodos`, `/cafe/<slug>` | Existing educational routes retained |

Shared interior layout: `app/templates/layouts/interior.html`. New room-specific styles: `app/static/css/interior.css`. The homepage's typography, grid and section order remain intact. Its demonstration menu and social link are no longer rendered as public information under Phase 2's content rules.

## Add real menu content

`app/cafe_content.py` remains the single content source. Phase 1 menu examples are retained for editing but not published. The old database's seeded coffee bags and their demonstration prices are **not** café menu inventory.

1. Replace `CAFE['menu']` with confirmed categories and records.
2. Set `menu_is_example=False`.
3. Set `currency` to the actual three-letter currency code. It is currently unset.
4. Each item needs a stable `id`, URL-safe lowercase `slug`, `name`, and `published=True` to appear.
5. Ordering additionally requires `availability='available'` and a valid decimal `price`. Missing price/currency never becomes a free item. Unavailable published items retain their detail pages.
6. Restart/redeploy the application using the existing Railway workflow.

Schema template (deliberately unpublished, no invented price):

```python
{
    'name': '<confirmed category>',
    'items': [{
        'id': '<stable-id>',
        'slug': '<lowercase-url-slug>',
        'name': '<confirmed name>',
        'published': False,
        'availability': 'unavailable',
        'short_description': '',
        'long_description': '',
        'price': None,  # decimal string with at most two decimal places
        'image': None,  # /static/... or HTTPS URL, authentic product photography
        'gallery': [],  # [{image: '/static/...', alt: '...', caption: '...'}]
        'featured': False,
        'options': [],
        'modifiers': [],
    }],
}
```

`description` is also accepted as the existing short-description field. Category comes from the parent group. Quantity belongs to the customer's cart, not the product record.

Options use one radio choice per group. Modifiers allow several checkboxes. Group structure:

```python
{
    'id': '<stable-group-id>',
    'label': '<confirmed label>',
    'required': False,
    'max_choices': 1,
    'choices': [{
        'id': '<stable-choice-id>',
        'label': '<confirmed choice>',
        'price_delta': '0.00',  # explicitly included option; replace for a real surcharge
        'available': True,
    }],
}
```

All fixture products, prices and modifiers used for automated checks live in `tests/menu_fixtures.py`. The application never imports them.

## Commerce foundation

- `MenuService` normalizes confirmed content and prices. Every calculation uses integer cents derived from decimal strings.
- `GET /api/menu` returns the published menu. `POST /api/order/quote` requires CSRF and accepts only product IDs, quantity, option IDs and modifier IDs. Client-supplied names/prices/totals do not determine a quote.
- Quotes validate availability, selected choices, required choices, modifier limits and quantities from 1 to 99. Missing/stale products remain visible as unavailable cart lines and do not enter the subtotal.
- The cart permits 50 distinct configurations. Identical combinations merge; editing a line can replace or merge it. A rejected update does not overwrite the previous cart.
- The client stores versioned selection data under `zero-day:cafe-selection:v1`, with no authoritative prices. It re-quotes on navigation, quantity changes, reconnection and cross-tab updates.
- Corrupt/blocked storage and network failures have readable recovery states. Options can be edited by returning to the product page from the cart.
- No delivery charge, tax, payment method or ordering channel was invented. Checkout is explicitly unavailable. This is a saved-selection foundation, not a submitted order.
- A future checkout must revalidate the selection on the server, create a real order and integrate a verified payment/order provider. Do not treat a quote or localStorage as an order.
- The old cart API/service remains for legacy compatibility; new pages do not call it.

## Media, visit data and services

The supplied `app/static/img/products/hero.mp4` is used unchanged. `hero-poster.webp` is a frame extracted from that video; composition and text positions remain the homepage's. Video is muted, looped and inline, starts when visible, pauses when hidden, and has a manual pause button. Reduced motion, data-saving and slow connections use the poster unless the visitor explicitly plays it. A media error keeps the poster.

Set `space_image`, `space_alt` and `space_gallery` only with authentic café media. These paths are relative to `app/static`. A gallery entry has `image`, `alt` and optional `caption`. The current ceramic composition is editorial, not presented as a photograph of the premises.

`experiences` accepts existing `{title, description, image, alt}` records for confirmed services; no events, delivery, coworking or policies were added. `policies` optionally accepts confirmed `{title, description}` records for the visit page.

The supplied address and 8 a.m.–8 p.m. hours are retained. Days, city, coordinates, contact accounts and policies remain unset. Set `maps_url` to the verified map location; the directions link only renders once supplied. A generic Instagram URL is not treated as a verified social account.

## Verification

Run:

```sh
.venv/bin/python -m pytest -q
npm test
```

Python integration coverage includes direct routes/404s, unpublished content, incomplete pricing, modifiers, stale cart lines, current prices and CSRF. JavaScript tests cover persistence, merging/editing, invalid quantities, corrupt/blocked storage and the existing visual modules.

The local Chromium audit uses an ephemeral testing server and injects artificial menu records only into that process. It checks the complete menu → product → cart flow, refresh, editing, offline recovery, empty/unavailable states, six viewport widths, video, reduced motion, no-JavaScript content and the catalog's WebGL fallback. Screenshots are under `/tmp/zero-day-phase2/` during this working session.

Latest result: 76 Python tests and 27 JavaScript tests pass. Chromium checks pass at 375, 430, 768, 1024, 1440 and 1920 px, with no horizontal overflow or JavaScript errors. The menu/product/cart flow and offline recovery pass at 375 and 1440 px.
