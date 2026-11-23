import React, { useState, useEffect } from 'react';
import { User, Bell, Database, RotateCcw, X, Check, Mail, Send, AlertCircle, Clock, ShieldCheck, CheckCircle2, Loader2 } from 'lucide-react';
import { api } from '../services/api';

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

  // Email status & test email states
  const [emailStatus, setEmailStatus] = useState(null);
  const [isSendingTest, setIsSendingTest] = useState(false);
  const [testEmailFeedback, setTestEmailFeedback] = useState(null);

  useEffect(() => {
    if (!isOpen) return;
    let isMounted = true;
    api.getEmailStatus()
      .then((status) => {
        if (isMounted && status) setEmailStatus(status);
      })
      .catch((err) => {
        console.warn('Failed to load email status:', err);
      });
    return () => {
      isMounted = false;
    };
  }, [isOpen]);

  const handleSendTestEmail = async () => {
    setIsSendingTest(true);
    setTestEmailFeedback(null);
    try {
      const res = await api.sendTestEmail();
      setTestEmailFeedback({
        type: 'success',
        text: res.message || 'Test email sent successfully! Please check administrator inbox.'
      });
    } catch (err) {
      setTestEmailFeedback({
        type: 'error',
        text: err.message || 'Failed to send test email. Please check server email configuration.'
      });
    } finally {
      setIsSendingTest(false);
    }
  };

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

          {/* Daily Follow-up Email (Internship Feature) */}
          <div className="settings-section">
            <div className="section-title-row">
              <Mail size={16} className="section-icon" />
              <h3 className="section-heading">Daily Follow-up Email</h3>
            </div>

            <p className="text-muted text-sm mb-3">
              Automated morning briefing sent to administrator with follow-ups scheduled for today and overdue leads.
            </p>

            <div className="email-config-card">
              <div className="email-status-top">
                <div className="email-pill-container">
                  <span
                    className={`email-badge ${
                      emailStatus?.enabled && emailStatus?.configured
                        ? 'email-badge-active'
                        : emailStatus?.configured
                        ? 'email-badge-disabled'
                        : 'email-badge-unconfigured'
                    }`}
                  >
                    <span className="email-status-indicator"></span>
                    {emailStatus?.enabled && emailStatus?.configured
                      ? 'Daily Dispatch Active'
                      : emailStatus?.configured
                      ? 'Dispatch Disabled'
                      : 'Not Configured'}
                  </span>
                </div>

                <button
                  type="button"
                  className="btn btn-outline-primary btn-sm test-email-btn"
                  onClick={handleSendTestEmail}
                  disabled={isSendingTest || !emailStatus?.configured}
                  title={
                    !emailStatus?.configured
                      ? 'Configure RESEND_API_KEY and recipient in backend environment to enable test email.'
                      : 'Send a live test email to administrator inbox.'
                  }
                >
                  {isSendingTest ? (
                    <>
                      <Loader2 size={13} className="spin-icon" />
                      <span>Sending...</span>
                    </>
                  ) : (
                    <>
                      <Send size={13} />
                      <span>Send Test Email</span>
                    </>
                  )}
                </button>
              </div>

              <div className="email-meta-grid">
                <div className="email-meta-row">
                  <span className="email-meta-label">Recipient</span>
                  <span className="email-meta-value">{emailStatus?.recipient_masked || 'Not configured'}</span>
                </div>
                <div className="email-meta-row">
                  <span className="email-meta-label">Scheduled Time</span>
                  <span className="email-meta-value">
                    <Clock size={12} className="meta-icon" /> {emailStatus?.scheduled_time || '8:00 AM Asia/Kolkata'}
                  </span>
                </div>
                <div className="email-meta-row">
                  <span className="email-meta-label">Timezone</span>
                  <span className="email-meta-value">{emailStatus?.timezone || 'Asia/Kolkata'}</span>
                </div>
                <div className="email-meta-row">
                  <span className="email-meta-label">Duplicate Prevention</span>
                  <span className="email-meta-value">
                    <ShieldCheck size={12} className="meta-icon" /> {emailStatus?.duplicate_prevention || 'Enabled (1 per calendar day)'}
                  </span>
                </div>
              </div>

              {testEmailFeedback && (
                <div className={`test-feedback-box ${testEmailFeedback.type}`}>
                  {testEmailFeedback.type === 'success' ? (
                    <CheckCircle2 size={15} className="feedback-icon" />
                  ) : (
                    <AlertCircle size={15} className="feedback-icon" />
                  )}
                  <span className="feedback-text">{testEmailFeedback.text}</span>
                </div>
              )}
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
