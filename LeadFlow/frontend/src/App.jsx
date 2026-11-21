import React, { useState, useEffect, useMemo, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardStats from './components/DashboardStats';
import FollowUpPanel from './components/FollowUpPanel';
import LeadsTable from './components/LeadsTable';
import AddLeadModal from './components/AddLeadModal';
import EditLeadModal from './components/EditLeadModal';
import DeleteConfirmModal from './components/DeleteConfirmModal';
import SettingsModal from './components/SettingsModal';
import ImportCSVModal from './components/ImportCSVModal';
import Toast from './components/Toast';

import { api } from './services/api';
import { INITIAL_LEADS } from './data/sampleLeads';
import { getFollowUpStatus } from './utils/dateUtils';
import { exportLeadsToCSV } from './utils/csvExport';

const PROFILE_KEY = 'leadflow_profile_v2';
const THEME_KEY = 'leadflow_theme';

export default function App() {
  // 1. Leads State (SQLite backend is the primary source of truth)
  const [leads, setLeads] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [backendConnected, setBackendConnected] = useState(null);

  // 2. Theme State (Light / Dark Mode with persistent localStorage)
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem(THEME_KEY);
      if (saved === 'dark' || saved === 'light') return saved;
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
      }
    } catch {
      // ignore
    }
    return 'light';
  });

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      // ignore
    }
    if (theme === 'dark') {
      document.documentElement.classList.add('dark-theme');
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark-theme');
      document.documentElement.setAttribute('data-theme', 'light');
    }
  }, [theme]);

  // Optional keyboard shortcut: Ctrl+D toggles theme
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'd') {
        e.preventDefault();
        toggleTheme();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleTheme]);

  // 2. User Profile State (Stored in localStorage for convenience)
  const [userProfile, setUserProfile] = useState(() => {
    try {
      const stored = localStorage.getItem(PROFILE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (e) {
      console.error('Failed reading profile from localStorage', e);
    }
    return {
      name: 'Alex Morgan',
      role: 'Sales Representative',
      email: 'alex.morgan@leadflow.demo',
      initials: 'AM'
    };
  });

  // 3. Navigation & Filtering State
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' | 'leads' | 'followups'
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // 4. Modals State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingLead, setEditingLead] = useState(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deletingLead, setDeletingLead] = useState(null);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  // 5. Toast Feedback State
  const [toast, setToast] = useState(null);

  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type });
  }, []);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => {
        setToast(null);
      }, 3500);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  // Persist user profile preferences
  useEffect(() => {
    try {
      localStorage.setItem(PROFILE_KEY, JSON.stringify(userProfile));
    } catch (e) {
      console.error('Failed saving profile to localStorage', e);
    }
  }, [userProfile]);

  // Fetch leads from SQLite backend
  const fetchLeads = useCallback(async () => {
    try {
      const data = await api.getLeads();
      setLeads(data);
      setBackendConnected(true);
    } catch (err) {
      console.warn('Backend unavailable or starting, using fallback:', err.message);
      setBackendConnected(false);
      setLeads((prev) => (prev.length > 0 ? prev : INITIAL_LEADS));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    api.getLeads()
      .then((data) => {
        if (isMounted) {
          setLeads(data);
          setBackendConnected(true);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.warn('Backend unavailable or starting, using fallback:', err.message);
          setBackendConnected(false);
          setLeads((prev) => (prev.length > 0 ? prev : INITIAL_LEADS));
          setIsLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // Calculated Metrics
  const { wonCount, urgentCount } = useMemo(() => {
    let won = 0;
    let urgent = 0;
    leads.forEach((l) => {
      if (l.status === 'Won') won++;
      if (l.status !== 'Won' && l.status !== 'Lost') {
        const f = getFollowUpStatus(l.followUpDate);
        if (f.status === 'overdue' || f.status === 'today') {
          urgent++;
        }
      }
    });
    return { wonCount: won, urgentCount: urgent };
  }, [leads]);

  // CRUD Handlers via Backend API
  const handleAddLead = async (newLeadData) => {
    try {
      const created = await api.createLead(newLeadData);
      setLeads((prev) => [created, ...prev]);
      showToast(`Lead for "${created.companyName}" added to database!`, 'success');
      setStatusFilter('ALL');
    } catch (err) {
      showToast(`Failed to add lead: ${err.message}`, 'error');
    }
  };

  const handleUpdateStatus = async (leadId, newStatus) => {
    // Optimistic UI update
    setLeads((prev) =>
      prev.map((lead) => {
        if (lead.id === leadId) {
          return { ...lead, status: newStatus };
        }
        return lead;
      })
    );
    try {
      await api.updateLead(leadId, { status: newStatus });
      showToast(`Status updated to ${newStatus}`, 'info');
    } catch (err) {
      showToast(`Failed to update status: ${err.message}`, 'error');
      fetchLeads(true);
    }
  };

  const handleSaveEdit = async (updatedLead) => {
    try {
      const saved = await api.updateLead(updatedLead.id, updatedLead);
      setLeads((prev) =>
        prev.map((lead) => (lead.id === saved.id ? saved : lead))
      );
      showToast(`Lead "${saved.companyName}" updated in database!`, 'success');
    } catch (err) {
      showToast(`Failed to update lead: ${err.message}`, 'error');
    }
  };

  const handleConfirmDelete = async (leadId) => {
    const leadToDelete = leads.find((l) => l.id === leadId);
    try {
      await api.deleteLead(leadId);
      setLeads((prev) => prev.filter((lead) => lead.id !== leadId));
      showToast(`Lead "${leadToDelete?.companyName || ''}" deleted from database.`, 'warning');
    } catch (err) {
      showToast(`Failed to delete lead: ${err.message}`, 'error');
    }
  };

  const handleReschedule = async (leadId, newDate) => {
    try {
      const updated = await api.updateLead(leadId, { followUpDate: newDate });
      setLeads((prev) =>
        prev.map((lead) => (lead.id === updated.id ? updated : lead))
      );
      showToast('Follow-up rescheduled in database!', 'success');
    } catch (err) {
      showToast(`Failed to reschedule: ${err.message}`, 'error');
    }
  };

  const handleExportCSV = (leadsToExport) => {
    const target = leadsToExport && leadsToExport.length > 0 ? leadsToExport : leads;
    const ok = exportLeadsToCSV(target);
    if (ok) {
      showToast(`Exported ${target.length} leads to CSV`, 'success');
    }
  };

  const handleResetSampleData = async () => {
    try {
      await api.resetSampleLeads();
      const fresh = await api.getLeads();
      setLeads(fresh);
      showToast('Database reset to original sample leads.', 'info');
    } catch (err) {
      showToast(`Failed to reset: ${err.message}`, 'error');
    }
  };

  const handleCSVImportSuccess = async (importResult) => {
    showToast(importResult.message || `Imported ${importResult.imported_count} leads!`, 'success');
    fetchLeads(true);
  };

  const handleOpenEdit = (lead) => {
    setEditingLead(lead);
    setIsEditModalOpen(true);
  };

  const handleOpenDelete = (lead) => {
    setDeletingLead(lead);
    setIsDeleteModalOpen(true);
  };

  const handleSelectStatusFilter = (filterVal) => {
    setStatusFilter(filterVal);
    if (activeTab === 'followups') {
      setActiveTab('leads');
    }
  };

  return (
    <div className="leadflow-app-layout">
      {/* Sidebar Component */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        leadsCount={leads.length}
        urgentCount={urgentCount}
        wonCount={wonCount}
        isMobileOpen={isMobileSidebarOpen}
        setIsMobileOpen={setIsMobileSidebarOpen}
        onOpenSettings={() => setIsSettingsModalOpen(true)}
        userProfile={userProfile}
      />

      {/* Main Content Workspace */}
      <div className="main-content-area">
        {/* Header Navigation Bar */}
        <Header
          activeTab={activeTab}
          onOpenAddModal={() => setIsAddModalOpen(true)}
          onOpenImportModal={() => setIsImportModalOpen(true)}
          onExportCSV={() => handleExportCSV(leads)}
          onToggleMobileSidebar={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
          urgentCount={urgentCount}
          onNavigateUrgent={() => setActiveTab('followups')}
          theme={theme}
          onToggleTheme={toggleTheme}
        />

        {/* Backend Connection Indicator Bar (Displays if backend is offline) */}
        {backendConnected === false && (
          <div className="backend-offline-banner">
            <span>
              <strong>Note:</strong> FastAPI backend is not detected at <code>http://localhost:8000</code>.
              Running in offline preview mode. Start backend with <code>uvicorn main:app --reload</code>.
            </span>
            <button
              type="button"
              className="btn btn-sm btn-secondary retry-btn"
              onClick={() => fetchLeads()}
            >
              Retry Connection
            </button>
          </div>
        )}

        {/* Dynamic Page Views */}
        <main className="content-workspace">
          {isLoading ? (
            <div className="loading-state-container">
              <div className="loading-spinner"></div>
              <p>Connecting to SQLite database...</p>
            </div>
          ) : (
            <>
              {/* View 1: Dashboard Overview (Shows Stats, Follow-up Panel, and Table) */}
              {activeTab === 'dashboard' && (
                <div className="view-container">
                  {/* Summary Stats Overview */}
                  <DashboardStats
                    leads={leads}
                    activeStatusFilter={statusFilter}
                    onSelectStatusFilter={handleSelectStatusFilter}
                  />

                  {/* Follow-up Urgency Panel */}
                  <FollowUpPanel
                    leads={leads}
                    onUpdateStatus={handleUpdateStatus}
                    onReschedule={handleReschedule}
                    onSelectLeadForEdit={handleOpenEdit}
                  />

                  {/* Comprehensive Leads Table */}
                  <section className="dashboard-table-section">
                    <div className="section-header-row">
                      <div>
                        <h2 className="section-title">All Tracked Leads</h2>
                        <p className="section-subtitle">
                          Filter, sort, search, and update pipeline statuses directly
                        </p>
                      </div>
                    </div>

                    <LeadsTable
                      leads={leads}
                      onUpdateStatus={handleUpdateStatus}
                      onOpenAddModal={() => setIsAddModalOpen(true)}
                      onOpenEditModal={handleOpenEdit}
                      onOpenImportModal={() => setIsImportModalOpen(true)}
                      onDeleteLead={handleOpenDelete}
                      onExportCSV={handleExportCSV}
                      statusFilter={statusFilter}
                      setStatusFilter={setStatusFilter}
                      searchQuery={searchQuery}
                      setSearchQuery={setSearchQuery}
                    />
                  </section>
                </div>
              )}

              {/* View 2: Leads Management View */}
              {activeTab === 'leads' && (
                <div className="view-container">
                  <LeadsTable
                    leads={leads}
                    onUpdateStatus={handleUpdateStatus}
                    onOpenAddModal={() => setIsAddModalOpen(true)}
                    onOpenEditModal={handleOpenEdit}
                    onOpenImportModal={() => setIsImportModalOpen(true)}
                    onDeleteLead={handleOpenDelete}
                    onExportCSV={handleExportCSV}
                    statusFilter={statusFilter}
                    setStatusFilter={setStatusFilter}
                    searchQuery={searchQuery}
                    setSearchQuery={setSearchQuery}
                  />
                </div>
              )}

              {/* View 3: Follow-ups Reminders View */}
              {activeTab === 'followups' && (
                <div className="view-container">
                  <FollowUpPanel
                    leads={leads}
                    onUpdateStatus={handleUpdateStatus}
                    onReschedule={handleReschedule}
                    onSelectLeadForEdit={handleOpenEdit}
                  />

                  {/* Quick Table showing all leads reference */}
                  <div className="followup-leads-section">
                    <div className="section-header-row">
                      <div>
                        <h3 className="section-title">All Leads Reference</h3>
                        <p className="section-subtitle">
                          Review contact information and schedules
                        </p>
                      </div>
                    </div>

                    <LeadsTable
                      leads={leads}
                      onUpdateStatus={handleUpdateStatus}
                      onOpenAddModal={() => setIsAddModalOpen(true)}
                      onOpenEditModal={handleOpenEdit}
                      onOpenImportModal={() => setIsImportModalOpen(true)}
                      onDeleteLead={handleOpenDelete}
                      onExportCSV={handleExportCSV}
                      statusFilter={statusFilter}
                      setStatusFilter={setStatusFilter}
                      searchQuery={searchQuery}
                      setSearchQuery={setSearchQuery}
                    />
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {/* Modals & Dialogs */}
      <AddLeadModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAddLead={handleAddLead}
      />

      <EditLeadModal
        key={editingLead?.id || 'none'}
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setEditingLead(null);
        }}
        lead={editingLead}
        onSaveLead={handleSaveEdit}
      />

      <DeleteConfirmModal
        isOpen={isDeleteModalOpen}
        onClose={() => {
          setIsDeleteModalOpen(false);
          setDeletingLead(null);
        }}
        lead={deletingLead}
        onConfirmDelete={handleConfirmDelete}
      />

      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        userProfile={userProfile}
        onUpdateProfile={setUserProfile}
        onResetSampleData={handleResetSampleData}
        totalLeadsCount={leads.length}
        theme={theme}
        onSetTheme={setTheme}
      />

      <ImportCSVModal
        key={isImportModalOpen ? 'open' : 'closed'}
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onImportSuccess={handleCSVImportSuccess}
      />

      {/* Toast Feedback Notification */}
      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
}
