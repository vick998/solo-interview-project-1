import { ChevronDown } from "lucide-react";

export function DocumentSidebar({
  models,
  selectedModel,
  onModelChange,
  documents = [],
  expandedDocId,
  onSelectDoc,
  onToggleExpand,
}) {
  return (
    <aside className="sidebar-right">
      <h3>Containing</h3>
      <div>
        <label>Model</label>
        <select value={selectedModel} onChange={(e) => onModelChange(e.target.value)}>
          {models.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label>Documents</label>
        <div className="doc-cards">
          {documents.map((d) => (
            <div
              key={d.id}
              className={`doc-card ${d.enabled ? "selected" : ""} ${expandedDocId === d.id ? "expanded" : ""}`}
              onClick={(e) => {
                if (!e.target.closest(".doc-card-dropdown")) onSelectDoc(d.id);
              }}
            >
              <div className="doc-card-header">
                <input
                  type="checkbox"
                  className="doc-card-checkbox"
                  checked={d.enabled}
                  onChange={() => onSelectDoc(d.id)}
                  onClick={(e) => e.stopPropagation()}
                />
                <span className="doc-card-name" title={d.display_name}>
                  {d.display_name}
                </span>
                <button
                  type="button"
                  className="doc-card-dropdown"
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleExpand(d.id);
                  }}
                  aria-label={expandedDocId === d.id ? "Collapse" : "Expand"}
                >
                  <ChevronDown size={16} />
                </button>
              </div>
              {expandedDocId === d.id && (
                <div className="doc-card-ner">NER characteristics (coming soon)</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
