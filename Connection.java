// config.js - Centralized Environment Configuration
export const API_CONFIG = {
  AZURE_FUNCTION_URL: process.env.REACT_APP_AZURE_FUNCTION_URL || 'https://<person1-function-app>.azurewebsites.net/api/GetData',
  TIMEOUT_MS: 8000
};

// useFetchDashboardData.js - React Custom Hook for Data Fetching & State Management
import { useState, useEffect, useCallback } from 'react';
import { API_CONFIG } from './config';

export const useFetchDashboardData = (filterParams) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    // Create an abort controller to handle quick user interactions/unmounts
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT_MS);

    try {
      const url = new URL(API_CONFIG.AZURE_FUNCTION_URL);
      if (filterParams) {
        Object.keys(filterParams).forEach(key => url.searchParams.append(key, filterParams[key]));
      }

      const response = await fetch(url, {
        method: 'GET',
        signal: controller.signal,
        headers: { 'Accept': 'application/json' }
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Server Error: ${response.status} (${response.statusText})`);
      }

      const jsonPayload = await response.json();
      setData(jsonPayload);
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Connection timed out. Please check if the backend service is running.');
      } else {
        setError(err.message || 'An unexpected error occurred while loading data.');
      }
    } finally {
      setLoading(false);
    }
  }, [filterParams]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
};
