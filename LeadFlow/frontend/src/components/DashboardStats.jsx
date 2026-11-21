import React from 'react';
import {
  Users,
  PhoneCall,
  Calendar,
  CheckCircle2
} from 'lucide-react';

export default function DashboardStats({
  leads = [],
  activeStatusFilter,
  onSelectStatusFilter
}) {
  // Dynamic counts calculated from leads
  const totalLeads = leads.length;
  const contactedCount = leads.filter((l) => l.status === 'Contacted').length;
  const meetingsCount = leads.filter((l) => l.status === 'Meeting').length;
  const wonCount = leads.filter((l) => l.status === 'Won').length;
  const newCount = leads.filter((l) => l.status === 'New').length;

  const winRate = totalLeads > 0 ? Math.round((wonCount / totalLeads) * 100) : 0;
  const contactRate = totalLeads > 0 ? Math.round(((totalLeads - newCount) / totalLeads) * 100) : 0;

  // Total deal value
  const totalPipelineValue = leads
    .filter((l) => l.status !== 'Lost')
    .reduce((acc, curr) => acc + (Number(curr.dealValue) || 0), 0);

  const cards = [
    {
      id: 'total',
      filterValue: 'ALL',
      title: 'Total Leads',
      count: totalLeads,
      description: 'Active opportunities tracked in pipeline',
      icon: Users,
      colorClass: 'stat-indigo',
      badge: `${newCount} uncontacted`,
      highlight: true
    },
    {
      id: 'contacted',
      filterValue: 'Contacted',
      title: 'Contacted',
      count: contactedCount,
      description: 'Initial outreach & qualification completed',
      icon: PhoneCall,
      colorClass: 'stat-amber',
      badge: `${contactRate}% outreach rate`
    },
    {
      id: 'meetings',
      filterValue: 'Meeting',
      title: 'Meetings',
      count: meetingsCount,
      description: 'Product demos & proposal reviews scheduled',
      icon: Calendar,
      colorClass: 'stat-purple',
      badge: 'High intent'
    },
    {
      id: 'won',
      filterValue: 'Won',
      title: 'Won Leads',
      count: wonCount,
      description: 'Successfully converted paying clients',
      icon: CheckCircle2,
      colorClass: 'stat-emerald',
      badge: `${winRate}% win rate`
    }
  ];

  return (
    <section className="dashboard-stats-section" aria-label="Dashboard Overview">
      <div className="stats-grid">
        {cards.map((card) => {
          const Icon = card.icon;
          const isSelected = activeStatusFilter === card.filterValue;

          return (
            <div
              key={card.id}
              className={`stat-card ${card.colorClass} ${
                isSelected ? 'stat-card-selected' : ''
              }`}
              onClick={() => onSelectStatusFilter(card.filterValue)}
              role="button"
              tabIndex={0}
              title={`Click to filter table by ${card.title}`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onSelectStatusFilter(card.filterValue);
                }
              }}
            >
              <div className="stat-card-header">
                <div className="stat-icon-wrapper">
                  <Icon size={22} className="stat-icon" />
                </div>
                <span className="stat-badge">{card.badge}</span>
              </div>

              <div className="stat-card-body">
                <span className="stat-title">{card.title}</span>
                <div className="stat-count-row">
                  <span className="stat-count">{card.count}</span>
                  {card.id === 'total' && (
                    <span className="stat-submetric">
                      ${(totalPipelineValue / 1000).toFixed(0)}k pipeline
                    </span>
                  )}
                </div>
                <p className="stat-description">{card.description}</p>
              </div>

              <div className="stat-card-footer">
                <span className="stat-filter-hint">
                  {isSelected ? '✓ Filtering by this status' : 'Click to filter'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
