import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import WrappedSubscriptionPage from './components/SubscriptionPage';
import InsightsDashboard from './components/InsightsDashboard';

const Placeholder = ({ title }) => <div><h2>{title}</h2></div>;

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Placeholder title="Login" />} />
        <Route path="/books" element={<Placeholder title="Books" />} />
        <Route path="/publish" element={<Placeholder title="Publish" />} />
        <Route path="/subscriptions" element={<WrappedSubscriptionPage />} />
        <Route path="/subscriptions/success" element={<Placeholder title="Subscription activated!" />} />
        <Route path="/subscriptions/cancel" element={<Placeholder title="Subscription cancelled." />} />
        <Route path="/progress" element={<Placeholder title="Progress" />} />
        <Route path="/analytics" element={<Placeholder title="Analytics" />} />
        <Route path="/insights" element={<InsightsDashboard />} />
      </Routes>
    </Router>
  );
}
