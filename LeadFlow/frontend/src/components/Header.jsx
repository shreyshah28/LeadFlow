import React from 'react';
import {
  Menu,
  Plus,
  Download,
  Upload,
  Calendar,
  Bell
} from 'lucide-react';
import { formatHeaderDate } from '../utils/dateUtils';

export default function Header({
  activeTab,
  onOpenAddModal,
  onOpenImportModal,
  onExportCSV,
  onToggleMobileSidebar,
  urgentCount,
  onNavigateUrgent
}) {
  const getTabTitle = () => {
    switch (activeTab) {
      case 'leads':
        return 'Leads Management';
      case 'followups':
        return 'Follow-up Reminders';
      case 'dashboard':
      default:
        return 'Dashboard Overview';
    }
  };

  const getTabSubtitle = () => {
    switch (activeTab) {
      case 'leads':
        return 'Manage, search, filter, and track all prospects';
      case 'followups':
        return 'Actionable overdue and today follow-up alerts';
      case 'dashboard':
      default:
        return 'Track your sales pipeline, conversions, and meetings';
    }
  };

  return (
    <header className="main-header">
      <div className="header-top-row">
        {/* Left: Mobile Toggle & Page Headings */}
        <div className="header-left">
          <button
            type="button"
            className="mobile-hamburger-btn"
            onClick={onToggleMobileSidebar}
            aria-label="Open menu"
          >
            <Menu size={22} />
          </button>

          <div className="header-titles">
            <h1 className="header-title">{getTabTitle()}</h1>
            <p className="header-subtitle">{getTabSubtitle()}</p>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="header-right">
          {/* Live Date Indicator */}
          <div className="header-date-badge" title="Current Date">
            <Calendar size={15} className="date-icon" />
            <span>{formatHeaderDate()}</span>
          </div>

          {/* Follow-up Urgent Bell */}
          <button
            type="button"
            className={`urgent-bell-btn ${urgentCount > 0 ? 'has-urgent' : ''}`}
            onClick={onNavigateUrgent}
            title={urgentCount > 0 ? `${urgentCount} follow-ups need attention` : 'No urgent follow-ups'}
            aria-label="View urgent follow-ups"
          >
            <Bell size={18} />
            {urgentCount > 0 && <span className="urgent-indicator-dot">{urgentCount}</span>}
          </button>

          {/* Import CSV Button */}
          <button
            type="button"
            className="btn btn-secondary header-btn"
            onClick={onOpenImportModal}
            title="Import leads from CSV file"
          >
            <Upload size={15} />
            <span className="btn-text">Import CSV</span>
          </button>

          {/* Export CSV Button */}
          <button
            type="button"
            className="btn btn-secondary header-btn"
            onClick={onExportCSV}
            title="Download CSV spreadsheet"
          >
            <Download size={15} />
            <span className="btn-text">Export CSV</span>
          </button>

          {/* Add Lead Primary CTA */}
          <button
            type="button"
            className="btn btn-primary header-btn add-lead-btn"
            onClick={onOpenAddModal}
            title="Create a new lead"
          >
            <Plus size={16} />
            <span className="btn-text">Add Lead</span>
          </button>
        </div>
      </div>
    </header>
  );
}
