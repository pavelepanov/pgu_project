import { useState } from "react";
import { apiFetch } from "../api.js";

export default function OnboardingScreen({ profile, onRegistered }) {
  const [step, setStep] = useState(1);
  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [age, setAge] = useState("");
  const [fitnessGoal, setFitnessGoal] = useState("maintain");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const bmi = heightCm && weightKg
    ? Math.round((Number(weightKg) / ((Number(heightCm) / 100) ** 2)) * 10) / 10
    : null;

  const goals = [
    { id: "lose", label: "Похудение", emoji: "📉" },
    { id: "gain", label: "Набор массы", emoji: "📈" },
    { id: "maintain", label: "Поддержание", emoji: "➡️" }
  ];

  function validateStep(stepNumber) {
    const height = Number(heightCm);
    const weight = Number(weightKg);
    const ageValue = Number(age);

    if (stepNumber === 1) {
      if (!heightCm) return "Укажите рост";
      if (height < 50 || height > 300) return "Рост должен быть от 50 до 300 см";
    }
    if (stepNumber === 2) {
      if (!weightKg) return "Укажите вес";
      if (weight < 20 || weight > 300) return "Вес должен быть от 20 до 300 кг";
    }
    if (stepNumber === 3) {
      if (!age) return "Укажите возраст";
      if (ageValue < 10 || ageValue > 120) return "Возраст должен быть от 10 до 120 лет";
    }
    return "";
  }

  async function handleRegister() {
    if (!heightCm || !weightKg || !age) {
      setError("Заполните все поля");
      return;
    }

    const finalError = validateStep(1) || validateStep(2) || validateStep(3);
    if (finalError) {
      setError(finalError);
      return;
    }

    setError("");
    setLoading(true);
    try {
      const data = await apiFetch("/api/auth/register", {
        method: "POST",
        body: {
          height_cm: Number(heightCm),
          weight_kg: Number(weightKg),
          age: Number(age),
          fitness_goal: fitnessGoal
        }
      });
      if (onRegistered) {
        onRegistered(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="screen stack onboarding">
      <div className="onboarding-hero">
        <div className="onboarding-logo">✨</div>
        <h1>HealthQuest</h1>
        <p>Твой персональный фитнес-ассистент</p>
      </div>

      {step === 1 && (
        <section className="surface">
          <div className="section-head">
            <h2>Рост</h2>
            <span>Шаг 1 из 4</span>
          </div>
          <label className="form-field">
            <span>Введи свой рост в сантиметрах</span>
            <input
              type="number"
              min="50"
              max="250"
              value={heightCm}
              onChange={(e) => setHeightCm(e.target.value)}
              placeholder="170"
              autoFocus
            />
          </label>
          <div className="section-actions">
            <button
              type="button"
              onClick={() => {
                const errorMessage = validateStep(1);
                if (errorMessage) {
                  setError(errorMessage);
                  return;
                }
                setError("");
                setStep(2);
              }}
              disabled={!heightCm || loading}
            >
              Далее
            </button>
          </div>
          {error && <p className="form-error">{error}</p>}
          {error && <p className="form-error">{error}</p>}
        </section>
      )}

      {step === 2 && (
        <section className="surface">
          <div className="section-head">
            <h2>Вес</h2>
            <span>Шаг 2 из 4</span>
          </div>
          <label className="form-field">
            <span>Введи свой вес в килограммах</span>
            <input
              type="number"
              step="0.1"
              min="20"
              max="300"
              value={weightKg}
              onChange={(e) => setWeightKg(e.target.value)}
              placeholder="70"
              autoFocus
            />
          </label>
          {bmi && (
            <p className="hint" style={{ marginTop: "12px" }}>
              Твой BMI: <strong>{bmi}</strong>
            </p>
          )}
          <div className="section-actions">
            <button type="button" onClick={() => setStep(1)}>
              Назад
            </button>
            <button
              type="button"
              onClick={() => {
                const errorMessage = validateStep(2);
                if (errorMessage) {
                  setError(errorMessage);
                  return;
                }
                setError("");
                setStep(3);
              }}
              disabled={!weightKg || loading}
            >
              Далее
            </button>
          </div>
          {error && <p className="form-error">{error}</p>}
        </section>
      )}

      {step === 3 && (
        <section className="surface">
          <div className="section-head">
            <h2>Возраст</h2>
            <span>Шаг 3 из 4</span>
          </div>
          <label className="form-field">
            <span>Введи свой возраст</span>
            <input
              type="number"
              min="10"
              max="120"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              placeholder="30"
              autoFocus
            />
          </label>
          <div className="section-actions">
            <button type="button" onClick={() => setStep(2)}>
              Назад
            </button>
            <button
              type="button"
              onClick={() => {
                const errorMessage = validateStep(3);
                if (errorMessage) {
                  setError(errorMessage);
                  return;
                }
                setError("");
                setStep(4);
              }}
              disabled={!age || loading}
            >
              Далее
            </button>
          </div>
          {error && <p className="form-error">{error}</p>}
        </section>
      )}

      {step === 4 && (
        <section className="surface">
          <div className="section-head">
            <h2>Цель</h2>
            <span>Шаг 4 из 4</span>
          </div>
          <p className="hint">Выбери свою основную цель. От неё зависит план питания и тренировок.</p>
          <div className="goal-grid">
            {goals.map((goal) => (
              <button
                key={goal.id}
                type="button"
                className={`goal-card ${fitnessGoal === goal.id ? "is-active" : ""}`}
                onClick={() => setFitnessGoal(goal.id)}
              >
                <span className="goal-emoji">{goal.emoji}</span>
                <span>{goal.label}</span>
              </button>
            ))}
          </div>
          <div className="section-actions">
            <button type="button" onClick={() => setStep(3)}>
              Назад
            </button>
            <button
              type="button"
              onClick={handleRegister}
              disabled={loading}
              className="button--primary"
            >
              {loading ? "Сохраняю..." : "Завершить регистрацию"}
            </button>
          </div>
          {error && <p className="form-error">{error}</p>}
        </section>
      )}
    </section>
  );
}
