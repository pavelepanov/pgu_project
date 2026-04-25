import { Check, ClipboardList, Plus, Search, X } from "lucide-react";
import { useEffect, useState } from "react";

import { apiFetch } from "../api.js";
import IconButton from "../components/IconButton.jsx";
import { hapticImpact } from "../telegram.js";

const emptyMetrics = {
  weight: 0,
  reps: 8,
  duration: "",
  distance: "",
  speed: "",
  pace: ""
};

function exerciseMode(exercise) {
  if (exercise?.load_type === "кардио") return "cardio";
  if (exercise?.load_type === "статическая") return "timed";
  return "strength";
}

function metricSummary(set) {
  if (!set) return "";
  if (set.load_type === "кардио") {
    const parts = [];
    if (set.distance_km) parts.push(`${set.distance_km} км`);
    if (set.duration_min) parts.push(`${set.duration_min} мин`);
    if (set.speed_kmh) parts.push(`${set.speed_kmh} км/ч`);
    if (set.pace_min_per_km) parts.push(`${set.pace_min_per_km} мин/км`);
    return parts.join(" · ") || "кардио";
  }
  if (set.load_type === "статическая") {
    return set.duration_min ? `${set.duration_min} мин` : `${set.reps} повтор.`;
  }
  return `${set.weight_kg} кг x ${set.reps}`;
}

function numeric(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatDelta(value) {
  if (!Number.isFinite(value)) return "0";
  return `${value > 0 ? "+" : ""}${Math.round(value * 10) / 10}`;
}

export default function WorkoutScreen({ workouts, onSaved }) {
  const [title, setTitle] = useState("Тренировка");
  const [query, setQuery] = useState("");
  const [planQuery, setPlanQuery] = useState("");
  const [exercises, setExercises] = useState([]);
  const [planExercises, setPlanExercises] = useState([]);
  const [knownPlanExercises, setKnownPlanExercises] = useState({});
  const [plans, setPlans] = useState([]);
  const [activePlan, setActivePlan] = useState(null);
  const [showBuilder, setShowBuilder] = useState(false);
  const [planTitle, setPlanTitle] = useState("");
  const [planDescription, setPlanDescription] = useState("");
  const [planExerciseIds, setPlanExerciseIds] = useState([]);
  const [selected, setSelected] = useState(null);
  const [previous, setPrevious] = useState(null);
  const [metrics, setMetrics] = useState(emptyMetrics);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const activeWorkout = workouts?.workouts?.[0] || null;
  const selectedPlanExercises = planExerciseIds.map((id) => knownPlanExercises[id]).filter(Boolean);
  const mode = exerciseMode(selected);
  const computedSpeed = numeric(metrics.distance) && numeric(metrics.duration)
    ? numeric(metrics.distance) / (numeric(metrics.duration) / 60)
    : numeric(metrics.speed);
  const computedPace = numeric(metrics.distance) && numeric(metrics.duration)
    ? numeric(metrics.duration) / numeric(metrics.distance)
    : numeric(metrics.pace);
  const weightDelta = previous ? numeric(metrics.weight) - Number(previous.weight_kg || 0) : 0;

  useEffect(() => {
    if (activePlan) return;
    const timeout = window.setTimeout(async () => {
      try {
        const data = await apiFetch(`/api/dictionaries/exercises?query=${encodeURIComponent(query)}`);
        setExercises(data.items || []);
      } catch (err) {
        setError(err.message);
      }
    }, 180);
    return () => window.clearTimeout(timeout);
  }, [query, activePlan]);

  useEffect(() => {
    const timeout = window.setTimeout(async () => {
      try {
        const data = await apiFetch(`/api/dictionaries/exercises?query=${encodeURIComponent(planQuery)}`);
        const items = data.items || [];
        setPlanExercises(items);
        setKnownPlanExercises((current) => {
          const next = { ...current };
          items.forEach((exercise) => {
            next[exercise.id] = exercise;
          });
          return next;
        });
      } catch (err) {
        setError(err.message);
      }
    }, 180);
    return () => window.clearTimeout(timeout);
  }, [planQuery]);

  async function loadPlans() {
    try {
      const data = await apiFetch("/api/workout-plans");
      setPlans(data.items || []);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadPlans();
  }, []);

  function updateMetric(field, value) {
    setMetrics((current) => ({ ...current, [field]: value }));
  }

  async function chooseExercise(exercise) {
    setSelected(exercise);
    setError("");
    try {
      const data = await apiFetch(`/api/workouts/previous-set?exercise_id=${exercise.id}`);
      setPrevious(data.item);
      if (data.item) {
        setMetrics({
          weight: data.item.weight_kg || 0,
          reps: data.item.reps || 8,
          duration: data.item.duration_min || "",
          distance: data.item.distance_km || "",
          speed: data.item.speed_kmh || "",
          pace: data.item.pace_min_per_km || ""
        });
      } else {
        setMetrics(emptyMetrics);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function createWorkout(showToast = true) {
    setError("");
    try {
      const workout = await apiFetch("/api/workouts", {
        method: "POST",
        body: { title: title || "Тренировка" }
      });
      if (showToast) await onSaved(`Создана: ${workout.title}`);
      return workout;
    } catch (err) {
      setError(err.message);
      if (!showToast) throw err;
      return null;
    }
  }

  function togglePlanExercise(exerciseId) {
    setPlanExerciseIds((current) => (
      current.includes(exerciseId)
        ? current.filter((id) => id !== exerciseId)
        : [...current, exerciseId]
    ));
  }

  async function createPlan() {
    if (!planTitle.trim()) {
      setError("Введите название плана");
      return;
    }
    if (planExerciseIds.length === 0) {
      setError("Выберите упражнения для плана");
      return;
    }

    setSaving(true);
    setError("");
    try {
      await apiFetch("/api/workout-plans", {
        method: "POST",
        body: {
          title: planTitle,
          description: planDescription,
          exercises: planExerciseIds.map((exerciseId) => ({
            exercise_id: exerciseId,
            target_sets: 3,
            target_reps: 10
          }))
        }
      });
      setPlanTitle("");
      setPlanDescription("");
      setPlanExerciseIds([]);
      setShowBuilder(false);
      await loadPlans();
      await onSaved("План тренировки создан");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function startPlan(planId) {
    setSaving(true);
    setError("");
    try {
      const data = await apiFetch(`/api/workout-plans/${planId}/start`, { method: "POST" });
      setActivePlan(data.plan);
      setTitle(data.workout?.title || "Тренировка");
      if (data.plan?.exercises?.[0]) {
        const first = data.plan.exercises[0];
        await chooseExercise({
          id: first.exercise_id,
          name: first.exercise_name,
          muscle_group: first.muscle_group,
          load_type: first.load_type
        });
      }
      await onSaved("План открыт как тренировка");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  function buildSetPayload() {
    if (mode === "cardio") {
      return {
        exercise_id: selected.id,
        weight_kg: 0,
        reps: 1,
        duration_min: numeric(metrics.duration) || null,
        distance_km: numeric(metrics.distance) || null,
        speed_kmh: computedSpeed ? Math.round(computedSpeed * 100) / 100 : null,
        pace_min_per_km: computedPace ? Math.round(computedPace * 100) / 100 : null
      };
    }
    if (mode === "timed") {
      return {
        exercise_id: selected.id,
        weight_kg: 0,
        reps: numeric(metrics.reps) || 1,
        duration_min: numeric(metrics.duration) || null
      };
    }
    return {
      exercise_id: selected.id,
      weight_kg: numeric(metrics.weight),
      reps: numeric(metrics.reps)
    };
  }

  function validateSet() {
    if (!selected) return "Выберите упражнение";
    if (mode === "strength") {
      if (numeric(metrics.weight) > 2000) return "Вес должен быть не больше 2000 кг";
      if (numeric(metrics.reps) <= 0) return "Повторы должны быть больше нуля";
    }
    if (mode === "cardio" && !numeric(metrics.duration) && !numeric(metrics.distance)) {
      return "Для кардио укажите длительность или дистанцию";
    }
    if (mode === "timed" && !numeric(metrics.duration)) {
      return "Укажите длительность выполнения";
    }
    return "";
  }

  async function addSet() {
    const validationError = validateSet();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSaving(true);
    setError("");
    try {
      const workout = activeWorkout || (await createWorkout(false));
      await apiFetch(`/api/workouts/${workout.id}/sets`, {
        method: "POST",
        body: buildSetPayload()
      });
      hapticImpact("medium");
      await onSaved("Подход добавлен. +5 XP");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  function renderPrevious() {
    if (!selected) return null;
    if (!previous) return <p className="hint">Первый подход по этому упражнению.</p>;

    if (mode === "cardio") {
      return (
        <p className="compare-pill">
          Прошлый раз: {metricSummary(previous)}
          <span>Сейчас: {metricSummary({ ...previous, ...buildSetPayload(), load_type: "кардио" }) || "заполни показатели"}</span>
        </p>
      );
    }
    if (mode === "timed") {
      const durationDelta = numeric(metrics.duration) - Number(previous.duration_min || 0);
      return (
        <p className="compare-pill">
          Прошлый раз: {metricSummary(previous)}
          <span>Сейчас: {formatDelta(durationDelta)} мин к прошлому результату</span>
        </p>
      );
    }
    return (
      <p className="compare-pill">
        Прошлый раз: {metricSummary(previous)}
        <span>Сейчас: {formatDelta(weightDelta)} кг к прошлому весу</span>
      </p>
    );
  }

  function renderMetricFields() {
    if (!selected) return null;
    if (mode === "cardio") {
      return (
        <>
          <div className="form-grid">
            <label className="field">
              <span>Дистанция, км</span>
              <input className="plain-input" type="number" min="0" max="10000" step="0.01" value={metrics.distance} onChange={(event) => updateMetric("distance", event.target.value)} />
            </label>
            <label className="field">
              <span>Длительность, мин</span>
              <input className="plain-input" type="number" min="0" max="10000" step="0.1" value={metrics.duration} onChange={(event) => updateMetric("duration", event.target.value)} />
            </label>
          </div>
          <div className="form-grid">
            <label className="field">
              <span>Скорость, км/ч</span>
              <input className="plain-input" type="number" min="0" max="300" step="0.1" value={metrics.speed} onChange={(event) => updateMetric("speed", event.target.value)} placeholder={computedSpeed ? String(Math.round(computedSpeed * 10) / 10) : ""} />
            </label>
            <label className="field">
              <span>Темп, мин/км</span>
              <input className="plain-input" type="number" min="0" max="1000" step="0.1" value={metrics.pace} onChange={(event) => updateMetric("pace", event.target.value)} placeholder={computedPace ? String(Math.round(computedPace * 10) / 10) : ""} />
            </label>
          </div>
        </>
      );
    }
    if (mode === "timed") {
      return (
        <div className="form-grid">
          <label className="field">
            <span>Длительность, мин</span>
            <input className="plain-input" type="number" min="0" max="10000" step="0.1" value={metrics.duration} onChange={(event) => updateMetric("duration", event.target.value)} />
          </label>
          <label className="field">
            <span>Повторы/раунды</span>
            <input className="plain-input" type="number" min="1" max="1000" value={metrics.reps} onChange={(event) => updateMetric("reps", event.target.value)} />
          </label>
        </div>
      );
    }
    return (
      <div className="form-grid">
        <label className="field">
          <span>Вес, кг</span>
          <input className="plain-input" type="number" min="0" max="2000" step="0.5" value={metrics.weight} onChange={(event) => updateMetric("weight", event.target.value)} />
        </label>
        <label className="field">
          <span>Повторы</span>
          <input className="plain-input" type="number" min="1" max="1000" value={metrics.reps} onChange={(event) => updateMetric("reps", event.target.value)} />
        </label>
      </div>
    );
  }

  return (
    <section className="screen stack">
      <section className="surface">
        <div className="section-head">
          <h2>Планы</h2>
          <button type="button" onClick={() => setShowBuilder((value) => !value)} aria-label="Создать план">
            {showBuilder ? <X size={18} /> : <Plus size={18} />}
          </button>
        </div>

        <div className="plan-list">
          {plans.map((plan) => (
            <article className={activePlan?.id === plan.id ? "plan-card is-active" : "plan-card"} key={plan.id}>
              <div className="plan-card__head">
                <div>
                  <span>{plan.is_default ? "Готовый план" : "Мой план"}</span>
                  <strong>{plan.title}</strong>
                </div>
                <ClipboardList size={21} />
              </div>
              {plan.description ? <p>{plan.description}</p> : null}
              <div className="plan-chip-list">
                {plan.exercises.map((exercise) => (
                  <button
                    key={exercise.id}
                    type="button"
                    onClick={() => chooseExercise({
                      id: exercise.exercise_id,
                      name: exercise.exercise_name,
                      muscle_group: exercise.muscle_group,
                      load_type: exercise.load_type
                    })}
                  >
                    {exercise.exercise_name}
                  </button>
                ))}
              </div>
              <button className="small-action" type="button" disabled={saving} onClick={() => startPlan(plan.id)}>
                Начать план
              </button>
            </article>
          ))}
        </div>

        {showBuilder ? (
          <div className="plan-builder">
            <label className="field">
              <span>Название</span>
              <input className="plain-input" value={planTitle} onChange={(event) => setPlanTitle(event.target.value)} placeholder="Например, День ног" />
            </label>
            <label className="field">
              <span>Описание</span>
              <input className="plain-input" value={planDescription} onChange={(event) => setPlanDescription(event.target.value)} placeholder="Коротко для себя" />
            </label>
            <label className="field">
              <span>Упражнения</span>
              <div className="input-shell">
                <Search size={18} />
                <input value={planQuery} onChange={(event) => setPlanQuery(event.target.value)} placeholder="Найти упражнения" />
              </div>
            </label>
            <div className="product-list product-list--short">
              {planExercises.map((exercise) => {
                const checked = planExerciseIds.includes(exercise.id);
                return (
                  <button
                    key={exercise.id}
                    type="button"
                    className={checked ? "product-row is-active" : "product-row"}
                    onClick={() => togglePlanExercise(exercise.id)}
                  >
                    <span>{exercise.name}</span>
                    <strong>{checked ? <Check size={16} /> : exercise.muscle_group}</strong>
                  </button>
                );
              })}
            </div>
            <p className="hint">
              В плане: {selectedPlanExercises.length ? selectedPlanExercises.map((exercise) => exercise.name).join(", ") : "пока пусто"}
            </p>
            <IconButton onClick={createPlan} disabled={saving}>{saving ? "Сохраняю..." : "Сохранить план"}</IconButton>
          </div>
        ) : null}
      </section>

      <div className="surface workout-entry">
        <div className="section-head">
          <h2>{activeWorkout ? activeWorkout.title : "Новая тренировка"}</h2>
          {!activeWorkout ? (
            <button type="button" onClick={() => createWorkout(true)} aria-label="Создать тренировку">
              <Plus size={18} />
            </button>
          ) : null}
        </div>

        {!activeWorkout && !activePlan ? (
          <label className="field">
            <span>Название</span>
            <input className="plain-input" value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
        ) : null}

        {activePlan ? (
          <div className="plan-workout-list">
            <div className="section-head section-head--compact">
              <h2>{activePlan.title}</h2>
              <button type="button" onClick={() => setActivePlan(null)} aria-label="Закрыть план">
                <X size={18} />
              </button>
            </div>
            {activePlan.exercises.map((exercise) => (
              <button
                key={exercise.id}
                type="button"
                className={selected?.id === exercise.exercise_id ? "plan-exercise is-active" : "plan-exercise"}
                onClick={() => chooseExercise({
                  id: exercise.exercise_id,
                  name: exercise.exercise_name,
                  muscle_group: exercise.muscle_group,
                  load_type: exercise.load_type
                })}
              >
                <span>{exercise.exercise_name}</span>
                <strong>{exercise.target_sets} x {exercise.target_reps}</strong>
              </button>
            ))}
          </div>
        ) : (
          <>
            <label className="field">
              <span>Упражнение</span>
              <div className="input-shell">
                <Search size={18} />
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Жим, бег, планка" />
              </div>
            </label>

            <div className="product-list product-list--short">
              {exercises.map((exercise) => (
                <button
                  key={exercise.id}
                  type="button"
                  className={selected?.id === exercise.id ? "product-row is-active" : "product-row"}
                  onClick={() => chooseExercise(exercise)}
                >
                  <span>{exercise.name}</span>
                  <strong>{exercise.load_type}</strong>
                </button>
              ))}
            </div>
          </>
        )}

        {selected ? (
          <div className="selected-panel sticky-actions">
            <div className="selected-title">
              <div>
                <span>{selected.muscle_group} · {selected.load_type}</span>
                <strong>{selected.name}</strong>
              </div>
            </div>
            {renderPrevious()}
            {renderMetricFields()}
            <IconButton onClick={addSet} disabled={saving}>{saving ? "Сохраняю..." : "Добавить подход"}</IconButton>
          </div>
        ) : null}

        {error ? <p className="form-error">{error}</p> : null}
      </div>

      <section className="surface">
        <div className="section-head">
          <h2>Сегодня</h2>
          <span>{workouts?.total_sets || 0} подходов</span>
        </div>
        {(workouts?.workouts || []).length === 0 ? <p className="empty">Тренировка еще не начата.</p> : null}
        <div className="list">
          {(workouts?.workouts || []).map((workout) => (
            <div className="workout-mini" key={workout.id}>
              <div className="list-row">
                <div>
                  <span>{workout.sets.length} подходов</span>
                  <strong>{workout.title}</strong>
                </div>
              </div>
              {workout.sets.map((set) => (
                <div className="sub-row" key={set.id}>
                  <span>{set.set_index}. {set.exercise_name}</span>
                  <strong>{metricSummary(set)}</strong>
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}
