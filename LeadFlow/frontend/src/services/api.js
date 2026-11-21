/**
 * LeadFlow Backend API Service
 * Communicates with FastAPI REST backend (SQLite database source of truth)
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Helper to handle fetch responses and extract JSON or error details
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' 
          ? errJson.detail 
          : JSON.stringify(errJson.detail);
      }
    } catch {
      // response wasn't JSON
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export const api = {
  /**
   * Health check
   */
  async checkHealth() {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      return await handleResponse(res);
    } catch (err) {
      console.warn('Backend health check failed:', err.message);
      return null;
    }
  },

  /**
   * Get all leads with optional query parameters
   */
  async getLeads(params = {}) {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.status && params.status !== 'ALL') query.append('status', params.status);
    if (params.city && params.city !== 'ALL') query.append('city', params.city);
    if (params.urgency && params.urgency !== 'ALL') query.append('urgency', params.urgency);

    const url = `${API_BASE_URL}/leads${query.toString() ? `?${query.toString()}` : ''}`;
    const res = await fetch(url);
    return handleResponse(res);
  },

  /**
   * Get a single lead by ID
   */
  async getLead(id) {
    const res = await fetch(`${API_BASE_URL}/leads/${id}`);
    return handleResponse(res);
  },

  /**
   * Create a new lead
   */
  async createLead(leadData) {
    const res = await fetch(`${API_BASE_URL}/leads`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        companyName: leadData.companyName,
        contactPerson: leadData.contactPerson,
        email: leadData.email,
        phone: leadData.phone,
        city: leadData.city,
        status: leadData.status || 'New',
        followUpDate: leadData.followUpDate,
        dealValue: Number(leadData.dealValue) || 0,
        notes: leadData.notes || ''
      })
    });
    return handleResponse(res);
  },

  /**
   * Update an existing lead
   */
  async updateLead(id, updateData) {
    const payload = {};
    if (updateData.companyName !== undefined) payload.companyName = updateData.companyName;
    if (updateData.contactPerson !== undefined) payload.contactPerson = updateData.contactPerson;
    if (updateData.email !== undefined) payload.email = updateData.email;
    if (updateData.phone !== undefined) payload.phone = updateData.phone;
    if (updateData.city !== undefined) payload.city = updateData.city;
    if (updateData.status !== undefined) payload.status = updateData.status;
    if (updateData.followUpDate !== undefined) payload.followUpDate = updateData.followUpDate;
    if (updateData.dealValue !== undefined) payload.dealValue = Number(updateData.dealValue);
    if (updateData.notes !== undefined) payload.notes = updateData.notes;

    const res = await fetch(`${API_BASE_URL}/leads/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  /**
   * Delete a lead by ID
   */
  async deleteLead(id) {
    const res = await fetch(`${API_BASE_URL}/leads/${id}`, {
      method: 'DELETE'
    });
    return handleResponse(res);
  },

  /**
   * Get dashboard metrics and statistics
   */
  async getStats() {
    const res = await fetch(`${API_BASE_URL}/stats`);
    return handleResponse(res);
  },

  /**
   * Upload and import a CSV file into SQLite database
   */
  async uploadCSV(file) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE_URL}/leads/upload-csv`, {
      method: 'POST',
      body: formData
    });
    return handleResponse(res);
  },

  /**
   * Reset database back to default sample leads
   */
  async resetSampleLeads() {
    const res = await fetch(`${API_BASE_URL}/leads/reset-sample`, {
      method: 'POST'
    });
    return handleResponse(res);
  }
};
