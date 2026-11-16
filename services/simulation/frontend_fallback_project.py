"""Starter project and evidence for the built-in Frontend fallback assignment."""

FRONTEND_README = """# Product Page

## Overview

This is the product detail page for the Everyday Headphones listing on the storefront.
Shoppers choose a colour, set a quantity, and press Buy Now to open the checkout panel,
which summarises the order before payment. The page is plain HTML, CSS, and JavaScript
with no framework or bundler; scripts are loaded with `defer` in a fixed order.

## Project structure

- `index.html` - page markup: colour options, quantity field, Buy Now button, and the
  checkout panel (`#checkout-panel`, `#checkout-summary`, `#checkout-total`, `#close-checkout`).
- `styles.css` - layout, focus styles, and the mobile breakpoint at 480px.
- `product-data.js` - the product catalogue for this page (`window.PRODUCT_DATA`): price and stock per colour.
- `cart.js` - pure pricing helpers (`lineTotal`, `formatPrice`) shared by the page and the tests.
- `checkout.js` - renders the order summary and opens or closes the checkout panel.
- `product.js` - wires the page together: colour changes, stock status, and Buy Now.
- `tests/cart.test.js` - existing unit tests for the pricing helpers (Node's built-in test runner).
- `package.json` - project metadata and the test script used in CI.

## Expected behaviour

- Changing colour updates the price and stock line, for example `$149.00 · 3 in stock`.
  A colour with no stock shows `Out of stock` and Buy Now is disabled.
- Quantity must be a whole number from 1 up to the stock of the selected colour. Invalid
  values show a message in `#quantity-error` and do not open checkout.
- Buy Now works with a mouse and with the keyboard (Enter and Space) and opens the panel
  with a summary of the current selection only:

```text
Everyday Headphones (sand) × 2
Total: $298.00
```

- When the panel opens, keyboard focus moves into it; Close hides it and returns focus to Buy Now.
- On screens up to 480px wide the Buy Now button spans the full width.

## Sample data and resources

`product-data.js` defines three colours: `black` ($149, 12 in stock), `sand` ($149, 3 in
stock), and `midnight` ($159, out of stock). The task email attaches
`browser-console.log` (errors captured by QA), `qa-regression-notes.md` (reproduction
steps on desktop and mobile), and `checkout-acceptance.md` (the agreed checkout behaviour).

## Verification

CareerGrid's terminal and browser preview cannot execute JavaScript or run the test
suite. In the workspace, verify by tracing each interaction through the scripts and
comparing results with the examples above and `product-data.js`. Add unit tests for any
helper you create in `tests/cart.test.js`. In CI or a local Node 18+ environment the tests
run with:

```bash
npm test
```

Report what you checked by reading code separately from tests you wrote; do not claim the
suite was executed.

## Deliverables and handover

- Code changes that restore checkout and meet the agreed checkout behaviour.
- Unit tests for any new quantity or pricing logic.
- Your changes committed and pushed, via a pull request or directly on main.
- A final team update with your diagnosis, what you changed, how you verified it, and any release risk.
"""

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Everyday Headphones</title>
  <link rel="stylesheet" href="styles.css">
  <script src="product-data.js" defer></script>
  <script src="cart.js" defer></script>
  <script src="checkout.js" defer></script>
  <script src="product.js" defer></script>
</head>
<body>
  <main>
    <article class="product">
      <h1>Everyday Headphones</h1>
      <p class="price-line"><span id="price">$149.00</span> · <span id="stock-status">In stock</span></p>
      <fieldset class="colors">
        <legend>Colour</legend>
        <label><input type="radio" name="color" value="black" checked> Black</label>
        <label><input type="radio" name="color" value="sand"> Sand</label>
        <label><input type="radio" name="color" value="midnight"> Midnight</label>
      </fieldset>
      <label for="quantity">Quantity</label>
      <input id="quantity" type="number" min="1" value="1" inputmode="numeric">
      <p id="quantity-error" class="field-error" role="alert" hidden></p>
      <button id="buy-now-btn" class="buy-now" type="button">Buy Now</button>
      <section id="checkout-panel" class="checkout" tabindex="-1" aria-labelledby="checkout-title" hidden>
        <h2 id="checkout-title">Checkout</h2>
        <ul id="checkout-summary"></ul>
        <p id="checkout-total"></p>
        <button id="close-checkout" type="button">Close</button>
      </section>
    </article>
  </main>
</body>
</html>
"""

STYLES_CSS = """body { margin: 0; font: 16px system-ui, sans-serif; background: #071126; color: #fff; }
.product { width: min(680px, calc(100% - 32px)); margin: 48px auto; }
.colors { border: 1px solid #334155; border-radius: 8px; margin: 16px 0; }
.field-error { color: #fca5a5; }
.buy-now { min-height: 44px; padding: 10px 18px; margin-top: 12px; }
.buy-now:disabled { opacity: .5; cursor: not-allowed; }
button:focus-visible, input:focus-visible, .checkout:focus-visible { outline: 3px solid #69c9ff; outline-offset: 3px; }
.checkout { margin-top: 20px; padding: 16px; border: 1px solid #334155; border-radius: 8px; }
@media (max-width: 480px) { .product { margin-top: 20px; } .buy-now { width: 100%; } }
"""

PRODUCT_DATA_JS = """window.PRODUCT_DATA = {
  name: 'Everyday Headphones',
  defaultColor: 'black',
  variants: {
    black: { price: 149, stock: 12 },
    sand: { price: 149, stock: 3 },
    midnight: { price: 159, stock: 0 },
  },
};
"""

CART_JS = """function lineTotal(unitPrice, quantity) {
  return Math.round(unitPrice * quantity * 100) / 100;
}

function formatPrice(amount) {
  return `$${amount.toFixed(2)}`;
}

if (typeof module !== 'undefined') {
  module.exports = { formatPrice, lineTotal };
}
"""

CHECKOUT_JS = """function renderCheckout(order) {
  const summary = document.querySelector('#checkout-summary');
  const total = document.querySelector('#checkout-total');
  summary.insertAdjacentHTML('beforeend', `<li>${order.name} (${order.color}) × ${order.quantity}</li>`);
  total.textContent = `Total: ${formatPrice(lineTotal(order.unitPrice, order.quantity))}`;
}

function openCheckout(panel) {
  panel.hidden = false;
}

function closeCheckout(panel) {
  panel.hidden = true;
}
"""

PRODUCT_JS = """const product = window.PRODUCT_DATA;
const colorInputs = document.querySelectorAll('input[name="color"]');
const quantityInput = document.querySelector('#quantity');
const priceLabel = document.querySelector('#price');
const stockLabel = document.querySelector('#stock-status');
const buyButton = document.querySelector('#checkout-btn');
const checkoutPanel = document.querySelector('#checkout-panel');
const closeButton = document.querySelector('#close-checkout');

function selectedColor() {
  const checked = document.querySelector('input[name="color"]:checked');
  return checked ? checked.value : product.defaultColor;
}

function updateAvailability() {
  const variant = product.variants[selectedColor()];
  priceLabel.textContent = formatPrice(variant.price);
  stockLabel.textContent = variant.stock > 0 ? `${variant.stock} in stock` : 'Out of stock';
  buyButton.disabled = variant.stock === 0;
}

function handleBuyNow() {
  const color = selectedColor();
  const variant = product.variants[color];
  const quantity = Number(quantityInput.value);
  renderCheckout({ name: product.name, color, quantity, unitPrice: variant.price });
  openCheckout(checkoutPanel);
}

colorInputs.forEach((input) => input.addEventListener('change', updateAvailability));
buyButton.addEventListener('click', handleBuyNow);
closeButton.addEventListener('click', () => closeCheckout(checkoutPanel));
updateAvailability();
"""

CART_TEST_JS = """const test = require('node:test');
const assert = require('node:assert/strict');

const { formatPrice, lineTotal } = require('../cart.js');

test('formats prices with two decimals', () => {
  assert.equal(formatPrice(149), '$149.00');
});

test('multiplies the unit price by the quantity', () => {
  assert.equal(lineTotal(149, 2), 298);
});

test('rounds totals to whole cents', () => {
  assert.equal(lineTotal(0.1, 3), 0.3);
});
"""

PACKAGE_JSON = """{
  "name": "product-page",
  "private": true,
  "scripts": {
    "test": "node --test"
  }
}
"""

CONSOLE_LOG = """[QA] Chrome 128 · /product/everyday-headphones · 2026-08-20 10:42
Uncaught TypeError: Cannot read properties of null (reading 'addEventListener')
    at product.js (top-level script)
[QA] Switching colour to Sand: price and stock text did not change (still "$149.00 · In stock").
[QA] Selecting Midnight: Buy Now still enabled, label still "In stock".
GET /product.js 200
GET /checkout.js 200
"""

QA_NOTES = """# QA regression notes - FE-4021

Build: storefront 2026.08.20-1 (today's deployment). Tester: Noah Reed.

Desktop (1440px) and mobile (375px), Chrome and Safari:

1. Load the product page and press Buy Now -> nothing happens. Same with Enter and Space.
2. Change colour -> price and stock text do not update.
3. Earlier build (before today): checkout opened, but we also logged these, still open:
   - Quantity 0, -2, or 2.5 opened checkout with totals like "Total: $-298.00".
   - Quantity 5 on Sand (3 in stock) was accepted.
   - Pressing Buy Now twice listed the product twice in the summary.
   - After opening checkout, screen-reader focus stayed on Buy Now, so the panel was not announced.

Please fix the regression and the open checkout issues together; release is blocked until checkout works.
"""

ACCEPTANCE = """# Checkout panel - acceptance notes (agreed with Product and UX)

- Buy Now opens the checkout panel by mouse and keyboard on desktop and mobile.
- Colour changes update price and stock; out-of-stock colours disable Buy Now.
- Quantity is a whole number from 1 to the selected colour's stock. Otherwise show a short
  message in the existing #quantity-error element and keep checkout closed.
- The summary always shows exactly one line for the current selection and the matching total.
- Opening the panel moves focus into it; Close hides it and returns focus to Buy Now.
- Existing styling, focus outlines, and the 480px mobile layout must stay as they are.
"""


FALLBACK_FILES = [
    {"path": "README.md", "content": FRONTEND_README},
    {"path": "index.html", "content": INDEX_HTML},
    {"path": "styles.css", "content": STYLES_CSS},
    {"path": "product-data.js", "content": PRODUCT_DATA_JS},
    {"path": "cart.js", "content": CART_JS},
    {"path": "checkout.js", "content": CHECKOUT_JS},
    {"path": "product.js", "content": PRODUCT_JS},
    {"path": "tests/cart.test.js", "content": CART_TEST_JS},
    {"path": "package.json", "content": PACKAGE_JSON},
]

FALLBACK_RESOURCES = [
    {"id": "console-log", "name": "browser-console.log", "type": "text", "content": CONSOLE_LOG},
    {"id": "qa-notes", "name": "qa-regression-notes.md", "type": "text", "content": QA_NOTES},
    {"id": "acceptance", "name": "checkout-acceptance.md", "type": "text", "content": ACCEPTANCE},
]
