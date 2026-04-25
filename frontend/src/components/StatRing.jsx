export default function StatRing({ value = 0, max = 100, label, unit, color = "#0a84ff" }) {
  const safeMax = max > 0 ? max : 1;
  const percent = Math.max(0, Math.min(100, Math.round((value / safeMax) * 100)));
  const degrees = Math.round((percent / 100) * 360);

  return (
    <div className="stat-ring" style={{ "--ring-color": color, "--ring-deg": `${degrees}deg` }}>
      <div className="stat-ring__dial">
        <div>
          <strong>{value}</strong>
          {unit ? <span>{unit}</span> : null}
        </div>
      </div>
      <p>{label}</p>
    </div>
  );
}
