import { ChevronDown } from "lucide-react";

const ENTITY_LABELS = {
  PER: "People",
  ORG: "Orgs",
  LOC: "Locations",
  MISC: "Other",
};
const ENTITY_CAP = 5;

function EntityOverview({ entities }) {
  if (entities == null || typeof entities !== "object") {
    return (
      <div className="doc-card-ner doc-card-ner-processing">
        <span className="doc-card-ner-spinner" aria-hidden />
        Processing entities…
      </div>
    );
  }
  const entries = Object.entries(entities).filter(([, list]) => Array.isArray(list) && list.length > 0);
  if (entries.length === 0) return <div className="doc-card-ner-empty">No entities extracted</div>;
  return (
    <div className="doc-card-ner">
      {entries.flatMap(([type, list]) => {
        const label = ENTITY_LABELS[type] ?? type;
        const shown = list.slice(0, ENTITY_CAP);
        const rest = list.length - ENTITY_CAP;
        return [
          ...shown.map((entry, i) => (
            <div key={`${type}-${i}`} className="doc-card-ner-row">
              <span className={`doc-card-ner-badge doc-card-ner-badge--${type}`}>{label}</span>
              <span className="doc-card-ner-entry"> – {entry}</span>
            </div>
          )),
          ...(rest > 0
            ? [
                <div key={`${type}-more`} className="doc-card-ner-row doc-card-ner-more">
                  +{rest} more
                </div>,
              ]
            : []),
        ];
      })}
    </div>
  );
}

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
              {expandedDocId === d.id && <EntityOverview entities={d.entities} />}
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
