import { Activity, ArrowLeft, CalendarDays, Droplets, Dumbbell, Flame, Moon, PieChart, TrendingUp } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "../api.js";

const DEFAULT_CALORIE_TARGET = 1800;

function isoDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function defaultStartDate() {
  const date = new Date();
  date.setDate(date.getDate() - 6);
  return isoDate(date);
}

function addDays(date, days) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

function makeDateRange(dateFrom, dateTo) {
  const start = new Date(`${dateFrom}T00:00:00`);
  const end = new Date(`${dateTo}T00:00:00`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end < start) return [];

  const days = [];
  for (let current = start; current <= end && days.length < 32; current = addDays(current, 1)) {
    days.push(isoDate(current));
  }
  return days;
}

function labelDate(date) {
  const today = isoDate(new Date());
  const yesterday = isoDate(addDays(new Date(), -1));
  if (date === today) return "сегодня";
  if (date === yesterday) return "вчера";
  return date.slice(5);
}

function shortLabelDate(date) {
  const today = isoDate(new Date());
  const yesterday = isoDate(addDays(new Date(), -1));
  if (date === today) return "сег";
  if (date === yesterday) return "вч";
  return String(Number(date.slice(8, 10)));
}

function average(items) {
  if (!items.length) return 0;
  return Math.round(items.reduce((sum, item) => sum + item.calories, 0) / items.length);
}

function exerciseValue(day, loadType) {
  const type = String(loadType || "").toLowerCase();
  if (type.includes("кардио")) return Number(day.distance_km || day.duration_min || day.best_speed_kmh || 0);
  if (type.includes("статическая")) return Number(day.duration_min || day.sets || 0);
  return Number(day.max_weight_kg || 0);
}

function exerciseUnit(loadType, history = []) {
  const type = String(loadType || "").toLowerCase();
  if (type.includes("кардио")) return history.some((day) => Number(day.distance_km || 0) > 0) ? "км" : "мин";
  if (type.includes("статическая")) return "мин";
  return "кг";
}

function exerciseMetricValue(exercise) {
  const loadType = String(exercise.load_type || "").toLowerCase();
  if (loadType.includes("кардио")) return Number(exercise.distance_km || exercise.duration_min || 0);
  if (loadType.includes("статическая")) return Number(exercise.duration_min || exercise.sets || 0);
  return Number(exercise.volume_kg || 0);
}

function exerciseMetricText(exercise) {
  const loadType = String(exercise.load_type || "").toLowerCase();
  if (loadType.includes("кардио")) {
    const parts = [];
    if (Number(exercise.distance_km || 0) > 0) parts.push(`${Math.round(Number(exercise.distance_km) * 10) / 10} км`);
    if (Number(exercise.duration_min || 0) > 0) parts.push(`${Math.round(Number(exercise.duration_min) * 10) / 10} мин`);
    if (Number(exercise.best_speed_kmh || 0) > 0) parts.push(`${Math.round(Number(exercise.best_speed_kmh) * 10) / 10} км/ч`);
    return parts.join(" · ") || `${exercise.sets || 0} подходов`;
  }
  if (loadType.includes("статическая")) {
    return `${Math.round(Number(exercise.duration_min || 0) * 10) / 10} мин · ${exercise.sets || 0} подходов`;
  }
  return `${Math.round(exercise.volume_kg || 0)} кг объема · ${exercise.max_weight_kg} кг максимум`;
}

export default function StatsScreen({ profile }) {
  const [dateFrom, setDateFrom] = useState(defaultStartDate());
  const [dateTo, setDateTo] = useState(isoDate(new Date()));
  const [stats, setStats] = useState(null);
  const [exerciseDetail, setExerciseDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;

    async function loadStats() {
      setLoading(true);
      setError("");
      try {
        const data = await apiFetch(`/api/stats/range?date_from=${dateFrom}&date_to=${dateTo}`);
        if (!ignore) setStats(data);
      } catch (err) {
        if (!ignore) setError(err.message);
      } finally {
        if (!ignore) setLoading(false);
      }
    }

    loadStats();
    return () => {
      ignore = true;
    };
  }, [dateFrom, dateTo]);

  const nutrition = stats?.nutrition || {};
  const strength = stats?.strength || {};
  const tracking = stats?.tracking || {};
  const days = useMemo(() => {
    const byDate = Object.fromEntries((nutrition.days || []).map((day) => [day.date, day]));
    return makeDateRange(dateFrom, dateTo).map((date) => ({
      date,
      label: labelDate(date),
      shortLabel: shortLabelDate(date),
      calories: byDate[date]?.calories || 0,
      protein: byDate[date]?.protein || 0,
      fat: byDate[date]?.fat || 0,
      carbs: byDate[date]?.carbs || 0
    }));
  }, [nutrition.days, dateFrom, dateTo]);
  const calorieTarget = profile?.calorie_target || DEFAULT_CALORIE_TARGET;
  const maxCalories = Math.max(calorieTarget, ...days.map((day) => day.calories));
  const avgCalories = average(days);
  const macroTotal = Math.max(
    1,
    Number(nutrition.totals?.protein || 0) + Number(nutrition.totals?.fat || 0) + Number(nutrition.totals?.carbs || 0)
  );
  const topExercises = (strength.exercises || []).slice(0, 6);
  const maxExerciseMetric = Math.max(1, ...topExercises.map(exerciseMetricValue));
  const trackingByDate = useMemo(() => {
    return Object.fromEntries((tracking.days || []).map((day) => [day.date, day]));
  }, [tracking.days]);
  const trackingDays = useMemo(() => {
    return makeDateRange(dateFrom, dateTo).map((date) => ({
      date,
      shortLabel: shortLabelDate(date),
      sleep_hours: trackingByDate[date]?.sleep_hours || 0,
      water_liters: trackingByDate[date]?.water_liters || 0
    }));
  }, [dateFrom, dateTo, trackingByDate]);
  const maxSleep = Math.max(8, ...trackingDays.map((day) => day.sleep_hours));
  const maxWater = Math.max(2.5, ...trackingDays.map((day) => day.water_liters));

  async function openExercise(exercise) {
    setDetailLoading(true);
    setError("");
    try {
      const data = await apiFetch(`/api/stats/exercises/${exercise.exercise_id}?date_from=${dateFrom}&date_to=${dateTo}`);
      setExerciseDetail(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setDetailLoading(false);
    }
  }

  if (exerciseDetail) {
    const history = exerciseDetail.history || [];
    const loadType = exerciseDetail.exercise?.load_type || "";
    const maxValue = Math.max(1, ...history.map((day) => exerciseValue(day, loadType)));
    const avgValue = history.length ? history.reduce((sum, day) => sum + exerciseValue(day, loadType), 0) / history.length : 0;
    const unit = exerciseUnit(loadType, history);

    return (
      <section className="screen stack">
        <section className="surface">
          <div className="section-head">
            <button type="button" onClick={() => setExerciseDetail(null)} aria-label="Назад к статистике">
              <ArrowLeft size={18} />
            </button>
            <span>{dateFrom} - {dateTo}</span>
          </div>
          <div className="exercise-detail-head">
            <p className="eyebrow">{exerciseDetail.exercise?.load_type} · {exerciseDetail.exercise?.muscle_group}</p>
            <h2>{exerciseDetail.exercise?.name}</h2>
          </div>
        </section>

        <section className="surface">
          <div className="section-head">
            <h2>Динамика по дням</h2>
            <TrendingUp size={22} color="var(--accent)" />
          </div>
          <p className="hint">Каждый столбец — лучший результат по упражнению за день. Над графиком указана дата, внизу — значение.</p>
          <div className="exercise-history-chart">
            {history.length === 0 ? <p className="empty">За период записей по упражнению нет.</p> : null}
            {history.map((day) => {
              const value = exerciseValue(day, loadType);
              return (
                <div className="exercise-history-column" key={day.date} title={`${day.date}: ${Math.round(value * 10) / 10} ${unit}`}>
                  <div><i style={{ height: `${Math.max(7, Math.round((value / maxValue) * 100))}%` }} /></div>
                  <span>{shortLabelDate(day.date)}</span>
                  <strong>{Math.round(value * 10) / 10}</strong>
                </div>
              );
            })}
          </div>
          <div className="bar-chart">
            <div className="bar-row">
              <span>Максимум</span>
              <i><b style={{ width: "100%" }} /></i>
              <strong>{Math.round(maxValue * 10) / 10} {unit}</strong>
            </div>
            <div className="bar-row">
              <span>Среднее</span>
              <i><b style={{ width: `${Math.max(6, Math.round((avgValue / maxValue) * 100))}%` }} /></i>
              <strong>{Math.round(avgValue * 10) / 10} {unit}</strong>
            </div>
          </div>
          <p className="hint">Единица графика: {unit}.</p>
        </section>

        <section className="surface">
          <div className="section-head">
            <h2>Записи</h2>
            <Dumbbell size={22} color="var(--accent)" />
          </div>
          <div className="list">
            {(exerciseDetail.sets || []).map((set) => (
              <div className="list-row" key={set.id}>
                <div>
                  <span>{set.created_at?.slice(0, 10)}</span>
                  <strong>{set.exercise_name}</strong>
                </div>
                <p>
                  {loadType === "кардио"
                    ? `${set.distance_km || 0} км · ${set.duration_min || 0} мин`
                    : loadType === "статическая"
                      ? `${set.duration_min || 0} мин`
                      : `${set.weight_kg} кг x ${set.reps}`}
                </p>
              </div>
            ))}
          </div>
        </section>
      </section>
    );
  }

  return (
    <section className="screen stack">
      <section className="stats-hero">
        <div>
          <p className="eyebrow">Аналитика</p>
          <h2>Видно, что реально работает</h2>
          <p>Выбери период и сравни питание, БЖУ и силовые без лишней ручной математики.</p>
        </div>
        <TrendingUp size={30} />
      </section>

      <div className="surface">
        <div className="section-head">
          <h2>Период</h2>
          <CalendarDays size={22} color="var(--accent)" />
        </div>
        <div className="stats-range">
          <label className="field">
            <span>Начало</span>
            <input className="plain-input" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
          </label>
          <label className="field">
            <span>Конец</span>
            <input className="plain-input" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </label>
        </div>
        {error ? <p className="form-error">{error}</p> : null}
        {loading ? <p className="muted">Считаю показатели...</p> : null}
      </div>

      <section className="surface">
        <div className="section-head">
          <h2>Питание</h2>
          <Flame size={22} color="var(--workout)" />
        </div>
        <div className="metric-grid metric-grid--compact">
          <div className="metric"><span>Всего</span><strong>{nutrition.totals?.calories || 0}</strong></div>
          <div className="metric"><span>Среднее</span><strong>{avgCalories}</strong></div>
          <div className="metric"><span>Дней</span><strong>{days.length}</strong></div>
          <div className="metric"><span>Цель</span><strong>{calorieTarget}</strong></div>
        </div>

        <div className="calorie-columns" aria-label="Калории по дням">
          {days.length === 0 ? <p className="empty">Выбери корректный период.</p> : null}
          {days.map((day) => (
            <div className={day.calories >= calorieTarget ? "calorie-column is-full" : "calorie-column"} key={day.date}>
              <div>
                <i style={{ height: `${Math.max(6, Math.round((day.calories / maxCalories) * 100))}%` }} />
              </div>
              <span>{day.shortLabel}</span>
              <strong>{day.calories}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="surface">
        <div className="section-head">
          <h2>Баланс БЖУ</h2>
          <PieChart size={22} color="var(--nutrition)" />
        </div>
        <div className="macro-split">
          <i style={{ width: `${Math.round(((nutrition.totals?.protein || 0) / macroTotal) * 100)}%` }} />
          <i style={{ width: `${Math.round(((nutrition.totals?.fat || 0) / macroTotal) * 100)}%` }} />
          <i style={{ width: `${Math.round(((nutrition.totals?.carbs || 0) / macroTotal) * 100)}%` }} />
        </div>
        <div className="macro-legend">
          <span><b /> Белки {nutrition.totals?.protein || 0} г</span>
          <span><b /> Жиры {nutrition.totals?.fat || 0} г</span>
          <span><b /> Углеводы {nutrition.totals?.carbs || 0} г</span>
        </div>
        <div className="macro-day-list">
          {days.slice(-7).map((day) => (
            <div className="macro-day" key={day.date}>
              <span>{day.label}</span>
              <div>
                <i style={{ width: `${Math.min(100, Math.round((day.protein / 140) * 100))}%` }} />
                <i style={{ width: `${Math.min(100, Math.round((day.fat / 70) * 100))}%` }} />
                <i style={{ width: `${Math.min(100, Math.round((day.carbs / 220) * 100))}%` }} />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="surface">
        <div className="section-head">
          <h2>Упражнения</h2>
          <Dumbbell size={22} color="var(--accent)" />
        </div>
        <div className="metric-grid metric-grid--compact">
          <div className="metric"><span>Тренировки</span><strong>{strength.total_workouts || 0}</strong></div>
          <div className="metric"><span>Подходы</span><strong>{strength.total_sets || 0}</strong></div>
        </div>

        <div className="strength-bars">
          {topExercises.length === 0 ? <p className="empty">Силовых записей за период пока нет.</p> : null}
          {topExercises.map((exercise) => (
            <button className="strength-bar strength-bar--button" type="button" key={exercise.exercise_id} onClick={() => openExercise(exercise)}>
              <div>
                <span>{exercise.muscle_group}</span>
                <strong>{exercise.exercise_name}</strong>
              </div>
              <i><b style={{ width: `${Math.max(6, Math.round((exerciseMetricValue(exercise) / maxExerciseMetric) * 100))}%` }} /></i>
              <p>{exerciseMetricText(exercise)}</p>
            </button>
          ))}
        </div>
        {detailLoading ? <p className="muted">Открываю упражнение...</p> : null}
      </section>

      <section className="surface">
        <div className="section-head">
          <h2>Сон и вода</h2>
          <Droplets size={22} color="var(--nutrition)" />
        </div>
        <div className="metric-grid metric-grid--compact">
          <div className="metric"><span>Сон средний</span><strong>{tracking.totals?.avg_sleep_hours || 0} ч</strong></div>
          <div className="metric"><span>Сон всего</span><strong>{tracking.totals?.sleep_hours || 0} ч</strong></div>
          <div className="metric"><span>Вода средняя</span><strong>{tracking.totals?.avg_water_liters || 0} л</strong></div>
          <div className="metric"><span>Вода всего</span><strong>{tracking.totals?.water_liters || 0} л</strong></div>
        </div>
        <div className="tracking-stat-grid">
          <div>
            <div className="tracking-stat-title"><Moon size={16} /> Сон</div>
            <div className="mini-columns">
              {trackingDays.map((day) => (
                <div className="mini-column" key={`sleep-${day.date}`}>
                  <i style={{ height: `${Math.max(5, Math.round((day.sleep_hours / maxSleep) * 100))}%` }} />
                  <span>{day.shortLabel}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <div className="tracking-stat-title"><Droplets size={16} /> Вода</div>
            <div className="mini-columns mini-columns--water">
              {trackingDays.map((day) => (
                <div className="mini-column" key={`water-${day.date}`}>
                  <i style={{ height: `${Math.max(5, Math.round((day.water_liters / maxWater) * 100))}%` }} />
                  <span>{day.shortLabel}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="surface">
        <div className="section-head">
          <h2>Вывод</h2>
          <Activity size={22} color="var(--accent)" />
        </div>
        <p className="empty">
          Польза HealthQuest здесь простая: ты видишь не отдельные записи, а картину периода. Если средние калории рядом с целью, а силовой объем растет, план работает.
        </p>
      </section>
    </section>
  );
}
