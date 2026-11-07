// Dashboard.jsx - Complete Implementation of UI Interactions, Loading, and Chart Re-rendering
import React, { useState } from 'react';
import { useFetchDashboardData } from './useFetchDashboardData';
import { MetricsChart } from './components/MetricsChart'; // Wrapper around Chart.js / Recharts

export const Dashboard = () => {
  const [timeframe, setTimeframe] = useState('7d');
  const [metricType, setMetricType] = useState('all');

  // Triggered automatically when timeframe or metricType shifts
  const { data, loading, error, refetch } = useFetchDashboardData({ timeframe, type: metricType });

  return (
    <div className="dashboard-container" style={{ padding: '24px', fontFamily: 'sans-serif' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h2>Cloud Metrics Live Dashboard</h2>
        
        {/* User Interaction Controls */}
        <div className="controls">
          <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} disabled={loading} style={{ marginRight: '10px' }}>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>

          <select value={metricType} onChange={(e) => setMetricType(e.target.value)} disabled={loading}>
            <option value="all">All Metrics</option>
            <option value="storage">Storage Performance</option>
            <option value="compute">Execution Frequency</option>
          </select>
        </div>
      </header>

      {/* Conditional Interface States (Task 5) */}
      {loading && (
        <div className="loading-state" style={{ padding: '40px', textAlign: 'center', background: '#f5f5f5', borderRadius: '8px' }}>
          <div className="spinner" style={{ border: '4px solid #f3f3f3', borderTop: '4px solid #0078d4', borderRadius: '50%', width: '30px', height: '30px', animation: 'spin 1s linear infinite', margin: '0 auto 10px' }} />
          <p>Fetching real-time data from Azure Serverless Endpoint...</p>
        </div>
      )}

      {error && (
        <div className="error-state" style={{ padding: '20px', border: '1px solid #f5c2c2', background: '#fce8e6', color: '#a80000', borderRadius: '8px' }}>
          <h4>⚠️ Backend Service Unavailable</h4>
          <p>{error}</p>
          <button onClick={refetch} style={{ marginTop: '10px', padding: '8px 12px', background: '#a80000', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            Retry Connection
          </button>
        </div>
      )}

      {!loading && !error && data && (
        <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="chart-card" style={{ background: '#fff', padding: '15px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', borderRadius: '8px' }}>
            <h3>Data Volumes Trend</h3>
            {/* The canvas/svg chart element automatically recreates/updates when data changes */}
            <MetricsChart chartData={data.timeSeries} type="line" />
          </div>
          <div className="chart-card" style={{ background: '#fff', padding: '15px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', borderRadius: '8px' }}>
            <h3>Operational Status Code Distribution</h3>
            <MetricsChart chartData={data.distribution} type="bar" />
          </div>
        </div>
      )}
    </div>
  );
};
