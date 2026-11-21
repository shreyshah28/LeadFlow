import React from 'react';
import { AlertTriangle, Trash2, X } from 'lucide-react';

export default function DeleteConfirmModal({ isOpen, onClose, lead, onConfirmDelete }) {
  if (!isOpen || !lead) return null;

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div
        className="modal-container modal-sm"
        onClick={(e) => e.stopPropagation()}
        tabIndex={-1}
      >
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-danger-icon">
              <AlertTriangle size={20} />
            </div>
            <h2 className="modal-title">Delete Lead</h2>
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

        <div className="modal-body-p">
          <p>
            Are you sure you want to delete <strong>{lead.companyName}</strong> (Contact:{' '}
            {lead.contactPerson})?
          </p>
          <p className="modal-subtext">
            This action cannot be undone and will remove the lead from your pipeline and follow-up
            reminders.
          </p>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-danger"
            onClick={() => {
              onConfirmDelete(lead.id);
              onClose();
            }}
          >
            <Trash2 size={15} />
            <span>Delete Lead</span>
          </button>
        </div>
      </div>
    </div>
  );
}

