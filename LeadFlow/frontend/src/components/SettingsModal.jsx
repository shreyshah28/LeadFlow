import React, { useState } from 'react';
import { User, Bell, Database, RotateCcw, X, Check } from 'lucide-react';

export default function SettingsModal({
  isOpen,
  onClose,
  userProfile,
  onUpdateProfile,
  onResetSampleData,
  totalLeadsCount
}) {
  const [name, setName] = useState(userProfile?.name || 'Alex Morgan');
  const [role, setRole] = useState(userProfile?.role || 'Intern / Sales Rep');
  const [email, setEmail] = useState(userProfile?.email || 'alex.morgan@leadflow.demo');
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [savedSuccess, setSavedSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSaveProfile = (e) => {
    e.preventDefault();
    const initials = name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'AM';

    onUpdateProfile({
      name,
      role,
      email,
      initials
    });

    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 800);
  };

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div
        className="modal-container modal-md"
        onClick={(e) => e.stopPropagation()}
        tabIndex={-1}
      >
        <div className="modal-header">
          <div className="modal-title-group">
            <h2 className="modal-title">Settings & Preferences</h2>
            <p className="modal-subtitle">Customize user profile and workspace configuration</p>
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

        <div className="settings-body">
          {/* User Profile Section */}
          <form onSubmit={handleSaveProfile} className="settings-section">
            <div className="section-title-row">
              <User size={16} className="section-icon" />
              <h3 className="section-heading">Representative Profile</h3>
            </div>

            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your Name"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Role / Title</label>
                <input
                  type="text"
                  className="form-input"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  placeholder="e.g. Sales Intern"
                />
              </div>

              <div className="form-group col-span-2">
                <label className="form-label">Email</label>
                <input
                  type="email"
                  className="form-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div className="profile-save-row">
              <button type="submit" className="btn btn-primary btn-sm">
                {savedSuccess ? (
                  <>
                    <Check size={14} />
                    <span>Saved!</span>
                  </>
                ) : (
                  'Save Profile'
                )}
              </button>
            </div>
          </form>

          {/* Notifications Preferences */}
          <div className="settings-section">
            <div className="section-title-row">
              <Bell size={16} className="section-icon" />
              <h3 className="section-heading">Follow-up Notifications</h3>
            </div>

            <div className="toggle-list">
              <label className="toggle-item">
                <div className="toggle-info">
                  <span className="toggle-title">In-app follow-up reminders</span>
                  <span className="toggle-desc">
                    Show badge and alert when follow-ups are due today or overdue
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={emailAlerts}
                  onChange={(e) => setEmailAlerts(e.target.checked)}
                  className="toggle-checkbox"
                />
              </label>
            </div>
          </div>

          {/* Data & Storage Management */}
          <div className="settings-section">
            <div className="section-title-row">
              <Database size={16} className="section-icon" />
              <h3 className="section-heading">Data Management</h3>
            </div>

            <p className="text-muted text-sm mb-2">
              Currently managing <strong>{totalLeadsCount}</strong> leads in SQLite database.
            </p>

            <div className="danger-zone-box">
              <div className="danger-zone-info">
                <span className="danger-zone-title">Reset to Default Sample Data</span>
                <span className="danger-zone-desc">
                  Restores the original 12 sample leads with active overdue and today dates.
                </span>
              </div>
              <button
                type="button"
                className="btn btn-outline-danger btn-sm"
                onClick={() => {
                  if (window.confirm('Reset database back to initial 12 sample leads?')) {
                    onResetSampleData();
                    onClose();
                  }
                }}
              >
                <RotateCcw size={14} />
                <span>Reset Data</span>
              </button>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
