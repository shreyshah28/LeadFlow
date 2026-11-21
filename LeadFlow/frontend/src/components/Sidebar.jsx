import React from 'react';
import {
  LayoutDashboard,
  Users,
  CalendarClock,
  Settings,
  Sparkles,
  TrendingUp,
  X
} from 'lucide-react';

export default function Sidebar({
  activeTab,
  setActiveTab,
  leadsCount,
  urgentCount,
  wonCount,
  isMobileOpen,
  setIsMobileOpen,
  onOpenSettings,
  userProfile
}) {
  const winRate = leadsCount > 0 ? Math.round((wonCount / leadsCount) * 100) : 0;

  const navItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      badge: null
    },
    {
      id: 'leads',
      label: 'Leads',
      icon: Users,
      badge: leadsCount
    },
    {
      id: 'followups',
      label: 'Follow-ups',
      icon: CalendarClock,
      badge: urgentCount > 0 ? urgentCount : null,
      badgeVariant: urgentCount > 0 ? 'urgent' : 'default'
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      badge: null
    }
  ];

  const handleNavClick = (tabId) => {
    if (tabId === 'settings') {
      onOpenSettings();
    } else {
      setActiveTab(tabId);
    }
    if (isMobileOpen) {
      setIsMobileOpen(false);
    }
  };

  return (
    <>
      {/* Mobile Backdrop overlay */}
      {isMobileOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setIsMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside className={`sidebar ${isMobileOpen ? 'sidebar-open' : ''}`}>
        {/* Branding & Logo */}
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <div className="brand-icon-box">
              <Sparkles className="brand-icon" size={20} />
            </div>
            <div className="brand-text">
              <span className="brand-name">LeadFlow</span>
              <span className="brand-tagline">CRM & Pipeline</span>
            </div>
          </div>
          <button
            type="button"
            className="mobile-close-btn"
            onClick={() => setIsMobileOpen(false)}
            aria-label="Close sidebar"
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation Section */}
        <div className="sidebar-nav-container">
          <div className="nav-group-label">MAIN NAVIGATION</div>
          <nav className="sidebar-nav">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  className={`nav-item ${isActive ? 'nav-item-active' : ''}`}
                  onClick={() => handleNavClick(item.id)}
                >
                  <div className="nav-item-content">
                    <Icon className="nav-icon" size={19} />
                    <span className="nav-label">{item.label}</span>
                  </div>
                  {item.badge !== null && (
                    <span
                      className={`nav-badge ${
                        item.badgeVariant === 'urgent' ? 'badge-urgent' : 'badge-neutral'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Pipeline Quick Health Progress */}
        <div className="sidebar-widget">
          <div className="widget-header">
            <div className="widget-title">
              <TrendingUp size={14} className="widget-icon" />
              <span>Pipeline Win Rate</span>
            </div>
            <span className="widget-value">{winRate}%</span>
          </div>
          <div className="progress-bar-bg">
            <div
              className="progress-bar-fill"
              style={{ width: `${Math.min(100, winRate)}%` }}
            />
          </div>
          <p className="widget-subtext">
            {wonCount} of {leadsCount} deals converted
          </p>
        </div>

        {/* Bottom Profile Section */}
        <div className="sidebar-footer">
          <button
            type="button"
            className="user-profile-btn"
            onClick={onOpenSettings}
            title="Click to view profile & settings"
          >
            <div className="profile-avatar">
              <span>{userProfile?.initials || 'AM'}</span>
              <span className="avatar-status-dot" title="Active" />
            </div>
            <div className="profile-info">
              <span className="profile-name">{userProfile?.name || 'Alex Morgan'}</span>
              <span className="profile-role">{userProfile?.role || 'Intern / Sales Rep'}</span>
            </div>
            <Settings size={16} className="profile-settings-icon" />
          </button>
        </div>
      </aside>
    </>
  );
}

