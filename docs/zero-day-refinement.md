> Phase 2 supersedes the menu/routing instructions below. See [zero-day-phase2.md](zero-day-phase2.md).

# ZERO DAY — editable café website

The application is Flask/Jinja with local Three.js, not React/Vite. The redesign keeps this stack, the Playfair Display / Plus Jakarta Sans typography, original assets and existing routes. Native scroll and intersection animations replace the former 270svh pinned sales story. No additional frontend runtime is required.

## Change the content

Edit `app/cafe_content.py` and restart Flask:

- Address and hours were supplied by the owner. Days of operation and city were not supplied.
- `menu` is the starter menu requested by the owner. It contains no prices. Set `menu_is_example=False` after confirming it.
- `instagram_url` currently points to Instagram's general homepage, not to an invented café account. Replace it and set `social_is_example=False`.
- Set `maps_url` to the café's verified location. It is omitted until then because the city is unknown.
- `space_image` / `space_alt`: add a photo of the actual café, using a path relative to `app/static`. The present composition is an editorial ceramic object, not a photograph of the premises.
- `hero_poster` / `hero_video`: optional real media. Video loads only on deliberate playback and includes a pause control.
- `experiences`: optional confirmed services. Empty by default; the page instead links to the existing preparation guide and space section.
- `/catalogo` now displays the full café menu. Existing origin detail and preparation routes remain educational, without shopping controls.

Menu category references (not copied descriptions or pricing):
- https://www.starbucks.com/menu/coffee-espresso/hot-coffee-espresso
- https://www.starbucks.com/menu?preview=true

## Asset audit and delivery

All 21 GLBs were inspected: ten supplied third-party originals, ten existing derived models and one generated ZERO DAY bag. There were no GLTF files, video files, local fonts or authentic café interior photographs. The generated bag is retained on disk but is not displayed. Original source files remain untouched.

The ten source models appear in the exhibition through their optimized derivatives. Legacy filenames such as `yirgacheffe` identify files only; the visible label is **Costa Coffee**, not a fictitious ZERO DAY product. The renderer no longer creates or applies ZERO DAY labels. Original brand textures are restored. The legacy specular-glossiness material in the scanned paper bag is converted for compatibility. Existing geometry simplification is retained for non-branded objects; the restored paper bag and Dunkin model are simplified with meshoptimizer without replacing materials.

One shared WebGL canvas renders only the most visible object. The exhibition has no automatic advancement. Pagination and previous/next buttons support keyboard operation; arrow keys and Home/End also work. Models load on intersection, rotate subtly with native scrolling, and render only on demand. Reduced motion, data-saving and failed WebGL retain faithful rendered images. Without JavaScript, all objects are readable in sequence.

`prepare_models.py` extracts textures from originals and performs material compatibility conversion; it does not rebrand. Its output is unsimplified geometry. `render_model_posters.py` generates corresponding static WebP images using a local server on port 5071, Playwright Chromium and ImageMagick. Do not run preparation without re-applying geometry optimization before publishing large originals.

Author attribution and licenses remain at `/static/models/credits.html`.

## Validation

45 Python tests and 21 JavaScript tests pass. Chromium review at 375, 430, 768, 1024, 1440 and 1920 px found no horizontal overflow or JavaScript errors. All ten exhibition models reach the rendered state, with one shared canvas. Mobile navigation, keyboard selection, reduced motion, no-JavaScript content and all five public routes were checked. Review screenshots and results: `/tmp/zero-day-refinement/`.
