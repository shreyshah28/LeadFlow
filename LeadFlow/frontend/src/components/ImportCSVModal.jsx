import React, { useState, useRef, useCallback } from 'react';
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertTriangle,
  X,
  Loader2,
  RotateCcw
} from 'lucide-react';
import { api } from '../services/api';

/**
 * Robust CSV parser for client-side preview
 */
function parseCSVPreview(text) {
  if (!text) return null;
  const lines = text
    .split(/\r\n|\n|\r/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0);

  if (lines.length === 0) return null;

  const parseLine = (line) => {
    const result = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"' || char === "'") {
        if (inQuotes && line[i + 1] === char) {
          current += char;
          i++;
        } else {
          inQuotes = !inQuotes;
        }
      } else if (char === ',' && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    result.push(current.trim());
    return result;
  };

  const headers = parseLine(lines[0]);
  const previewRows = lines.slice(1, 4).map(parseLine);

  // Check required column mappings
  const lowerHeaders = headers.map((h) => h.toLowerCase());
  const hasCompany = lowerHeaders.some((h) => h.includes('company') || h.includes('org'));
  const hasContact = lowerHeaders.some(
    (h) => h.includes('contact') || h.includes('person') || (h.includes('name') && !h.includes('company'))
  );
  const hasEmail = lowerHeaders.some((h) => h.includes('email') || h.includes('mail'));

  const missingCols = [];
  if (!hasCompany) missingCols.push('Company Name');
  if (!hasContact) missingCols.push('Contact Person');
  if (!hasEmail) missingCols.push('Email');

  return {
    headers,
    previewRows,
    totalRowsEstimate: Math.max(0, lines.length - 1),
    hasRequiredCols: missingCols.length === 0,
    missingCols
  };
}

export default function ImportCSVModal({ isOpen, onClose, onImportSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  // Full reset function that clears all state and DOM file input value
  const resetAll = useCallback(() => {
    setSelectedFile(null);
    setPreviewData(null);
    setIsUploading(false);
    setResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  // Safe close handler that restores initial state
  const handleClose = useCallback(() => {
    if (isUploading) return;
    resetAll();
    if (onClose) onClose();
  }, [isUploading, resetAll, onClose]);

  const processFile = (file) => {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Please select a valid CSV file (.csv)');
      setSelectedFile(null);
      setPreviewData(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setSelectedFile(file);
    setError(null);
    setResult(null);

    // Read first chunk for instant preview
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = parseCSVPreview(event.target.result);
        setPreviewData(parsed);
        if (parsed && !parsed.hasRequiredCols) {
          setError(
            `Notice: File appears to be missing recommended columns: ${parsed.missingCols.join(', ')}`
          );
        } else {
          setError(null);
        }
      } catch {
        setPreviewData(null);
      }
    };
    reader.onerror = () => {
      setError('Could not read the CSV file for preview.');
      setPreviewData(null);
    };
    // Read up to 32KB which is plenty for previewing headers and top rows
    reader.readAsText(file.slice(0, 32768));
  };

  const handleFileChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (isUploading) return;
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file) {
      processFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || isUploading) return;

    setIsUploading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.uploadCSV(selectedFile);
      setResult(data);
      if (onImportSuccess) {
        onImportSuccess(data);
      }
    } catch (err) {
      setError(err.message || 'Failed to upload and import CSV.');
    } finally {
      setIsUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={handleClose} role="dialog" aria-modal="true">
      <div
        className="modal-container modal-md"
        onClick={(e) => e.stopPropagation()}
        tabIndex={-1}
      >
        <div className="modal-header">
          <div className="modal-title-group">
            <h2 className="modal-title">Import Leads from CSV</h2>
            <p className="modal-subtitle">
              Upload a spreadsheet to import records into the SQLite database
            </p>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={handleClose}
            aria-label="Close modal"
            disabled={isUploading}
          >
            <X size={18} />
          </button>
        </div>

        <div className="modal-body-p">
          {!result ? (
            <>
              {/* Dropzone */}
              <div
                className={`csv-dropzone ${selectedFile ? 'has-file' : ''}`}
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => {
                  if (!isUploading) {
                    fileInputRef.current?.click();
                  }
                }}
              >
                {/* File Input: resetting value in onClick ensures re-selecting same file fires onChange */}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  style={{ display: 'none' }}
                  onClick={(e) => {
                    e.target.value = '';
                  }}
                  onChange={handleFileChange}
                />
                <div className="dropzone-content">
                  <div className="dropzone-icon-box">
                    {selectedFile ? <FileText size={28} /> : <Upload size={28} />}
                  </div>
                  {selectedFile ? (
                    <div className="dropzone-file-info">
                      <span className="file-name">{selectedFile.name}</span>
                      <span className="file-size">
                        {(selectedFile.size / 1024).toFixed(1)} KB
                        {previewData?.totalRowsEstimate !== undefined &&
                          ` • ~${previewData.totalRowsEstimate} rows detected`}
                      </span>
                    </div>
                  ) : (
                    <div className="dropzone-prompts">
                      <p className="dropzone-main-text">
                        <strong>Click to browse</strong> or drag & drop a CSV file here
                      </p>
                      <p className="dropzone-sub-text">
                        Supports LeadFlow export format or standard CRM CSVs
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* CSV Preview Table when a valid file is parsed */}
              {previewData && previewData.headers && previewData.headers.length > 0 && (
                <div className="csv-preview-box">
                  <div className="csv-preview-header">
                    <span>
                      Detected Columns: {previewData.headers.length} | First{' '}
                      {previewData.previewRows.length} Rows Preview
                    </span>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      style={{ padding: '2px 8px', fontSize: '0.72rem' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        resetAll();
                      }}
                    >
                      Clear File
                    </button>
                  </div>
                  <div className="csv-preview-table-wrapper">
                    <table className="csv-preview-table">
                      <thead>
                        <tr>
                          {previewData.headers.map((h, i) => (
                            <th key={i}>{h || `Col ${i + 1}`}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {previewData.previewRows.map((row, rIdx) => (
                          <tr key={rIdx}>
                            {previewData.headers.map((_, cIdx) => (
                              <td key={cIdx}>{row[cIdx] || '—'}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Supported Columns Guide */}
              <div className="csv-guide-box">
                <span className="guide-title">Required Columns:</span>
                <span className="guide-tags">
                  <code>Company Name</code>, <code>Contact Person</code>, <code>Email</code>
                </span>
                <span className="guide-title" style={{ marginTop: '6px' }}>
                  Optional Columns:
                </span>
                <span className="guide-tags">
                  <code>Phone</code>, <code>City</code>, <code>Status</code>, <code>Follow-up Date</code>,{' '}
                  <code>Deal Value</code>, <code>Notes</code>
                </span>
              </div>

              {/* Error message */}
              {error && (
                <div className="alert-box alert-error">
                  <AlertTriangle size={16} />
                  <span>{error}</span>
                </div>
              )}
            </>
          ) : (
            /* Result Summary View */
            <div className="import-result-view">
              <div className="result-icon-box success">
                <CheckCircle2 size={32} />
              </div>
              <h3 className="result-title">Import Finished!</h3>
              <p className="result-message">{result.message}</p>

              <div className="result-stats-row">
                <div className="result-stat-card">
                  <span className="stat-label">Imported</span>
                  <span className="stat-val text-success">{result.imported_count}</span>
                </div>
                <div className="result-stat-card">
                  <span className="stat-label">Skipped</span>
                  <span className="stat-val text-warning">{result.skipped_count}</span>
                </div>
                <div className="result-stat-card">
                  <span className="stat-label">Total Rows</span>
                  <span className="stat-val">{result.total_rows}</span>
                </div>
              </div>

              {/* Skipped row errors if any */}
              {result.errors && result.errors.length > 0 && (
                <div className="skipped-errors-box">
                  <span className="skipped-title">Skipped Rows Details:</span>
                  <ul className="skipped-list">
                    {result.errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="modal-footer">
          {!result ? (
            <>
              {selectedFile && (
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={resetAll}
                  disabled={isUploading}
                >
                  <RotateCcw size={14} />
                  <span>Change File</span>
                </button>
              )}
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleClose}
                disabled={isUploading}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
              >
                {isUploading ? (
                  <>
                    <Loader2 size={16} className="spin-icon" />
                    <span>Importing...</span>
                  </>
                ) : (
                  <>
                    <Upload size={16} />
                    <span>Import Leads</span>
                  </>
                )}
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={resetAll}
              >
                <RotateCcw size={14} />
                <span>Import Another File</span>
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleClose}
              >
                Done
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
