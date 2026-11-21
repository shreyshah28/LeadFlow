import React, { useState } from 'react';
import {
  AlertTriangle,
  Clock,
  Calendar,
  CheckCircle2,
  Phone,
  Mail,
  ChevronRight,
  Sparkles,
  CalendarDays
} from 'lucide-react';
import { getFollowUpStatus, getRelativeDate } from '../utils/dateUtils';

export default function FollowUpPanel({
  leads = [],
  onUpdateStatus,
  onReschedule,
  onSelectLeadForEdit
}) {
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'overdue', 'today'

  // Partition leads by urgency
  const classifiedLeads = leads
    .map((lead) => {
      const followUp = getFollowUpStatus(lead.followUpDate);
      return { ...lead, followUp };
    })
    .filter((lead) => lead.status !== 'Won' && lead.status !== 'Lost'); // only active leads

  const overdueLeads = classifiedLeads.filter((l) => l.followUp.status === 'overdue');
  const todayLeads = classifiedLeads.filter((l) => l.followUp.status === 'today');

  const allUrgentLeads = [...overdueLeads, ...todayLeads].sort((a, b) => {
    // Sort overdue first, then by date ascending
    if (a.followUp.status === 'overdue' && b.followUp.status !== 'overdue') return -1;
    if (b.followUp.status === 'overdue' && a.followUp.status !== 'overdue') return 1;
    return (a.followUpDate || '').localeCompare(b.followUpDate || '');
  });

  const displayLeads =
    activeTab === 'overdue'
      ? overdueLeads
      : activeTab === 'today'
      ? todayLeads
      : allUrgentLeads;

  return (
    <section className="follow-up-panel card" aria-label="Follow-up Reminders">
      <div className="panel-header">
        <div className="panel-title-group">
          <div className="panel-icon-badge">
            <Clock size={18} />
          </div>
          <div>
            <h2 className="panel-title">Follow-up Reminders</h2>
            <p className="panel-subtitle">
              Calculated dynamically against today's date
            </p>
          </div>
        </div>

        {/* Tab Pills */}
        <div className="panel-tab-pills">
          <button
            type="button"
            className={`pill-btn ${activeTab === 'all' ? 'pill-active' : ''}`}
            onClick={() => setActiveTab('all')}
          >
            All Urgent ({allUrgentLeads.length})
          </button>
          <button
            type="button"
            className={`pill-btn pill-danger ${activeTab === 'overdue' ? 'pill-active-danger' : ''}`}
            onClick={() => setActiveTab('overdue')}
          >
            <AlertTriangle size={13} />
            <span>Overdue ({overdueLeads.length})</span>
          </button>
          <button
            type="button"
            className={`pill-btn pill-warning ${activeTab === 'today' ? 'pill-active-warning' : ''}`}
            onClick={() => setActiveTab('today')}
          >
            <Clock size={13} />
            <span>Due Today ({todayLeads.length})</span>
          </button>
        </div>
      </div>

      {/* Reminder Cards List */}
      <div className="reminders-list">
        {displayLeads.length === 0 ? (
          <div className="reminders-empty">
            <div className="empty-sparkle-box">
              <Sparkles size={24} className="sparkle-icon" />
            </div>
            <p className="empty-title">All caught up!</p>
            <p className="empty-desc">
              {activeTab === 'overdue'
                ? 'No overdue follow-ups right now. Great job keeping in touch!'
                : activeTab === 'today'
                ? 'No follow-ups due today.'
                : 'No urgent follow-up tasks currently pending.'}
            </p>
          </div>
        ) : (
          <div className="reminders-grid">
            {displayLeads.map((lead) => {
              const isOverdue = lead.followUp.status === 'overdue';

              return (
                <div
                  key={lead.id}
                  className={`reminder-card ${
                    isOverdue ? 'reminder-card-overdue' : 'reminder-card-today'
                  }`}
                >
                  <div className="reminder-card-top">
                    <div className="reminder-company-info">
                      <h3 className="reminder-company">{lead.companyName}</h3>
                      <span className="reminder-contact">{lead.contactPerson} • {lead.city}</span>
                    </div>

                    <span
                      className={`urgency-badge ${
                        isOverdue ? 'urgency-overdue' : 'urgency-today'
                      }`}
                    >
                      {isOverdue ? (
                        <>
                          <AlertTriangle size={12} />
                          <span>{lead.followUp.label}</span>
                        </>
                      ) : (
                        <>
                          <Clock size={12} />
                          <span>Due Today</span>
                        </>
                      )}
                    </span>
                  </div>

                  {lead.notes && (
                    <p className="reminder-notes" title={lead.notes}>
                      {lead.notes}
                    </p>
                  )}

                  <div className="reminder-details-bar">
                    <div className="reminder-contact-methods">
                      {lead.phone && (
                        <a
                          href={`tel:${lead.phone}`}
                          className="contact-link"
                          title={`Call ${lead.phone}`}
                        >
                          <Phone size={13} />
                          <span>{lead.phone}</span>
                        </a>
                      )}
                      {lead.email && (
                        <a
                          href={`mailto:${lead.email}`}
                          className="contact-link"
                          title={`Email ${lead.email}`}
                        >
                          <Mail size={13} />
                          <span>Email</span>
                        </a>
                      )}
                    </div>
                    <span className="current-status-pill status-tag-small">
                      Status: <strong>{lead.status}</strong>
                    </span>
                  </div>

                  {/* Action buttons */}
                  <div className="reminder-actions-row">
                    {lead.status === 'New' && (
                      <button
                        type="button"
                        className="btn-action-small btn-action-contacted"
                        onClick={() => onUpdateStatus(lead.id, 'Contacted')}
                      >
                        <CheckCircle2 size={13} />
                        <span>Mark Contacted</span>
                      </button>
                    )}

                    {lead.status === 'Contacted' && (
                      <button
                        type="button"
                        className="btn-action-small btn-action-meeting"
                        onClick={() => onUpdateStatus(lead.id, 'Meeting')}
                      >
                        <Calendar size={13} />
                        <span>Schedule Meeting</span>
                      </button>
                    )}

                    {lead.status === 'Meeting' && (
                      <button
                        type="button"
                        className="btn-action-small btn-action-won"
                        onClick={() => onUpdateStatus(lead.id, 'Won')}
                      >
                        <CheckCircle2 size={13} />
                        <span>Mark as Won</span>
                      </button>
                    )}

                    {/* Quick Postpone / Reschedule button */}
                    <button
                      type="button"
                      className="btn-action-small btn-action-reschedule"
                      title="Postpone follow-up by 2 days"
                      onClick={() => onReschedule(lead.id, getRelativeDate(2))}
                    >
                      <CalendarDays size={13} />
                      <span>+2 Days</span>
                    </button>

                    {/* Edit Lead */}
                    <button
                      type="button"
                      className="btn-action-small btn-action-edit"
                      onClick={() => onSelectLeadForEdit(lead)}
                      title="Edit full lead details"
                    >
                      <span>Edit</span>
                      <ChevronRight size={13} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
