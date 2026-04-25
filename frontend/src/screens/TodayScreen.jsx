import { Dumbbell, Plus, Utensils } from "lucide-react";

import IconButton from "../components/IconButton.jsx";
import StatRing from "../components/StatRing.jsx";

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

function macroPercent(value, target) {
  return Math.max(4, Math.min(100, Math.round(((Number(value) || 0) / target) * 100)));
}

function MacroBar({ label, value, target }) {
  return (
    <div className="macro-bar">
      <div>
        <span>{label}</span>
        <strong>{value || 0} / {target} г</strong>
      </div>
      <i style={{ "--bar-fill": `${macroPercent(value, target)}%` }} />
    </div>
  );
}

export default function TodayScreen({ profile, nutrition, workouts, loading, error, onNavigate, onRefresh }) {
  const totals = nutrition?.totals || {};
  const entries = nutrition?.entries || [];
  const workoutItems = workouts?.workouts || [];
  const totalSets = workouts?.total_sets || 0;
  const mealCalories = entries.reduce((acc, entry) => {
    acc[entry.meal_type] = (acc[entry.meal_type] || 0) + entry.calories;
    return acc;
  }, {});

  return (
    <section className="screen stack">
      {error ? (
        <div className="notice notice--error">
          <span>{error}</span>
          <button type="button" onClick={onRefresh}>Повторить</button>
        </div>
      ) : null}

      <div className="hero-panel diary-panel">
        <div className="diary-panel__top">
          <div>
            <p className="eyebrow">Дневник</p>
            <h2>Сегодня</h2>
          </div>
          <span>{profile?.xp_total || 0} XP</span>
        </div>

        <div className="macro-strip">
          <MacroBar label="Белки" value={totals.protein} target={140} />
          <MacroBar label="Жиры" value={totals.fat} target={70} />
          <MacroBar label="Углеводы" value={totals.carbs} target={220} />
        </div>

        <div className="diary-panel__center">
          <div className="calorie-side">
            <strong>1800</strong>
            <span>норма</span>
          </div>
          <StatRing value={totals.calories || 0} max={1800} label="ккал" color="#ffffff" />
          <div className="calorie-side">
            <strong>{totalSets}</strong>
            <span>подходы</span>
          </div>
        </div>
      </div>

      <div className="quick-actions">
        <IconButton icon={Utensils} onClick={() => onNavigate("nutrition")}>Еда</IconButton>
        <IconButton icon={Dumbbell} className="icon-button--warm" onClick={() => onNavigate("workout")}>Тренировка</IconButton>
      </div>

      <div className="meal-summary-grid">
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

      <section className="surface">
        <div className="section-head">
          <h2>Питание</h2>
          <button type="button" onClick={() => onNavigate("nutrition")} aria-label="Добавить питание">
            <Plus size={18} />
          </button>
        </div>
        {loading ? <p className="muted">Загрузка...</p> : null}
        {!loading && entries.length === 0 ? <p className="empty">Сегодня еще нет приемов пищи.</p> : null}
        <div className="list">
          {entries.slice(0, 4).map((entry) => (
            <div className="list-row" key={entry.id}>
              <div>
                <span>{mealLabels[entry.meal_type] || entry.meal_type}</span>
                <strong>{entry.product_name}</strong>
              </div>
              <p>{entry.calories} ккал</p>
            </div>
          ))}
        </div>
      </section>

      <section className="surface">
        <div className="section-head">
          <h2>Тренировки</h2>
          <button type="button" onClick={() => onNavigate("workout")} aria-label="Добавить подход">
            <Plus size={18} />
          </button>
        </div>
        {!loading && workoutItems.length === 0 ? <p className="empty">Подходы появятся после первой тренировки.</p> : null}
        <div className="list">
          {workoutItems.slice(0, 2).map((workout) => (
            <div className="workout-mini" key={workout.id}>
              <div className="list-row">
                <div>
                  <span>{workout.sets.length} подходов</span>
                  <strong>{workout.title}</strong>
                </div>
                <p>{workout.sets.length ? "Готово" : "План"}</p>
              </div>
              {workout.sets.slice(0, 3).map((set) => (
                <div className="sub-row" key={set.id}>
                  <span>{set.exercise_name}</span>
                  <strong>{set.weight_kg} кг × {set.reps}</strong>
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}
