import { Dumbbell, Plus, Utensils } from "lucide-react";

import IconButton from "../components/IconButton.jsx";
import StatRing from "../components/StatRing.jsx";

const mealLabels = {
  breakfast: "Завтрак",
  lunch: "Обед",
  dinner: "Ужин",
  snack: "Перекус"
};

export default function TodayScreen({ profile, nutrition, workouts, loading, error, onNavigate, onRefresh }) {
  const totals = nutrition?.totals || {};
  const entries = nutrition?.entries || [];
  const workoutItems = workouts?.workouts || [];
  const totalSets = workouts?.total_sets || 0;

  return (
    <section className="screen stack">
      {error ? (
        <div className="notice notice--error">
          <span>{error}</span>
          <button type="button" onClick={onRefresh}>Повторить</button>
        </div>
      ) : null}

      <div className="hero-panel">
        <div className="hero-panel__copy">
          <p className="eyebrow">Баланс дня</p>
          <strong>{totals.calories || 0}</strong>
          <span>ккал</span>
        </div>
        <StatRing value={profile?.xp_progress || 0} max={profile?.xp_to_next || 100} label="XP" color="#0a84ff" />
      </div>

      <div className="quick-actions">
        <IconButton icon={Utensils} onClick={() => onNavigate("nutrition")}>Еда</IconButton>
        <IconButton icon={Dumbbell} className="icon-button--warm" onClick={() => onNavigate("workout")}>Тренировка</IconButton>
      </div>

      <div className="metric-grid">
        <div className="metric">
          <span>Белки</span>
          <strong>{totals.protein || 0} г</strong>
        </div>
        <div className="metric">
          <span>Жиры</span>
          <strong>{totals.fat || 0} г</strong>
        </div>
        <div className="metric">
          <span>Углеводы</span>
          <strong>{totals.carbs || 0} г</strong>
        </div>
        <div className="metric">
          <span>Подходы</span>
          <strong>{totalSets}</strong>
        </div>
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
