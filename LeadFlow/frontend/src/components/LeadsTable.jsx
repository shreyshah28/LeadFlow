import React, { useState, useMemo } from 'react';
import {
  Search,
  Filter,
  ArrowUpDown,
  Mail,
  Phone,
  MapPin,
  AlertCircle,
  Clock,
  Edit3,
  Trash2,
  RotateCcw,
  Plus,
  Download,
  Upload,
  ChevronDown
} from 'lucide-react';
import { getFollowUpStatus, formatDisplayDate } from '../utils/dateUtils';

const STATUS_OPTIONS = ['New', 'Contacted', 'Meeting', 'Won', 'Lost'];

const toCanonicalCity = (str) => {
  if (!str) return '';
  return str
    .trim()
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
};

export default function LeadsTable({
  leads = [],
  onUpdateStatus,
  onOpenAddModal,
  onOpenEditModal,
  onOpenImportModal,
  onDeleteLead,
  onExportCSV,
  statusFilter,
  setStatusFilter,
  searchQuery,
  setSearchQuery
}) {
  const [cityFilter, setCityFilter] = useState('ALL');
  const [urgencyFilter, setUrgencyFilter] = useState('ALL'); // 'ALL', 'OVERDUE', 'TODAY', 'UPCOMING'
  const [sortField, setSortField] = useState('followUpDate'); // 'followUpDate', 'companyName', 'contactPerson', 'status'
  const [sortOrder, setSortOrder] = useState('asc'); // 'asc', 'desc'

  // Extract unique normalized cities for city filter dropdown (deduplicating case variations)
  const uniqueCities = useMemo(() => {
    const cityMap = new Map();
    leads.forEach((l) => {
      if (l.city && l.city.trim()) {
        const trimmed = l.city.trim();
        const lower = trimmed.toLowerCase();
        if (!cityMap.has(lower)) {
          cityMap.set(lower, toCanonicalCity(trimmed));
        }
      }
    });
    return Array.from(cityMap.values()).sort((a, b) => a.localeCompare(b));
  }, [leads]);

  // Counts for status tabs
  const statusCounts = useMemo(() => {
    const counts = { ALL: leads.length, New: 0, Contacted: 0, Meeting: 0, Won: 0, Lost: 0 };
    leads.forEach((l) => {
      if (counts[l.status] !== undefined) counts[l.status]++;
    });
    return counts;
  }, [leads]);

  // Handle sort toggle
  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  // Filtered and sorted leads
  const filteredLeads = useMemo(() => {
    return leads
      .filter((lead) => {
        // Status filter
        if (statusFilter !== 'ALL' && lead.status !== statusFilter) {
          return false;
        }

        // City filter (case-insensitive)
        if (cityFilter !== 'ALL') {
          const leadCity = (lead.city || '').trim().toLowerCase();
          const targetCity = cityFilter.trim().toLowerCase();
          if (leadCity !== targetCity) {
            return false;
          }
        }

        // Urgency filter
        if (urgencyFilter !== 'ALL') {
          const followUp = getFollowUpStatus(lead.followUpDate);
          if (urgencyFilter === 'OVERDUE' && followUp.status !== 'overdue') return false;
          if (urgencyFilter === 'TODAY' && followUp.status !== 'today') return false;
          if (urgencyFilter === 'UPCOMING' && followUp.status !== 'upcoming') return false;
        }

        // Search query across Company, Contact Person, and City
        if (searchQuery.trim() !== '') {
          const query = searchQuery.toLowerCase().trim();
          const matchCompany = lead.companyName?.toLowerCase().includes(query);
          const matchContact = lead.contactPerson?.toLowerCase().includes(query);
          const matchCity = lead.city?.toLowerCase().includes(query);
          const matchEmail = lead.email?.toLowerCase().includes(query);
          if (!matchCompany && !matchContact && !matchCity && !matchEmail) {
            return false;
          }
        }

        return true;
      })
      .sort((a, b) => {
        let valA = a[sortField] || '';
        let valB = b[sortField] || '';

        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();

        if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
        if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
  }, [leads, statusFilter, cityFilter, urgencyFilter, searchQuery, sortField, sortOrder]);

  const hasActiveFilters =
    statusFilter !== 'ALL' ||
    cityFilter !== 'ALL' ||
    urgencyFilter !== 'ALL' ||
    searchQuery.trim() !== '';

  const handleResetFilters = () => {
    setStatusFilter('ALL');
    setCityFilter('ALL');
    setUrgencyFilter('ALL');
    setSearchQuery('');
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'New':
        return 'badge-status-new';
      case 'Contacted':
        return 'badge-status-contacted';
      case 'Meeting':
        return 'badge-status-meeting';
      case 'Won':
        return 'badge-status-won';
      case 'Lost':
        return 'badge-status-lost';
      default:
        return 'badge-status-default';
    }
  };

  return (
    <div className="leads-table-container card">
      {/* Table Controls Header */}
      <div className="table-controls-bar">
        {/* Top: Status Tabs */}
        <div className="status-tabs-row">
          <div className="status-tabs" role="tablist">
            <button
              type="button"
              className={`status-tab ${statusFilter === 'ALL' ? 'active' : ''}`}
              onClick={() => setStatusFilter('ALL')}
            >
              All Leads <span className="tab-count">{statusCounts.ALL}</span>
            </button>
            {STATUS_OPTIONS.map((st) => (
              <button
                key={st}
                type="button"
                className={`status-tab ${statusFilter === st ? 'active' : ''} tab-${st.toLowerCase()}`}
                onClick={() => setStatusFilter(st)}
              >
                {st} <span className="tab-count">{statusCounts[st]}</span>
              </button>
            ))}
          </div>

          <div className="table-quick-actions">
            {onOpenImportModal && (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={onOpenImportModal}
                title="Import leads from CSV file"
              >
                <Upload size={14} />
                <span>Import CSV</span>
              </button>
            )}
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => onExportCSV(filteredLeads)}
              title="Download currently filtered leads as CSV"
            >
              <Download size={14} />
              <span>Export CSV</span>
            </button>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={onOpenAddModal}
            >
              <Plus size={14} />
              <span>Add Lead</span>
            </button>
          </div>
        </div>

        {/* Bottom Filter Controls: Search & Filters */}
        <div className="search-filters-row">
          {/* Search Box: Company, Contact, City */}
          <div className="search-input-wrapper">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search by company, contact person, or city..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                type="button"
                className="clear-search-btn"
                onClick={() => setSearchQuery('')}
                title="Clear search"
              >
                ×
              </button>
            )}
          </div>

          {/* Filter Dropdowns */}
          <div className="filters-group">
            {/* Urgency Filter */}
            <div className="filter-select-wrapper">
              <label htmlFor="urgency-filter" className="filter-label">
                Follow-up:
              </label>
              <select
                id="urgency-filter"
                className="filter-select"
                value={urgencyFilter}
                onChange={(e) => setUrgencyFilter(e.target.value)}
              >
                <option value="ALL">All Dates</option>
                <option value="OVERDUE">Overdue Only</option>
                <option value="TODAY">Due Today</option>
                <option value="UPCOMING">Upcoming</option>
              </select>
            </div>

            {/* City Filter */}
            <div className="filter-select-wrapper">
              <label htmlFor="city-filter" className="filter-label">
                City:
              </label>
              <select
                id="city-filter"
                className="filter-select"
                value={cityFilter}
                onChange={(e) => setCityFilter(e.target.value)}
              >
                <option value="ALL">All Cities</option>
                {uniqueCities.map((city) => (
                  <option key={city} value={city}>
                    {city}
                  </option>
                ))}
              </select>
            </div>

            {/* Reset Filters button */}
            {hasActiveFilters && (
              <button
                type="button"
                className="btn-reset-filters"
                onClick={handleResetFilters}
                title="Reset all search filters"
              >
                <RotateCcw size={13} />
                <span>Reset</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Table Results Count Bar */}
      <div className="table-meta-bar">
        <span className="results-count">
          Showing <strong>{filteredLeads.length}</strong> of <strong>{leads.length}</strong> leads
        </span>
        {hasActiveFilters && (
          <span className="filtered-hint">
            (Filtered view active)
          </span>
        )}
      </div>

      {/* Responsive Table Element */}
      <div className="table-responsive">
        <table className="leads-table">
          <thead>
            <tr>
              <th
                className="sortable-th col-company"
                onClick={() => handleSort('companyName')}
                title="Sort by Company"
              >
                <div className="th-content">
                  <span>Company Name</span>
                  <ArrowUpDown size={13} className="sort-icon" />
                </div>
              </th>
              <th
                className="sortable-th col-contact"
                onClick={() => handleSort('contactPerson')}
                title="Sort by Contact Person"
              >
                <div className="th-content">
                  <span>Contact Person</span>
                  <ArrowUpDown size={13} className="sort-icon" />
                </div>
              </th>
              <th className="col-email">Email</th>
              <th className="col-phone">Phone</th>
              <th
                className="sortable-th col-city"
                onClick={() => handleSort('city')}
                title="Sort by City"
              >
                <div className="th-content">
                  <span>City</span>
                  <ArrowUpDown size={13} className="sort-icon" />
                </div>
              </th>
              <th
                className="sortable-th col-status"
                onClick={() => handleSort('status')}
                title="Sort by Status"
              >
                <div className="th-content">
                  <span>Status</span>
                  <ArrowUpDown size={13} className="sort-icon" />
                </div>
              </th>
              <th
                className="sortable-th col-date"
                onClick={() => handleSort('followUpDate')}
                title="Sort by Follow-up Date"
              >
                <div className="th-content">
                  <span>Follow-up Date</span>
                  <ArrowUpDown size={13} className="sort-icon" />
                </div>
              </th>
              <th className="col-actions text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredLeads.length === 0 ? (
              <tr>
                <td colSpan={8} className="empty-table-cell">
                  <div className="empty-table-view">
                    <Filter size={32} className="empty-icon" />
                    <p className="empty-table-title">No leads found</p>
                    <p className="empty-table-subtitle">
                      No prospects match your current search and filter criteria.
                    </p>
                    {hasActiveFilters && (
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={handleResetFilters}
                      >
                        Clear All Filters
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ) : (
              filteredLeads.map((lead) => {
                const followUp = getFollowUpStatus(lead.followUpDate);
                const isOverdue = followUp.status === 'overdue';
                const isToday = followUp.status === 'today';

                return (
                  <tr key={lead.id} className="lead-row">
                    {/* Company Name */}
                    <td className="col-company">
                      <div className="company-cell">
                        <div className="company-avatar">
                          {lead.companyName?.charAt(0).toUpperCase() || 'C'}
                        </div>
                        <div className="company-info">
                          <span className="company-name-text" title={lead.companyName}>
                            {lead.companyName}
                          </span>
                          {lead.notes && (
                            <span className="lead-notes-preview" title={lead.notes}>
                              {lead.notes}
                            </span>
                          )}
                        </div>
                      </div>
                    </td>

                    {/* Contact Person */}
                    <td className="col-contact">
                      <span className="contact-person-text">{lead.contactPerson}</span>
                    </td>

                    {/* Email */}
                    <td className="col-email">
                      {lead.email ? (
                        <a
                          href={`mailto:${lead.email}`}
                          className="table-link email-link"
                          title={`Send email to ${lead.email}`}
                        >
                          <Mail size={13} className="inline-icon" />
                          <span>{lead.email}</span>
                        </a>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>

                    {/* Phone */}
                    <td className="col-phone">
                      {lead.phone ? (
                        <a
                          href={`tel:${lead.phone}`}
                          className="table-link phone-link"
                          title={`Call ${lead.phone}`}
                        >
                          <Phone size={13} className="inline-icon" />
                          <span>{lead.phone}</span>
                        </a>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>

                    {/* City */}
                    <td className="col-city">
                      <div className="city-cell">
                        <MapPin size={13} className="city-icon" />
                        <span>{lead.city || '—'}</span>
                      </div>
                    </td>

                    {/* Status with Direct Interactive Dropdown */}
                    <td className="col-status">
                      <div className="status-select-container">
                        <select
                          className={`status-select ${getStatusBadgeClass(lead.status)}`}
                          value={lead.status}
                          onChange={(e) => onUpdateStatus(lead.id, e.target.value)}
                          title="Change status directly from table"
                          aria-label={`Status for ${lead.companyName}`}
                        >
                          {STATUS_OPTIONS.map((st) => (
                            <option key={st} value={st}>
                              {st}
                            </option>
                          ))}
                        </select>
                        <ChevronDown size={12} className="status-dropdown-icon" />
                      </div>
                    </td>

                    {/* Follow-up Date */}
                    <td className="col-date">
                      <div className="date-cell">
                        <span className="date-text">
                          {formatDisplayDate(lead.followUpDate)}
                        </span>
                        {lead.followUpDate && (
                          <span
                            className={`date-urgency-tag ${
                              isOverdue
                                ? 'tag-overdue'
                                : isToday
                                ? 'tag-today'
                                : 'tag-upcoming'
                            }`}
                          >
                            {isOverdue && <AlertCircle size={10} />}
                            {isToday && <Clock size={10} />}
                            <span>{followUp.label}</span>
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="col-actions text-right">
                      <div className="table-actions-group">
                        <button
                          type="button"
                          className="action-icon-btn edit-btn"
                          onClick={() => onOpenEditModal(lead)}
                          title="Edit Lead"
                          aria-label="Edit Lead"
                        >
                          <Edit3 size={15} />
                        </button>
                        <button
                          type="button"
                          className="action-icon-btn delete-btn"
                          onClick={() => onDeleteLead(lead)}
                          title="Delete Lead"
                          aria-label="Delete Lead"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
