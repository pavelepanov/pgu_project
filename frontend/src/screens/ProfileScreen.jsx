import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api.js";
import StatRing from "../components/StatRing.jsx";

const goals = [
  { id: "lose", label: "Похудение", emoji: "📉" },
  { id: "gain", label: "Набор массы", emoji: "📈" },
  { id: "maintain", label: "Поддержание", emoji: "➡️" },
];

function initials(profile) {
  return (profile?.first_name || "H").slice(0, 1).toUpperCase();
}

export default function ProfileScreen({ profile, onSaved }) {
  const records = profile?.personal_records || [];
  const [heightCm, setHeightCm] = useState(profile?.height_cm ?? "");
  const [weightKg, setWeightKg] = useState(profile?.weight_kg ?? "");
  const [age, setAge] = useState(profile?.age ?? "");
  const [fitnessGoal, setFitnessGoal] = useState(profile?.fitness_goal || "maintain");
  const [proteinTarget, setProteinTarget] = useState(profile?.protein_target ?? "");
  const [fatTarget, setFatTarget] = useState(profile?.fat_target ?? "");
  const [carbsTarget, setCarbsTarget] = useState(profile?.carbs_target ?? "");
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setHeightCm(profile?.height_cm ?? "");
    setWeightKg(profile?.weight_kg ?? "");
    setAge(profile?.age ?? "");
    setFitnessGoal(profile?.fitness_goal || "maintain");
    setProteinTarget(profile?.protein_target ?? "");
    setFatTarget(profile?.fat_target ?? "");
    setCarbsTarget(profile?.carbs_target ?? "");
  }, [profile]);

  function isWholeNumber(value) {
    return /^\d+$/.test(String(value));
  }

  function resetForm() {
    setHeightCm(profile?.height_cm ?? "");
    setWeightKg(profile?.weight_kg ?? "");
    setAge(profile?.age ?? "");
    setFitnessGoal(profile?.fitness_goal || "maintain");
    setProteinTarget(profile?.protein_target ?? "");
    setFatTarget(profile?.fat_target ?? "");
    setCarbsTarget(profile?.carbs_target ?? "");
    setError("");
  }

  function updateWholeNumber(setter, value, label) {
    setter(value);
    if (value && !isWholeNumber(value)) {
      setError(`${label} должен быть целым числом`);
      return;
    }
    setError("");
  }

  const bmi = useMemo(() => {
    if (!heightCm || !weightKg) return null;
    const height = Number(heightCm);
    const weight = Number(weightKg);
    if (!height || !weight) return null;
    return Math.round((weight / ((height / 100) ** 2)) * 10) / 10;
  }, [heightCm, weightKg]);

  function validateProfile() {
    const height = Number(heightCm);
    const weight = Number(weightKg);
    const ageValue = Number(age);
    const protein = Number(proteinTarget);
    const fat = Number(fatTarget);
    const carbs = Number(carbsTarget);

    if (heightCm && !isWholeNumber(heightCm)) {
      return "Рост должен быть целым числом";
    }
    if (weightKg && !isWholeNumber(weightKg)) {
      return "Вес должен быть целым числом";
    }
    if (age && !isWholeNumber(age)) {
      return "Возраст должен быть целым числом";
    }
    if (heightCm && (height < 50 || height > 300)) {
      return "Рост должен быть от 50 до 300 см";
    }
    if (weightKg && (weight < 20 || weight > 500)) {
      return "Вес должен быть от 20 до 500 кг";
    }
    if (age && (ageValue < 10 || ageValue > 120)) {
      return "Возраст должен быть от 10 до 120 лет";
    }
    if (!fitnessGoal || !["lose", "gain", "maintain"].includes(fitnessGoal)) {
      return "Выберите корректную цель";
    }
    if (proteinTarget && (protein < 0 || protein > 1000)) {
      return "Белки должны быть от 0 до 1000 г";
    }
    if (fatTarget && (fat < 0 || fat > 500)) {
      return "Жиры должны быть от 0 до 500 г";
    }
    if (carbsTarget && (carbs < 0 || carbs > 500)) {
      return "Углеводы должны быть от 0 до 500 г";
    }
    return "";
  }

  async function saveProfile() {
    const validationError = validateProfile();
    if (validationError) {
      setError(validationError);
      return;
    }

    setError("");
    setLoading(true);
    try {
      await apiFetch("/api/profile", {
        method: "PATCH",
        body: {
          height_cm: heightCm ? Number(heightCm) : null,
          weight_kg: weightKg ? Number(weightKg) : null,
          age: age ? Number(age) : null,
          fitness_goal: fitnessGoal,
          protein_target: proteinTarget ? Number(proteinTarget) : null,
          fat_target: fatTarget ? Number(fatTarget) : null,
          carbs_target: carbsTarget ? Number(carbsTarget) : null,
        },
      });
      if (onSaved) {
        onSaved("Профиль обновлён");
      }
      setIsEditing(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

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
          <h2>Параметры</h2>
          <span>{bmi ? `BMI ${bmi}` : "Добавьте рост и вес"}</span>
        </div>
        <div className="form-grid">
          <label className="form-field">
            <span>Рост, см</span>
            <input
              type="number"
              min="50"
              max="250"
              step="1"
              value={heightCm ?? ""}
              onChange={(event) => updateWholeNumber(setHeightCm, event.target.value, "Рост")}
              placeholder="170"
              disabled={!isEditing || loading}
            />
          </label>
          <label className="form-field">
            <span>Вес, кг</span>
            <input
              type="number"
              step="1"
              min="20"
              max="300"
              value={weightKg ?? ""}
              onChange={(event) => updateWholeNumber(setWeightKg, event.target.value, "Вес")}
              placeholder="70"
              disabled={!isEditing || loading}
            />
          </label>
          <label className="form-field">
            <span>Возраст</span>
            <input
              type="number"
              min="10"
              max="120"
              step="1"
              value={age ?? ""}
              onChange={(event) => updateWholeNumber(setAge, event.target.value, "Возраст")}
              placeholder="30"
              disabled={!isEditing || loading}
            />
          </label>
        </div>
        <div className="section-head" style={{ marginTop: "18px" }}>
          <h2>Цель и норма БЖУ</h2>
          <span>Выбери свою цель и скорректируй желаемую норму</span>
        </div>
        <div className="goal-grid">
          {goals.map((goal) => (
            <button
              key={goal.id}
              type="button"
              className={`goal-card ${fitnessGoal === goal.id ? "is-active" : ""}`}
              onClick={() => setFitnessGoal(goal.id)}
              disabled={!isEditing || loading}
            >
              <span className="goal-emoji">{goal.emoji}</span>
              <span>{goal.label}</span>
            </button>
          ))}
        </div>
        <div className="form-grid">
          <label className="form-field">
            <span>Белки, г</span>
            <input
              type="number"
              min="0"
              max="1000"
              value={proteinTarget ?? ""}
              onChange={(event) => setProteinTarget(event.target.value)}
              placeholder="140"
              disabled={!isEditing || loading}
            />
          </label>
          <label className="form-field">
            <span>Жиры, г</span>
            <input
              type="number"
              min="0"
              max="500"
              value={fatTarget ?? ""}
              onChange={(event) => setFatTarget(event.target.value)}
              placeholder="70"
              disabled={!isEditing || loading}
            />
          </label>
          <label className="form-field">
            <span>Углеводы, г</span>
            <input
              type="number"
              min="0"
              max="500"
              value={carbsTarget ?? ""}
              onChange={(event) => setCarbsTarget(event.target.value)}
              placeholder="220"
              disabled={!isEditing || loading}
            />
          </label>
        </div>
        <div className="section-actions">
          {!isEditing ? (
            <button type="button" onClick={() => setIsEditing(true)} disabled={loading}>
              Изменить
            </button>
          ) : (
            <>
              <button type="button" onClick={saveProfile} disabled={loading}>
                {loading ? "Сохраняем..." : "Сохранить"}
              </button>
              <button type="button" className="button--secondary" onClick={() => { resetForm(); setIsEditing(false); }} disabled={loading}>
                Отмена
              </button>
            </>
          )}
        </div>
        {error ? <p className="form-error">{error}</p> : null}
      </section>

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
