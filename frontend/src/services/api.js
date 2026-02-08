// src/services/api.js
const API_BASE_URL = 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  async checkHealth() {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      if (!response.ok) throw new Error('API health check failed');
      return await response.json();
    } catch (error) {
      console.error('Health check error:', error);
      throw error;
    }
  }

  async getApiInfo() {
    try {
      const response = await fetch(`${this.baseUrl}/`);
      if (!response.ok) throw new Error('Failed to fetch API info');
      return await response.json();
    } catch (error) {
      console.error('API info error:', error);
      throw error;
    }
  }

  async getFacilities() {
    try {
      const response = await fetch(`${this.baseUrl}/facilities`);
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Facilities data not found. Please process data first.');
        }
        throw new Error('Failed to fetch facilities');
      }
      return await response.json();
    } catch (error) {
      console.error('Fetch facilities error:', error);
      throw error;
    }
  }

  async getRegions() {
    try {
      const response = await fetch(`${this.baseUrl}/regions`);
      if (!response.ok) throw new Error('Failed to fetch regions');
      return await response.json();
    } catch (error) {
      console.error('Fetch regions error:', error);
      throw error;
    }
  }

  async askQuestion(question) {
    try {
      const response = await fetch(`${this.baseUrl}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        if (response.status === 400) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Bad request');
        }
        throw new Error('Failed to ask question');
      }

      return await response.json();
    } catch (error) {
      console.error('Ask question error:', error);
      throw error;
    }
  }

  async getTrace(traceId) {
    try {
      const response = await fetch(`${this.baseUrl}/trace/${traceId}`);
      if (!response.ok) throw new Error('Failed to fetch trace');
      return await response.json();
    } catch (error) {
      console.error('Fetch trace error:', error);
      throw error;
    }
  }
}

export const apiService = new ApiService();