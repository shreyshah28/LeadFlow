/**
 * Realistic initial sample leads for LeadFlow CRM
 * Uses dynamic dates relative to current date so overdue, today, and upcoming follow-ups are always active!
 */
import { getRelativeDate } from '../utils/dateUtils';

export const INITIAL_LEADS = [
  {
    id: 'lead-001',
    companyName: 'Apex Logistics Corp',
    contactPerson: 'David Miller',
    email: 'david.miller@apexlogistics.com',
    phone: '+1 (555) 234-8901',
    city: 'Chicago',
    status: 'Contacted',
    followUpDate: getRelativeDate(-2), // 2 days overdue
    dealValue: 24500,
    notes: 'Interested in enterprise fleet routing add-on. Sent pricing deck.'
  },
  {
    id: 'lead-002',
    companyName: 'NovaTech Solutions',
    contactPerson: 'Sarah Jenkins',
    email: 'sjenkins@novatech.io',
    phone: '+1 (555) 345-6789',
    city: 'San Francisco',
    status: 'Meeting',
    followUpDate: getRelativeDate(0), // Due Today
    dealValue: 48000,
    notes: 'Technical architecture review call scheduled for 2:30 PM.'
  },
  {
    id: 'lead-003',
    companyName: 'Horizon Retail Partners',
    contactPerson: 'Marcus Vance',
    email: 'marcus@horizonretail.com',
    phone: '+1 (555) 456-7890',
    city: 'New York',
    status: 'New',
    followUpDate: getRelativeDate(-3), // 3 days overdue
    dealValue: 18000,
    notes: 'Inbound lead from product webinar. Needs discovery call.'
  },
  {
    id: 'lead-004',
    companyName: 'BluePeak Analytics',
    contactPerson: 'Elena Rostova',
    email: 'elena.r@bluepeakanalytics.com',
    phone: '+1 (555) 567-8901',
    city: 'Seattle',
    status: 'Won',
    followUpDate: getRelativeDate(-5),
    dealValue: 65000,
    notes: 'Signed 1-year annual contract. Handed over to Customer Success.'
  },
  {
    id: 'lead-005',
    companyName: 'CloudScale AI Labs',
    contactPerson: 'Julian Chen',
    email: 'jchen@cloudscale.ai',
    phone: '+1 (555) 678-9012',
    city: 'Austin',
    status: 'Meeting',
    followUpDate: getRelativeDate(0), // Due Today
    dealValue: 52000,
    notes: 'Budget approved by VP of Engineering. Contract negotiation stage.'
  },
  {
    id: 'lead-006',
    companyName: 'GreenPulse Energy',
    contactPerson: 'Rachel Adams',
    email: 'rachel@greenpulseenergy.com',
    phone: '+1 (555) 789-0123',
    city: 'Denver',
    status: 'Contacted',
    followUpDate: getRelativeDate(1), // Tomorrow
    dealValue: 31000,
    notes: 'Follow up on security compliance questionnaire response.'
  },
  {
    id: 'lead-007',
    companyName: 'SwiftPay Networks',
    contactPerson: 'Karan Patel',
    email: 'karan@swiftpay.org',
    phone: '+1 (555) 890-1234',
    city: 'Atlanta',
    status: 'Won',
    followUpDate: getRelativeDate(-8),
    dealValue: 84000,
    notes: 'Payment gateway integration pilot succeeded. Enterprise license active.'
  },
  {
    id: 'lead-008',
    companyName: 'Lumina Health Systems',
    contactPerson: 'Dr. Rebecca Thorne',
    email: 'rthorne@luminahealth.org',
    phone: '+1 (555) 901-2345',
    city: 'Boston',
    status: 'New',
    followUpDate: getRelativeDate(2), // In 2 days
    dealValue: 39500,
    notes: 'HIPAA certification confirmed. Scheduled initial phone call.'
  },
  {
    id: 'lead-009',
    companyName: 'MetroSupply Distribution',
    contactPerson: 'Carlos Delgado',
    email: 'carlos@metrosupply.com',
    phone: '+1 (555) 012-3456',
    city: 'Dallas',
    status: 'Lost',
    followUpDate: getRelativeDate(-12),
    dealValue: 15000,
    notes: 'Decided to renew with legacy vendor due to fiscal budget constraints.'
  },
  {
    id: 'lead-010',
    companyName: 'Vanguard CyberSec',
    contactPerson: 'Priya Sharma',
    email: 'psharma@vanguardcyber.net',
    phone: '+1 (555) 123-4567',
    city: 'San Francisco',
    status: 'Contacted',
    followUpDate: getRelativeDate(3), // In 3 days
    dealValue: 42000,
    notes: 'Expressed strong interest in API rate limiting and webhook security.'
  },
  {
    id: 'lead-011',
    companyName: 'Beacon Commerce Group',
    contactPerson: 'Arthur Pendelton',
    email: 'arthur@beaconcommerce.co',
    phone: '+1 (555) 234-5678',
    city: 'Miami',
    status: 'Meeting',
    followUpDate: getRelativeDate(5), // In 5 days
    dealValue: 37000,
    notes: 'Demonstrating automated lead scoring feature to regional team.'
  },
  {
    id: 'lead-012',
    companyName: 'Nexus FinTech Labs',
    contactPerson: 'Sophia Williams',
    email: 'sophia.williams@nexusfintech.io',
    phone: '+1 (555) 345-7890',
    city: 'New York',
    status: 'Won',
    followUpDate: getRelativeDate(-1),
    dealValue: 72000,
    notes: 'Multi-year contract finalized. Onboarding starts next Monday.'
  }
];

