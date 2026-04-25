import StatRing from "../components/StatRing.jsx";

function initials(profile) {
  return (profile?.first_name || "H").slice(0, 1).toUpperCase();
}

export default function ProfileScreen({ profile }) {
  const records = profile?.personal_records || [];

  return (
    <section className="screen stack">
      <div className="profile-hero">
        <div className="avatar">
          {profile?.photo_url ? <img src={profile.photo_url} alt="" /> : <span>{initials(profile)}</span>}
        </div>
        <div>
          <p className="eyebrow">@{profile?.username || "telegram"}</p>
          <h2>{profile?.first_name || "HealthQuest"}</h2>
          <span>{profile?.xp_total || 0} XP всего</span>
        </div>
      </div>

      <div className="surface">
        <div className="section-head">
          <h2>Уровень {profile?.level || 1}</h2>
          <span>{profile?.xp_progress || 0}/{profile?.xp_to_next || 100} XP</span>
        </div>
        <StatRing value={profile?.xp_progress || 0} max={profile?.xp_to_next || 100} label="До следующего" color="#30d158" />
      </div>

      <section className="surface">
        <div className="section-head">
          <h2>Личные рекорды</h2>
          <span>{records.length}</span>
        </div>
        {records.length === 0 ? <p className="empty">Рекорды появятся после первых подходов.</p> : null}
        <div className="record-grid">
          {records.map((record) => (
            <div className="record-card" key={record.id}>
              <span>{record.exercise_name}</span>
              <strong>{record.max_weight_kg} кг</strong>
              <p>{record.max_reps} повторений</p>
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}
