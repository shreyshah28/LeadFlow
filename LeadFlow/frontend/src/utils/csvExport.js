/**
 * CSV Export utility for LeadFlow
 */
import { formatDisplayDate } from './dateUtils';

export function exportLeadsToCSV(leads, filename = 'LeadFlow_Leads') {
  if (!leads || leads.length === 0) {
    console.warn('exportLeadsToCSV: No leads available to export.');
    return false;
  }

  // Headers defined clearly
  const headers = [
    'ID',
    'Company Name',
    'Contact Person',
    'Email',
    'Phone',
    'City',
    'Status',
    'Follow-up Date (ISO)',
    'Follow-up Date (Formatted)',
    'Deal Value ($)',
    'Notes'
  ];

  // Helper to escape CSV cell contents
  const escapeCell = (val) => {
    if (val === null || val === undefined) return '""';
    const str = String(val).replace(/"/g, '""');
    return `"${str}"`;
  };

  // Build CSV rows
  const rows = leads.map((lead, idx) => [
    escapeCell(lead.id || idx + 1),
    escapeCell(lead.companyName),
    escapeCell(lead.contactPerson),
    escapeCell(lead.email),
    escapeCell(lead.phone),
    escapeCell(lead.city),
    escapeCell(lead.status),
    escapeCell(lead.followUpDate),
    escapeCell(formatDisplayDate(lead.followUpDate)),
    escapeCell(lead.dealValue ? `$${Number(lead.dealValue).toLocaleString()}` : '$0'),
    escapeCell(lead.notes || '')
  ]);

  const csvContent = [
    headers.map((h) => `"${h}"`).join(','),
    ...rows.map((row) => row.join(','))
  ].join('\r\n');

  // Prefix with UTF-8 BOM so Microsoft Excel handles special characters correctly
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  
  const today = new Date().toISOString().split('T')[0];
  link.setAttribute('href', url);
  link.setAttribute('download', `${filename}_${today}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  return true;
}

