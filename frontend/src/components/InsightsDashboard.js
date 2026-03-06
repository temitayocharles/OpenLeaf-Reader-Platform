import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const InsightsDashboard = () => {
  const [bookStats, setBookStats] = useState({});
  const [globalStats, setGlobalStats] = useState({});

  useEffect(() => {
    // Fetch for a sample book or user favorites
    axios.get('http://localhost:8000/analytics/books/sample_book_id', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    }).then(res => setBookStats(res.data));

    // Global (admin)
    axios.get('http://localhost:8000/analytics/global', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    }).then(res => setGlobalStats(res.data)).catch(() => {});
  }, []);

  const chartData = {
    labels: ['Completion Rate'],
    datasets: [{
      label: 'Estimated %',
      data: [bookStats.estimated_completion_rate || 0],
      backgroundColor: 'rgba(75,192,192,0.6)',
    }]
  };

  return (
    <div>
      <h2>Reading Insights</h2>
      {bookStats.total_pages_read && (
        <>
          <p>Total pages read (sample book): {bookStats.total_pages_read}</p>
          <p>Unique readers: {bookStats.unique_readers}</p>
          <Bar data={chartData} options={{ responsive: true }} />
        </>
      )}
      {globalStats.total_self_published && (
        <p>Self-published books on platform: {globalStats.total_self_published}</p>
      )}
    </div>
  );
};

export default InsightsDashboard;
