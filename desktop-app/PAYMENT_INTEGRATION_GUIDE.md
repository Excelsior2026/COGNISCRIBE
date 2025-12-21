# CliniScribe Pro - Payment Integration Guide

## Overview

CliniScribe Pro needs a payment system to handle subscriptions for the professional OBS-powered audio recording features. Here are your best options for desktop app monetization:

---

## Recommended Payment Solutions

### 1. **Paddle** (⭐ RECOMMENDED for Desktop Apps)

**Why Paddle:**
- ✅ **Merchant of Record** - They handle ALL tax/VAT compliance globally
- ✅ **Desktop-focused** - Built for software subscriptions
- ✅ **Clean checkout** - Hosted payment pages or inline forms
- ✅ **Subscription management** - Automatic billing, upgrades, cancellations
- ✅ **Global payments** - Supports 100+ currencies, credit cards, PayPal, wire transfer
- ✅ **No PCI compliance needed** - They handle all security
- ✅ **Analytics included** - Revenue reporting, retention metrics

**Pricing:**
- 5% + 50¢ per transaction
- Includes all taxes, VAT, and compliance

**Integration Steps:**
1. Sign up at https://paddle.com
2. Create a product and pricing plan
3. Get your Vendor ID and Product ID
4. Use Paddle.js for checkout

**Example Implementation:**
```typescript
// Install Paddle SDK
npm install @paddle/paddle-js

// In your React component
import { initializePaddle } from '@paddle/paddle-js';

const paddle = await initializePaddle({
  environment: 'production',
  token: 'YOUR_CLIENT_SIDE_TOKEN',
});

// Trigger checkout
paddle.Checkout.open({
  items: [{ priceId: 'pri_cliniscribe_pro_monthly', quantity: 1 }],
});
```

**Webhook Integration:**
```rust
// In main.rs - handle subscription events
#[tauri::command]
async fn verify_subscription(paddle_subscription_id: String) -> Result<bool, String> {
    // Call Paddle API to verify subscription status
    // Store subscription info in config
    Ok(true)
}
```

---

### 2. **Stripe** (Good for Flexibility)

**Why Stripe:**
- ✅ **Industry standard** - Most trusted payment processor
- ✅ **Powerful API** - Complete control over payment flow
- ✅ **Subscription billing** - Sophisticated billing logic
- ✅ **Customer portal** - Built-in subscription management UI
- ❌ **You handle taxes** - Need to calculate VAT/sales tax yourself
- ❌ **PCI compliance** - More security responsibility

**Pricing:**
- 2.9% + 30¢ per transaction (US)
- Additional fees for international cards

**Integration Steps:**
1. Sign up at https://stripe.com
2. Create products and price plans
3. Generate API keys
4. Use Stripe Checkout or Elements

**Example Implementation:**
```typescript
// Install Stripe
npm install @stripe/stripe-js

import { loadStripe } from '@stripe/stripe-js';

const stripe = await loadStripe('pk_live_YOUR_KEY');

// Create checkout session via your backend
const response = await fetch('http://localhost:8080/create-checkout-session', {
  method: 'POST',
});

const session = await response.json();

// Redirect to Stripe checkout
stripe.redirectToCheckout({ sessionId: session.id });
```

**Backend (Python API):**
```python
import stripe
stripe.api_key = 'sk_live_YOUR_KEY'

@app.post('/create-checkout-session')
async def create_checkout():
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_cliniscribe_pro',
            'quantity': 1,
        }],
        mode='subscription',
        success_url='http://localhost:8080/success',
        cancel_url='http://localhost:8080/cancel',
    )
    return {'sessionId': session.id}
```

---

### 3. **Lemon Squeezy** (Great for SaaS/Subscriptions)

**Why Lemon Squeezy:**
- ✅ **Merchant of Record** - Like Paddle, handles taxes globally
- ✅ **Modern API** - Developer-friendly
- ✅ **Lower fees** - 5% for Merchant of Record service
- ✅ **Discount codes** - Built-in promotion system
- ✅ **License keys** - Can generate activation codes

**Pricing:**
- 5% + payment processing fees
- Includes tax/VAT handling

**Integration:**
```typescript
// Use Lemon.js
<script src="https://assets.lemonsqueezy.com/lemon.js"></script>

// Trigger checkout
window.LemonSqueezy.Url.Open('https://cliniscribe.lemonsqueezy.com/checkout/buy/PRODUCT_ID');
```

---

### 4. **License Key System** (One-Time Payment)

**Alternative Approach:**
If you prefer one-time purchases instead of subscriptions:

**Gumroad** or **Lemon Squeezy** can generate license keys:

```typescript
// Verify license key
#[tauri::command]
async fn activate_license(license_key: String) -> Result<bool, String> {
    // Call license verification API
    let response = reqwest::Client::new()
        .post("https://api.lemonsqueezy.com/v1/licenses/validate")
        .json(&json!({ "license_key": license_key }))
        .send()
        .await?;

    // Store activation status
    Ok(true)
}
```

---

## Recommended Architecture

### For CliniScribe Pro:

**1. Subscription Check on Startup:**
```typescript
// On app launch, check subscription status
const isProUser = await invoke('check_pro_subscription');

if (isProUser) {
  // Enable Pro features
  enableOBSRecording();
} else {
  // Show upgrade prompt
  showProUpgradeWizard();
}
```

**2. Backend Verification:**
```rust
// In config.rs
#[derive(Serialize, Deserialize, Clone)]
pub struct AppConfig {
    pub setup_completed: bool,
    pub pro_subscription_id: Option<String>,
    pub pro_expires_at: Option<String>,
    // ... other fields
}

// Verify subscription
pub async fn is_pro_active(config: &AppConfig) -> bool {
    if let Some(sub_id) = &config.pro_subscription_id {
        // Call payment provider API to verify
        // Return true if active, false if cancelled/expired
        true
    } else {
        false
    }
}
```

**3. Store Subscription Info:**
```rust
#[tauri::command]
async fn activate_pro_subscription(
    state: State<'_, AppState>,
    subscription_id: String,
    expires_at: String,
) -> Result<(), String> {
    let mut config = state.config.lock().await;
    config.pro_subscription_id = Some(subscription_id);
    config.pro_expires_at = Some(expires_at);
    save_config(&config).map_err(|e| e.to_string())?;
    Ok(())
}
```

---

## Implementation Checklist

### Phase 1: Payment Provider Setup
- [ ] Choose payment provider (Paddle recommended)
- [ ] Sign up and complete account setup
- [ ] Create product: "CliniScribe Pro"
- [ ] Set pricing (e.g., $9.99/month or $99/year)
- [ ] Get API keys

### Phase 2: Integration
- [ ] Add payment SDK to package.json
- [ ] Create checkout flow in ProUpgradeWizard
- [ ] Implement subscription verification endpoint
- [ ] Store subscription status in AppConfig
- [ ] Add webhook handler for subscription events

### Phase 3: Feature Gating
- [ ] Check Pro status before enabling OBS recording
- [ ] Show upgrade prompt for free users
- [ ] Add "Manage Subscription" in settings
- [ ] Handle subscription cancellation gracefully

### Phase 4: Testing
- [ ] Test successful payment flow
- [ ] Test subscription verification
- [ ] Test feature access with/without Pro
- [ ] Test subscription expiration
- [ ] Test cancellation flow

---

## Pricing Suggestions

**Monthly Subscription:**
- $9.99/month - Good balance for students
- $14.99/month - Premium tier with priority support

**Annual Subscription:**
- $99/year (~$8.25/month) - 2 months free
- $149/year (~$12.42/month) - Premium annual

**One-Time Purchase:**
- $199 - Lifetime Pro access
- Good for institutions buying in bulk

---

## Compliance Notes

### Student/Educational Pricing
- Offer 50% discount for students with .edu email
- Use Paddle's or Stripe's coupon system

### HIPAA Compliance
- If storing PHI, ensure payment provider is HIPAA compliant
- Paddle and Stripe both offer HIPAA-compliant options

### Refund Policy
- Offer 14-day money-back guarantee
- Clearly state in pricing page

---

## Next Steps

1. **Choose Paddle** (recommended) or Stripe
2. Create account and product
3. Update `ProUpgradeWizard.tsx` with real payment integration
4. Add subscription verification to config system
5. Test end-to-end flow
6. Launch! 🚀

---

## Support & Resources

**Paddle:**
- Docs: https://developer.paddle.com
- React Guide: https://developer.paddle.com/build/checkout/build-overlay-checkout

**Stripe:**
- Docs: https://stripe.com/docs
- Subscriptions: https://stripe.com/docs/billing/subscriptions/overview

**Lemon Squeezy:**
- Docs: https://docs.lemonsqueezy.com
- API: https://docs.lemonsqueezy.com/api
