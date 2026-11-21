import React, { useState } from 'react';
import { X, Building2, User, Mail, Phone, MapPin, Calendar, Tag, DollarSign } from 'lucide-react';

const STATUS_OPTIONS = ['New', 'Contacted', 'Meeting', 'Won', 'Lost'];

const toCanonicalCity = (str) => {
  if (!str) return '';
  return str
    .trim()
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
};

export default function EditLeadModal({ isOpen, onClose, lead, onSaveLead }) {
  const [formData, setFormData] = useState({
    companyName: lead?.companyName || '',
    contactPerson: lead?.contactPerson || '',
    email: lead?.email || '',
    phone: lead?.phone || '',
    city: lead?.city || '',
    status: lead?.status || 'New',
    followUpDate: lead?.followUpDate || '',
    dealValue: lead?.dealValue !== undefined ? lead.dealValue : '',
    notes: lead?.notes || ''
  });

  const [errors, setErrors] = useState({});

  if (!isOpen || !lead) return null;

  const validate = () => {
    const newErrors = {};
    if (!formData.companyName.trim()) newErrors.companyName = 'Company name is required';
    if (!formData.contactPerson.trim()) newErrors.contactPerson = 'Contact person is required';
    if (!formData.email.trim()) {
      newErrors.email = 'Email address is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      newErrors.email = 'Please enter a valid email address';
    }
    if (!formData.phone.trim()) newErrors.phone = 'Phone number is required';
    if (!formData.city.trim()) newErrors.city = 'City is required';
    if (!formData.followUpDate) newErrors.followUpDate = 'Follow-up date is required';
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

    onSaveLead({
      ...lead,
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
            <h2 className="modal-title">Edit Lead Details</h2>
            <p className="modal-subtitle">Update contact details, status, or follow-up schedule</p>
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
              <label htmlFor="edit-companyName" className="form-label">
                Company Name <span className="required-star">*</span>
              </label>
              <div className="input-with-icon">
                <Building2 size={16} className="input-icon" />
                <input
                  type="text"
                  id="edit-companyName"
                  name="companyName"
                  className={`form-input ${errors.companyName ? 'input-error' : ''}`}
                  value={formData.companyName}
                  onChange={handleChange}
                />
              </div>
              {errors.companyName && (
                <span className="error-message">{errors.companyName}</span>
              )}
            </div>

            {/* Contact Person */}
            <div className="form-group">
              <label htmlFor="edit-contactPerson" className="form-label">
                Contact Person <span className="required-star">*</span>
              </label>
              <div className="input-with-icon">
                <User size={16} className="input-icon" />
                <input
                  type="text"
                  id="edit-contactPerson"
                  name="contactPerson"
                  className={`form-input ${errors.contactPerson ? 'input-error' : ''}`}
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
              <label htmlFor="edit-city" className="form-label">
                City <span className="required-star">*</span>
              </label>
              <div className="input-with-icon">
                <MapPin size={16} className="input-icon" />
                <input
                  type="text"
                  id="edit-city"
                  name="city"
                  className={`form-input ${errors.city ? 'input-error' : ''}`}
                  value={formData.city}
                  onChange={handleChange}
                />
              </div>
              {errors.city && <span className="error-message">{errors.city}</span>}
            </div>

            {/* Email */}
            <div className="form-group">
              <label htmlFor="edit-email" className="form-label">
                Email Address <span className="required-star">*</span>
              </label>
              <div className="input-with-icon">
                <Mail size={16} className="input-icon" />
                <input
                  type="email"
                  id="edit-email"
                  name="email"
                  className={`form-input ${errors.email ? 'input-error' : ''}`}
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
              {errors.email && <span className="error-message">{errors.email}</span>}
            </div>

            {/* Phone */}
            <div className="form-group">
              <label htmlFor="edit-phone" className="form-label">
                Phone Number <span className="required-star">*</span>
              </label>
              <div className="input-with-icon">
                <Phone size={16} className="input-icon" />
                <input
                  type="tel"
                  id="edit-phone"
                  name="phone"
                  className={`form-input ${errors.phone ? 'input-error' : ''}`}
                  value={formData.phone}
                  onChange={handleChange}
                />
              </div>
              {errors.phone && <span className="error-message">{errors.phone}</span>}
            </div>

            {/* Status */}
            <div className="form-group">
              <label htmlFor="edit-status" className="form-label">
                Lead Status
              </label>
              <div className="input-with-icon">
                <Tag size={16} className="input-icon" />
                <select
                  id="edit-status"
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
              <label htmlFor="edit-followUpDate" className="form-label">
                Next Follow-up Date <span className="required-star">*</span>
              </label>
              <div className="input-with-icon">
                <Calendar size={16} className="input-icon" />
                <input
                  type="date"
                  id="edit-followUpDate"
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
              <label htmlFor="edit-dealValue" className="form-label">
                Estimated Deal Value ($)
              </label>
              <div className="input-with-icon">
                <DollarSign size={16} className="input-icon" />
                <input
                  type="number"
                  id="edit-dealValue"
                  name="dealValue"
                  className="form-input"
                  value={formData.dealValue}
                  onChange={handleChange}
                />
              </div>
            </div>

            {/* Notes */}
            <div className="form-group col-span-2">
              <label htmlFor="edit-notes" className="form-label">
                Opportunity Notes / Next Steps
              </label>
              <textarea
                id="edit-notes"
                name="notes"
                rows={3}
                className="form-input form-textarea"
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
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
