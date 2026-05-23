import { Beef, Dumbbell, Flame, Plus, Sparkles, Target, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "../api.js";
import StatRing from "../components/StatRing.jsx";

const DAILY_TARGET = 1800;
const macroTargets = {
  protein: 140,
  fat: 70,
  carbs: 220
};

const mealLabels = {
  breakfast: "Завтрак",
  lunch: "Обед",
  dinner: "Ужин",
  snack: "Перекус"
};

const mealMeta = [
  { key: "breakfast", label: "Завтрак", time: "08:00", target: 350 },
  { key: "lunch", label: "Обед", time: "12:00", target: 550 },
  { key: "snack", label: "Перекус", time: "16:00", target: 250 },
  { key: "dinner", label: "Ужин", time: "20:00", target: 450 }
];

function isoDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function shiftDate(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date;
}

function percent(value, target) {
  return Math.max(3, Math.min(100, Math.round(((Number(value) || 0) / target) * 100)));
}

function dayLabel(date) {
  const today = isoDate(new Date());
  const yesterday = isoDate(shiftDate(-1));
  const tomorrow = isoDate(shiftDate(1));
  if (date === today) return "сегодня";
  if (date === yesterday) return "вчера";
  if (date === tomorrow) return "завтра";
  return date.slice(5);
}

function shortDayLabel(date) {
  const today = isoDate(new Date());
  const yesterday = isoDate(shiftDate(-1));
  const tomorrow = isoDate(shiftDate(1));
  if (date === today) return "сег";
  if (date === yesterday) return "вч";
  if (date === tomorrow) return "зав";
  return String(Number(date.slice(8, 10)));
}

function buildDays(stats) {
  const byDate = Object.fromEntries((stats?.nutrition?.days || []).map((day) => [day.date, day]));
  return [-1, 0, 1].map((offset) => {
    const date = isoDate(shiftDate(offset));
    return {
      date,
      label: dayLabel(date),
      shortLabel: shortDayLabel(date),
      calories: byDate[date]?.calories || 0,
      planned: offset > 0
    };
  });
}

function buildWeek(stats) {
  const byDate = Object.fromEntries((stats?.nutrition?.days || []).map((day) => [day.date, day]));
  return [-5, -4, -3, -2, -1, 0, 1].map((offset) => {
    const date = isoDate(shiftDate(offset));
    return {
      date,
      label: dayLabel(date),
      shortLabel: shortDayLabel(date),
      calories: byDate[date]?.calories || 0,
      planned: offset > 0
    };
  });
}

function MacroBar({ label, value, target }) {
  return (
    <div className="macro-progress">
      <div>
        <span>{label}</span>
        <strong>{value || 0} / {target} г</strong>
      </div>
      <i style={{ "--bar-fill": `${percent(value, target)}%` }} />
    </div>
  );
}

function workoutSummary(set) {
  const hasCardio = set.distance_km || set.duration_min || set.speed_kmh || set.pace_min_per_km;
  if (set.load_type?.includes("кардио") || set.load_type?.includes("cardio") || hasCardio) {
    const parts = [];
    if (set.distance_km) parts.push(`${set.distance_km} км`);
    if (set.duration_min) parts.push(`${set.duration_min} мин`);
    if (set.speed_kmh) parts.push(`${set.speed_kmh} км/ч`);
    if (set.pace_min_per_km) parts.push(`${set.pace_min_per_km} мин/км`);
    return parts.length ? parts.join(" · ") : "Заполните параметры";
  }
  return `${set.weight_kg || 0} кг x ${set.reps || 0}`;
}

export default function TodayScreen({ profile, nutrition, workouts, loading, error, onNavigate, onRefresh }) {
  const [rangeStats, setRangeStats] = useState(null);
  const [rangeError, setRangeError] = useState("");
  const [tracking, setTracking] = useState({ sleep_hours: null, water_liters: null });
  const [trackingError, setTrackingError] = useState("");
  const [trackingLoading, setTrackingLoading] = useState(false);
  const [summaryText, setSummaryText] = useState("");
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState("");
  const [summaryPeriodDays, setSummaryPeriodDays] = useState(1);
  const [showPeriodPicker, setShowPeriodPicker] = useState(false);
  
  const totals = nutrition?.totals || {};
  const entries = nutrition?.entries || [];
  const workoutItems = workouts?.workouts || [];
  const totalSets = workouts?.total_sets || 0;
  const calories = totals.calories || 0;
  const caloriesLeft = Math.max(0, DAILY_TARGET - calories);
  const dayScore = Math.min(100, Math.round((calories / DAILY_TARGET) * 100));
  const mealCalories = entries.reduce((acc, entry) => {
    acc[entry.meal_type] = (acc[entry.meal_type] || 0) + entry.calories;
    return acc;
  }, {});

  useEffect(() => {
    let ignore = false;

    async function loadRange() {
      setRangeError("");
      try {
        const dateFrom = isoDate(shiftDate(-5));
        const dateTo = isoDate(shiftDate(1));
        const data = await apiFetch(`/api/stats/range?date_from=${dateFrom}&date_to=${dateTo}`);
        if (!ignore) setRangeStats(data);
      } catch (err) {
        if (!ignore) setRangeError(err.message);
      }
    }

    async function loadTracking() {
      setTrackingError("");
      try {
        const data = await apiFetch(`/api/tracking/today`);
        if (!ignore) setTracking(data);
      } catch (err) {
        if (!ignore) setTrackingError(err.message);
      }
    }

    loadRange();
    loadTracking();
    return () => {
      ignore = true;
    };
  }, [nutrition]);

  async function saveTracking() {
    setTrackingError("");
    setTrackingLoading(true);
    try {
      const payload = {
        sleep_hours: tracking.sleep_hours,
        water_liters: tracking.water_liters,
      };
      const data = await apiFetch(`/api/tracking/today`, {
        method: "POST",
        body: payload,
      });
      setTracking(data);
    } catch (err) {
      setTrackingError(err.message);
    } finally {
      setTrackingLoading(false);
    }
  }

  async function deleteEntry(entryId) {
    try {
      await apiFetch(`/api/nutrition/entries/${entryId}`, {
        method: "DELETE",
      });
      if (onRefresh) {
        onRefresh();
      }
    } catch (err) {
      setSummaryError(err.message);
    }
  }

  async function loadSummary() {
    setSummaryError("");
    setSummaryLoading(true);
    try {
      const endpoint = summaryPeriodDays === 1 
        ? "/api/summary/today"
        : `/api/summary/period?days=${summaryPeriodDays}`;
      const data = await apiFetch(endpoint, { method: "POST" });
      setSummaryText(data.summary || "");
    } catch (err) {
      setSummaryError(err.message);
    } finally {
      setSummaryLoading(false);
    }
  }

  async function handleFabClick() {
    await loadSummary();
    setShowPeriodPicker(false);
  }

  const threeDays = useMemo(() => buildDays(rangeStats), [rangeStats]);
  const weekDays = useMemo(() => buildWeek(rangeStats), [rangeStats]);
  const maxWeekCalories = Math.max(DAILY_TARGET, ...weekDays.map((day) => day.calories));
  const coachText = calories === 0
    ? "Добавь первый прием пищи, и дневник начнет показывать реальную картину."
    : caloriesLeft > 0
      ? `До нормы осталось ${caloriesLeft} ккал. Это помогает не гадать, а спокойно добрать день.`
      : "Норма закрыта. Теперь главное не потерять ритм и отметить тренировку, если она была.";

  return (
    <section className="screen stack">
      {error ? (
        <div className="notice notice--error">
          <span>{error}</span>
          <button type="button" onClick={onRefresh}>Повторить</button>
        </div>
      ) : null}

      <section className="today-hero">
        <div className="today-hero__copy">
          <p className="eyebrow">Баланс дня</p>
          <h2>{caloriesLeft ? `${caloriesLeft} ккал осталось` : "Дневная цель закрыта"}</h2>
          <p>{coachText}</p>
        </div>
        <div className="today-hero__ring">
          <StatRing value={calories} max={DAILY_TARGET} label="ккал" color="#7650d9" />
          <span>{dayScore}% дня</span>
        </div>
      </section>

      <section className="insight-grid">
        <article className="insight-card">
          <Flame size={20} />
          <span>Съедено</span>
          <strong>{calories}</strong>
          <p>из {DAILY_TARGET} ккал</p>
        </article>
        <article className="insight-card">
          <Dumbbell size={20} />
          <span>Тренировка</span>
          <strong>{totalSets}</strong>
          <p>подходов сегодня</p>
        </article>
        <article className="insight-card">
          <Sparkles size={20} />
          <span>Опыт</span>
          <strong>{profile?.xp_total || 0}</strong>
          <p>XP всего</p>
        </article>
      </section>

      <section className="surface">
        <div className="section-head">
          <h2>Сон и вода</h2>
        </div>
        <div className="tracking-grid">
          <label className="tracking-field">
            <span>Сон, ч</span>
            <input
              type="number"
              step="0.1"
              min="0"
              max="24"
              value={tracking.sleep_hours ?? ""}
              onChange={(event) => setTracking((prev) => ({ ...prev, sleep_hours: event.target.value ? Number(event.target.value) : null }))}
              placeholder="0.0"
            />
          </label>
          <label className="tracking-field">
            <span>Вода, л</span>
            <input
              type="number"
              step="0.1"
              min="0"
              max="20"
              value={tracking.water_liters ?? ""}
              onChange={(event) => setTracking((prev) => ({ ...prev, water_liters: event.target.value ? Number(event.target.value) : null }))}
              placeholder="0.0"
            />
          </label>
        </div>
        <div className="section-actions">
          <button type="button" onClick={saveTracking} disabled={trackingLoading}>
            {trackingLoading ? "Сохранение..." : "Сохранить трекинг"}
          </button>
        </div>
        {trackingError ? <p className="form-error">{trackingError}</p> : null}
        {summaryError ? <p className="form-error">{summaryError}</p> : null}
        {summaryText ? (
          <div className="summary-card">
            <strong>Сводка дня</strong>
            <p>{summaryText}</p>
          </div>
        ) : null}
      </section>

      <button
        type="button"
        className="fab fab--summary"
        onClick={() => setShowPeriodPicker(true)}
        disabled={summaryLoading}
        title="Выбрать период сводки"
      >
        <Sparkles size={24} />
      </button>

      {showPeriodPicker && (
        <div className="modal-overlay" onClick={() => setShowPeriodPicker(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Выбери период</h3>
            <div className="period-buttons">
              {[1, 7, 14, 30].map((days) => (
                <button
                  key={days}
                  type="button"
                  className={`period-btn ${summaryPeriodDays === days ? "is-active" : ""}`}
                  onClick={() => setSummaryPeriodDays(days)}
                >
                  {days === 1 ? "День" : `${days} дней`}
                </button>
              ))}
            </div>
            <button
              type="button"
              className="button--primary"
              onClick={handleFabClick}
              disabled={summaryLoading}
            >
              {summaryLoading ? "Генерирую..." : "Получить сводку"}
            </button>
          </div>
        </div>
      )}

      <section className="surface surface--focus">
        <div className="section-head">
          <h2>Вчера, сегодня, завтра</h2>
          <Target size={22} color="var(--accent)" />
        </div>
        <div className="day-compare">
          {threeDays.map((day) => (
            <div className={day.planned ? "day-pill is-planned" : "day-pill"} key={day.date}>
              <span>{day.label}</span>
              <strong>{day.planned ? DAILY_TARGET : day.calories}</strong>
              <p>{day.planned ? "план" : "ккал"}</p>
            </div>
          ))}
        </div>
        <div className="week-bars" aria-label="Калории за неделю">
          {weekDays.map((day) => {
            const displayCalories = day.planned ? DAILY_TARGET : day.calories;
            return (
              <div className={day.planned ? "week-bar is-planned" : "week-bar"} key={day.date}>
                <i style={{ height: `${Math.max(8, Math.round((displayCalories / maxWeekCalories) * 100))}%` }} />
                <span>{day.shortLabel}</span>
              </div>
            );
          })}
        </div>
        {rangeError ? <p className="form-error">{rangeError}</p> : null}
      </section>

      <section className="surface">
        <div className="section-head">
          <h2>Баланс БЖУ</h2>
          <Beef size={22} color="var(--nutrition)" />
        </div>
        <div className="macro-progress-list">
          <MacroBar label="Белки" value={totals.protein} target={macroTargets.protein} />
          <MacroBar label="Жиры" value={totals.fat} target={macroTargets.fat} />
          <MacroBar label="Углеводы" value={totals.carbs} target={macroTargets.carbs} />
        </div>
      </section>

      <section className="surface">
        <div className="section-head">
          <h2>Приемы пищи</h2>
          <button type="button" onClick={() => onNavigate("nutrition")} aria-label="Добавить питание">
            <Plus size={18} />
          </button>
        </div>
        <div className="meal-summary-grid meal-summary-grid--calm">
          {mealMeta.map((meal) => {
            const value = mealCalories[meal.key] || 0;
            return (
              <button
                key={meal.key}
                type="button"
                className="meal-card"
                onClick={() => onNavigate("nutrition")}
                style={{ "--meal-progress": `${Math.min(100, Math.round((value / meal.target) * 100))}%` }}
              >
                <span>{meal.label}</span>
                <b>{meal.time}</b>
                <strong>{value} ккал</strong>
                <p>из {meal.target} ккал</p>
                <i />
              </button>
            );
          })}
        </div>
      </section>

      <section className="surface">
        <div className="section-head">
          <h2>Сегодня в журнале</h2>
          <button type="button" onClick={() => onNavigate("workout")} aria-label="Добавить подход">
            <Plus size={18} />
          </button>
        </div>
        {loading ? <p className="muted">Загрузка...</p> : null}
        {!loading && entries.length === 0 && workoutItems.length === 0 ? <p className="empty">Пока пусто. Начни с еды или тренировки во вкладках снизу.</p> : null}
        <div className="list">
          {entries.slice(0, 3).map((entry) => (
            <div className="list-row list-row--deletable" key={entry.id}>
              <div>
                <span>{mealLabels[entry.meal_type] || entry.meal_type}</span>
                <strong>{entry.product_name}</strong>
              </div>
              <button type="button" className="ghost-icon" onClick={() => deleteEntry(entry.id)} aria-label="Удалить прием пищи">
                <X size={16} />
              </button>
              <p>{entry.calories} ккал</p>
            </div>
          ))}
          {workoutItems.slice(0, 2).map((workout) => (
            <div className="workout-mini" key={workout.id}>
              <div className="list-row">
                <div>
                  <span>{workout.sets.length} подходов</span>
                  <strong>{workout.title}</strong>
                </div>
                <p>{workout.sets.length ? "готово" : "план"}</p>
              </div>
              {workout.sets.slice(0, 2).map((set) => (
                <div className="sub-row" key={set.id}>
                  <span>{set.exercise_name}</span>
                  <strong>{workoutSummary(set)}</strong>
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}
