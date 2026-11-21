/**
 * Date utility functions for LeadFlow CRM
 */

// Format a date object or string into YYYY-MM-DD
export function toISODateString(dateInput) {
  if (!dateInput) return '';
  if (typeof dateInput === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(dateInput.trim())) {
    return dateInput.trim();
  }
  const d = new Date(dateInput);
  if (isNaN(d.getTime())) return '';
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// Get today's date in YYYY-MM-DD using local time
export function getTodayString() {
  return toISODateString(new Date());
}

// Get a date string offset by N days from today
export function getRelativeDate(offsetDays = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return toISODateString(d);
}

// Format date for display (e.g., "Nov 20, 2026")
export function formatDisplayDate(dateInput) {
  if (!dateInput) return '—';
  // Parse YYYY-MM-DD explicitly to prevent UTC timezone shift
  if (typeof dateInput === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(dateInput)) {
    const [year, month, day] = dateInput.split('-').map(Number);
    const dateObj = new Date(year, month - 1, day);
    return dateObj.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }
  const d = new Date(dateInput);
  if (isNaN(d.getTime())) return String(dateInput);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

// Format full header date (e.g., "Thursday, November 20, 2026")
export function formatHeaderDate(dateInput = new Date()) {
  const d = new Date(dateInput);
  return d.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

/**
 * Calculate follow-up status relative to current date
 * Returns: { status: 'overdue' | 'today' | 'upcoming', diffDays: number, label: string }
 */
export function getFollowUpStatus(followUpDate) {
  if (!followUpDate) {
    return { status: 'none', diffDays: 0, label: 'No date set' };
  }

  const todayStr = getTodayString();
  const targetStr = toISODateString(followUpDate);

  // Compare date strings directly YYYY-MM-DD
  if (targetStr < todayStr) {
    // Calculate how many days overdue
    const [tY, tM, tD] = todayStr.split('-').map(Number);
    const [fY, fM, fD] = targetStr.split('-').map(Number);
    const today = new Date(tY, tM - 1, tD);
    const target = new Date(fY, fM - 1, fD);
    const diffTime = today.getTime() - target.getTime();
    const diffDays = Math.max(1, Math.round(diffTime / (1000 * 60 * 60 * 24)));
    return {
      status: 'overdue',
      diffDays,
      label: diffDays === 1 ? '1 day overdue' : `${diffDays} days overdue`
    };
  } else if (targetStr === todayStr) {
    return {
      status: 'today',
      diffDays: 0,
      label: 'Due today'
    };
  } else {
    // Calculate days upcoming
    const [tY, tM, tD] = todayStr.split('-').map(Number);
    const [fY, fM, fD] = targetStr.split('-').map(Number);
    const today = new Date(tY, tM - 1, tD);
    const target = new Date(fY, fM - 1, fD);
    const diffTime = target.getTime() - today.getTime();
    const diffDays = Math.max(1, Math.round(diffTime / (1000 * 60 * 60 * 24)));
    return {
      status: 'upcoming',
      diffDays,
      label: diffDays === 1 ? 'Tomorrow' : `In ${diffDays} days`
    };
  }
}

