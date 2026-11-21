import React, { useState } from 'react';
import { X, Building2, User, Mail, Phone, MapPin, Calendar, Tag, DollarSign } from 'lucide-react';
import { getRelativeDate } from '../utils/dateUtils';

const STATUS_OPTIONS = ['New', 'Contacted', 'Meeting', 'Won', 'Lost'];

const toCanonicalCity = (str) => {
  if (!str) return '';
  return str
    .trim()
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
};

export default function AddLeadModal({ isOpen, onClose, onAddLead }) {
  const [formData, setFormData] = useState({
    companyName: '',
    contactPerson: '',
    email: '',
    phone: '',
    city: '',
    status: 'New',
    followUpDate: getRelativeDate(1), // defaults to tomorrow
    dealValue: '',
    notes: ''
  });

  const [errors, setErrors] = useState({});

  if (!isOpen) return null;

  const validate = () => {
    const newErrors = {};
    if (!formData.companyName.trim()) {
      newErrors.companyName = 'Company name is required';
    }
    if (!formData.contactPerson.trim()) {
      newErrors.contactPerson = 'Contact person is required';
    }
    if (!formData.email.trim()) {
      newErrors.email = 'Email address is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      newErrors.email = 'Please enter a valid email address';
    }
    if (!formData.phone.trim()) {
      newErrors.phone = 'Phone number is required';
    }
    if (!formData.city.trim()) {
      newErrors.city = 'City is required';
    }
    if (!formData.followUpDate) {
      newErrors.followUpDate = 'Follow-up date is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;

    onAddLead({
      companyName: formData.companyName.trim(),
      contactPerson: formData.contactPerson.trim(),
      email: formData.email.trim(),
      phone: formData.phone.trim(),
      city: toCanonicalCity(formData.city),
      status: formData.status,
      followUpDate: formData.followUpDate,
      dealValue: formData.dealValue ? parseFloat(formData.dealValue) : 0,
      notes: formData.notes.trim()
    });

    // Reset form after submission
    setFormData({
      companyName: '',
      contactPerson: '',
      email: '',
      phone: '',
      city: '',
      status: 'New',
      followUpDate: getRelativeDate(1),
      dealValue: '',
      notes: ''
    });
    setErrors({});
    onClose();
  };

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div
        className="modal-container"
        onClick={(e) => e.stopPropagation()}
        tabIndex={-1}
      >
        <div className="modal-header">
          <div className="modal-title-group">
            <h2 className="modal-title">Add New Lead</h2>
            <p className="modal-subtitle">Enter prospect contact and qualification details</p>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-grid">
            {/* Company Name */}
            <div className="form-group col-span-2">
              <label htmlFor="companyName" className="form-label">
                Company Name <span className="required-star">*</span>
              </label>
              <div className="input-with-icon">
                <Building2 size={16} className="input-icon" />
                <input
                  type="text"
                  id="companyName"
                  name="companyName"
                  className={`form-input ${errors.companyName ? 'input-error' : ''}`}
                  placeholder="e.g. Acme Corporation"
                  value={formData.companyName}
                  onChange={handleChange}
                  autoFocus
                />
              </div>
              {errors.companyName && (
                <span className="error-message">{errors.companyName}</span>
              )}
            </div>

            {/* Contact Person */}
            <div className="form-group">
              <label htmlFor="contactPerson" className="form-label">
                Contact Person <span className="required-star">*</span>
              </label>
              <div className="input-with-icon">
                <User size={16} className="input-icon" />
                <input
                  type="text"
                  id="contactPerson"
                  name="contactPerson"
                  className={`form-input ${errors.contactPerson ? 'input-error' : ''}`}
                  placeholder="e.g. Jane Doe"
                  value={formData.contactPerson}
                  onChange={handleChange}
                />
              </div>
              {errors.contactPerson && (
                <span className="error-message">{errors.contactPerson}</span>
              )}
            </div>

            {/* City */}
            <div className="form-group">
              <label htmlFor="city" className="form-label">
                City <span className="required-star">*</span>
              </label>
              <div className="input-with-icon">
                <MapPin size={16} className="input-icon" />
                <input
                  type="text"
                  id="city"
                  name="city"
                  className={`form-input ${errors.city ? 'input-error' : ''}`}
                  placeholder="e.g. San Francisco"
                  value={formData.city}
                  onChange={handleChange}
                />
              </div>
              {errors.city && <span className="error-message">{errors.city}</span>}
            </div>

            {/* Email */}
            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Email Address <span className="required-star">*</span>
              </label>
              <div className="input-with-icon">
                <Mail size={16} className="input-icon" />
                <input
                  type="email"
                  id="email"
                  name="email"
                  className={`form-input ${errors.email ? 'input-error' : ''}`}
                  placeholder="e.g. jane@acme.com"
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
              {errors.email && <span className="error-message">{errors.email}</span>}
            </div>

            {/* Phone */}
            <div className="form-group">
              <label htmlFor="phone" className="form-label">
                Phone Number <span className="required-star">*</span>
              </label>
              <div className="input-with-icon">
                <Phone size={16} className="input-icon" />
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  className={`form-input ${errors.phone ? 'input-error' : ''}`}
                  placeholder="e.g. +1 (555) 000-1234"
                  value={formData.phone}
                  onChange={handleChange}
                />
              </div>
              {errors.phone && <span className="error-message">{errors.phone}</span>}
            </div>

            {/* Status */}
            <div className="form-group">
              <label htmlFor="status" className="form-label">
                Lead Status
              </label>
              <div className="input-with-icon">
                <Tag size={16} className="input-icon" />
                <select
                  id="status"
                  name="status"
                  className="form-input form-select"
                  value={formData.status}
                  onChange={handleChange}
                >
                  {STATUS_OPTIONS.map((st) => (
                    <option key={st} value={st}>
                      {st}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Next Follow-up Date */}
            <div className="form-group">
              <label htmlFor="followUpDate" className="form-label">
                Next Follow-up Date <span className="required-star">*</span>
              </label>
              <div className="input-with-icon">
                <Calendar size={16} className="input-icon" />
                <input
                  type="date"
                  id="followUpDate"
                  name="followUpDate"
                  className={`form-input ${errors.followUpDate ? 'input-error' : ''}`}
                  value={formData.followUpDate}
                  onChange={handleChange}
                />
              </div>
              {errors.followUpDate && (
                <span className="error-message">{errors.followUpDate}</span>
              )}
            </div>

            {/* Deal Value */}
            <div className="form-group col-span-2">
              <label htmlFor="dealValue" className="form-label">
                Estimated Deal Value ($)
              </label>
              <div className="input-with-icon">
                <DollarSign size={16} className="input-icon" />
                <input
                  type="number"
                  id="dealValue"
                  name="dealValue"
                  className="form-input"
                  placeholder="e.g. 25000"
                  value={formData.dealValue}
                  onChange={handleChange}
                />
              </div>
            </div>

            {/* Notes */}
            <div className="form-group col-span-2">
              <label htmlFor="notes" className="form-label">
                Opportunity Notes / Next Steps
              </label>
              <textarea
                id="notes"
                name="notes"
                rows={3}
                className="form-input form-textarea"
                placeholder="Key meeting notes, pain points, or follow-up agenda..."
                value={formData.notes}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Create Lead
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
