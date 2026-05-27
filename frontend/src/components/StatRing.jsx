export default function StatRing({ value = 0, max = 100, label, unit, color = "#0a84ff" }) {
  const safeMax = max > 0 ? max : 1;
  const percent = Math.max(0, Math.min(100, Math.round((value / safeMax) * 100)));
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const progress = (percent / 100) * circumference;

  return (
    <div className="stat-ring" style={{ "--ring-color": color }}>
      <div className="stat-ring__dial">
        <svg viewBox="0 0 100 100" aria-hidden="true">
          <circle className="stat-ring__track" cx="50" cy="50" r={radius} />
          <circle
            className="stat-ring__value"
            cx="50"
            cy="50"
            r={radius}
            strokeDasharray={`${progress} ${circumference}`}
          />
        </svg>
        <div className="stat-ring__center">
          <strong>{value}</strong>
          {unit ? <span>{unit}</span> : null}
        </div>
      </div>
      <p>{label}</p>
    </div>
  );
}
