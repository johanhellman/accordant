/**
 * ModelSelector Component
 * 
 * A reusable dropdown component for selecting LLM models.
 * Displays model name and ID, and shows override warnings when applicable.
 * 
 * @param {Object} props - Component props
 * @param {string} props.value - Currently selected model ID
 * @param {Array<{id: string, name: string}>} props.models - List of available models
 * @param {Function} props.onChange - Callback when selection changes (receives event)
 * @param {string} props.label - Label text for the select dropdown
 * @param {string} [props.effectiveModel] - Effective model ID (from env/config override)
 * @param {boolean} [props.showOverrideWarning=true] - Whether to show override warning
 */
function ModelSelector({ value, models, onChange, label, effectiveModel, showOverrideWarning = true }) {
  const isOverridden = showOverrideWarning && effectiveModel && value !== effectiveModel;

  return (
    <div className="form-group model-config">
      <label>{label}</label>
      <select value={value} onChange={onChange}>
        {models.map((m) => (
          <option key={m.id} value={m.id}>
            {m.name} ({m.id})
          </option>
        ))}
      </select>
      {isOverridden && (
        <div className="override-warning">
          ⚠️ Overridden by Env Var. Active: <strong>{effectiveModel}</strong>
        </div>
      )}
    </div>
  );
}

export default ModelSelector;

