# MMF Fusion website

Vape shop site for MMF Fusion, 231 Monument Road, Glen Marais, Kempton Park. Built from our vape-shop template, restyled in MMF's own navy, cyan and violet "fusion" theme.

Plain HTML/CSS/JS, no build step. Works on any static host (Vercel, GitHub Pages).

## Pages
| File | What it is |
|---|---|
| `index.html` | Home: fusion hero (canvas vapour streams, orbiting products, tap-to-fuse logo), brand ticker, order again, categories, just landed, vape finder quiz, Spin the Fusion, burn-rate calculator, coil finder banner, ways to get it, 7Waves, brands, community |
| `shop.html` | Full catalogue with filters (category, brand, flavour, puffs, price) |
| `product.html` | Product page (`?id=`): option picker, what fits / fits these devices, related, recently viewed |
| `fit.html` | Coil & Pod Finder (`?d=xros`) |
| `visit.html` | The shop: map, directions, contact form that opens WhatsApp |
| `about.html`, `help.html`, `guide.html` | About, delivery & returns FAQs, vaping guidance |

## Things still to fill in (ask the shop)
| What | Where |
|---|---|
| Trading hours | `SHOP.hrs` in `assets/site.js`, e.g. `wk("09:00-14:00", "08:00-18:00")`. Live open/closed on the Visit page then switches on by itself. Add `openingHoursSpecification` to the JSON-LD too. |
| Payment methods | Add a payment strip on the home page (see the comment there) and update the "How do I pay?" FAQ |
| 7Waves go-live | `CONFIG.partnerLive: true` in `assets/site.js`, then change the "Coming soon" copy on the home and help pages |
| Store photos | About page (the logo badge is a placeholder) |
| Real stock | When their WooCommerce shop has products: `python tools/snapshot.py`, then set `CONFIG.onlineStore` to `https://mmffusion.com` to turn on "Buy now" and "Pay online now" |

## Products
- Right now `assets/products.json` is **sample stock** from the CloudVapor template (hookah, smoking gear, pouches and cannabis lines removed). `python tools/snapshot.py --sample` rebuilds it.
- `python tools/snapshot.py` loads MMF's own in-stock WooCommerce products, with flavour/colour options and photos. It stops with a message while their shop is still empty.

## Brand
- `brand.json` holds the current details; `tools/rebrand.py` swaps them.
- Theme: `assets/mmf.css` (loaded after `assets/site.css`). Gradient `--fusion`, cyan `#3fd6f0`, violet `#9a8cff`, navy `#060912`. Buttons use dark ink on the gradient for contrast.
- Logo: `assets/img/logo.webp` / `logo-sm.webp` are the light version for the dark theme, made from the logo on mmffusion.com.

## Test locally
`python -m http.server 5190`, then open http://localhost:5190. Check every page at 375px for sideways scrolling and console errors.

## Publish
Every page has `<meta name="robots" content="noindex, nofollow">` so the demo stays out of Google. Remove it once the owner signs off. Bump `?v=N` on the CSS/JS links and `CACHE` in `sw.js` on every release.
