import { useState, useRef } from "react";
import { X } from "lucide-react";
import { api, apiUpload } from "./api.js";

export function UploadModal({ isOpen, onClose, chatId, onUploadSuccess }) {
  const [urlInput, setUrlInput] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [feedbackType, setFeedbackType] = useState(null);
  const fileInputRef = useRef(null);

  const clearFeedback = () => {
    setFeedback(null);
    setFeedbackType(null);
  };

  const showSuccess = (msg) => {
    setFeedback(msg);
    setFeedbackType("success");
  };

  const showError = (msg) => {
    setFeedback(msg);
    setFeedbackType("error");
  };

  const handleFileUpload = async (e) => {
    if (!chatId) return;
    const files = e.target.files;
    if (!files?.length) return;
    try {
      await apiUpload(chatId, Array.from(files));
      showSuccess("Upload successful");
      onUploadSuccess?.();
    } catch (err) {
      showError(err.message || "Upload failed");
    }
    e.target.value = "";
  };

  const handleAddUrl = async () => {
    if (!chatId || !urlInput.trim()) return;
    try {
      await api(`/chats/${chatId}/add-urls`, {
        method: "POST",
        body: JSON.stringify({ urls: [urlInput.trim()] }),
      });
      setUrlInput("");
      showSuccess("URL added successfully");
      onUploadSuccess?.();
    } catch (err) {
      showError(err.message || "Failed to add URL");
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      className="upload-modal-overlay"
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-label="Upload documents"
    >
      <div className="upload-modal">
        <div className="upload-modal-header">
          <h3>Upload documents</h3>
          <button
            type="button"
            className="upload-modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>
        <div className="upload-modal-body">
          <div className="upload-modal-section">
            <label>File upload</label>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleFileUpload}
              className="upload-modal-file-input"
            />
            <button
              type="button"
              className="upload-modal-browse"
              onClick={() => fileInputRef.current?.click()}
            >
              Browse files
            </button>
          </div>
          <div className="upload-modal-section">
            <label>Add URL</label>
            <div className="upload-modal-url-row">
              <input
                type="text"
                placeholder="https://..."
                value={urlInput}
                onChange={(e) => {
                  setUrlInput(e.target.value);
                  clearFeedback();
                }}
                onKeyDown={(e) => e.key === "Enter" && handleAddUrl()}
                className="upload-modal-url-input"
              />
              <button type="button" className="upload-modal-add-url" onClick={handleAddUrl}>
                Add URL
              </button>
            </div>
          </div>
          {feedback && (
            <div className={`upload-modal-feedback upload-modal-feedback--${feedbackType}`}>
              {feedback}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
