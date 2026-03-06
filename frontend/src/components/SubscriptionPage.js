import React, { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, useStripe } from '@stripe/react-stripe-js';
import axios from 'axios';

const stripePublishableKey = process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY;
const stripePromise = stripePublishableKey ? loadStripe(stripePublishableKey) : null;

const SubscriptionPage = () => {
  const [tier, setTier] = useState('basic');
  const [loading, setLoading] = useState(false);
  const stripe = useStripe();

  const handleSubscribe = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post('http://localhost:8000/payments/create-checkout-session',  // via Kong
        { tier },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );

      const { id: sessionId } = data;

      const { error } = await stripe.redirectToCheckout({ sessionId });

      if (error) console.error(error);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div>
      <h2>Choose Your OpenLeaf Plus Plan</h2>
      <div>
        <label>
          <input type="radio" value="basic" checked={tier === 'basic'} onChange={() => setTier('basic')} />
          Basic - $9.99/mo (e-books only)
        </label>
      </div>
      <div>
        <label>
          <input type="radio" value="premium" checked={tier === 'premium'} onChange={() => setTier('premium')} />
          Premium - $14.99/mo (e-books + audiobooks)
        </label>
      </div>
      <button onClick={handleSubscribe} disabled={loading || !stripe}>
        {loading ? 'Processing...' : 'Subscribe Now'}
      </button>
    </div>
  );
};

export default function WrappedSubscriptionPage() {
  if (!stripePromise) {
    return (
      <div>
        <h2>Choose Your OpenLeaf Plus Plan</h2>
        <p>Stripe publishable key is not configured. Set REACT_APP_STRIPE_PUBLISHABLE_KEY in frontend/.env.</p>
      </div>
    );
  }

  return (
    <Elements stripe={stripePromise}>
      <SubscriptionPage />
    </Elements>
  );
}
