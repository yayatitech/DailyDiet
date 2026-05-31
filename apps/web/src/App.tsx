import { Link } from "react-router-dom";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  cellId,
  clearTokens,
  completionSet,
  DAY_KEYS,
  DAY_LABELS,
  DayKey,
  formatTodayHeading,
  getToken,
  MealItem,
  setTokens,
  TimeSlot,
  todayDayKey,
  weekForToday,
  WeekDetail,
  WeekSummary,
} from "./api";
import DayMealsView, { todayProgress } from "./DayMealsView";
import MealSlotEditor, { itemsToContent } from "./MealSlotEditor";
import MealSlotViewer from "./MealSlotViewer";

type LayoutMode = "today" | "week" | "day";
type InteractionMode = "view" | "edit";

const INTERACTION_MODE_KEY = "dailyDiet.interactionMode";

function loadInteractionMode(): InteractionMode {
  const stored = localStorage.getItem(INTERACTION_MODE_KEY);
  return stored === "edit" ? "edit" : "view";
}

function saveInteractionMode(mode: InteractionMode): void {
  localStorage.setItem(INTERACTION_MODE_KEY, mode);
}

function MealSlotCell({
  items,
  checked,
  isView,
  onToggle,
  onChange,
}: {
  items: MealItem[];
  checked: boolean;
  isView: boolean;
  onToggle: (checked: boolean) => void;
  onChange: (items: MealItem[]) => void;
}) {
  if (isView) {
    return (
      <label className="cell-label">
        <input type="checkbox" className="track-cb" checked={checked} onChange={(e) => onToggle(e.target.checked)} />
        <MealSlotViewer items={items} />
      </label>
    );
  }
  return <MealSlotEditor items={items} onChange={onChange} />;
}

export default function App() {
  const [weeks, setWeeks] = useState<WeekSummary[]>([]);
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [weekId, setWeekId] = useState("");
  const [week, setWeek] = useState<WeekDetail | null>(null);
  const [done, setDone] = useState<Set<string>>(new Set());
  const [layoutMode, setLayoutMode] = useState<LayoutMode>("today");
  const [interactionMode, setInteractionMode] = useState<InteractionMode>(loadInteractionMode);
  const [day, setDay] = useState<DayKey>("monday");
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isView = interactionMode === "view";

  const setMode = (mode: InteractionMode) => {
    setInteractionMode(mode);
    saveInteractionMode(mode);
  };

  const loadWeek = useCallback(async (id: string) => {
    const [w, c] = await Promise.all([api.week(id), api.completions(id)]);
    setWeek(w);
    setDone(completionSet(id, c));
    const today = todayDayKey(w);
    if (today) setDay(today);
    return w;
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const [wList, sList] = await Promise.all([api.weeks(), api.timeSlots()]);
        setWeeks(wList);
        setSlots(sList);
        const initial = weekForToday(wList);
        const initialId = initial?.id ?? wList[0]?.id ?? "";
        setWeekId(initialId);
        if (initialId) await loadWeek(initialId);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    })();
  }, [loadWeek]);

  useEffect(() => {
    if (!week || layoutMode !== "today") return;
    const today = todayDayKey(week);
    if (today) setDay(today);
  }, [week, layoutMode]);

  const onWeekChange = async (id: string) => {
    setWeekId(id);
    try {
      await loadWeek(id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const selectTodayLayout = () => {
    setLayoutMode("today");
    if (week) {
      const today = todayDayKey(week);
      if (today) setDay(today);
    }
  };

  const debouncedMeal = (d: DayKey, slot: number, items: MealItem[]) => {
    if (!week) return;
    setWeek({
      ...week,
      meals: {
        ...week.meals,
        [d]: week.meals[d].map((m, i) => (i === slot ? items : m)),
      },
    });
    const content = itemsToContent(items);
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      api.patchMeal(weekId, d, slot, content).catch((e) => setError(String(e)));
    }, 300);
  };

  const debouncedNotes = (notes: string) => {
    if (!week) return;
    setWeek({ ...week, notes });
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      api.patchNotes(weekId, notes).catch((e) => setError(String(e)));
    }, 300);
  };

  const toggleDone = async (d: DayKey, slot: number, checked: boolean) => {
    const id = cellId(weekId, d, slot);
    const next = new Set(done);
    if (checked) next.add(id);
    else next.delete(id);
    setDone(next);
    try {
      await api.toggleCompletion(weekId, d, slot, checked);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const today = week ? todayDayKey(week) : null;
  const activeDay = layoutMode === "today" ? (today ?? day) : day;
  const todayOutsideWeek = layoutMode === "today" && week && !today;

  if (error && !week) return <p className="error">{error}</p>;

  return (
    <>
      <header className="app-header">
        <div className="brand">
          <h1>DailyDiet</h1>
          <p className="subtitle">Weekly Meal Plan · v2</p>
        </div>
        <div className="controls">
          <label className="control">
            <span>Week</span>
            <select value={weekId} onChange={(e) => onWeekChange(e.target.value)}>
              {weeks.map((w) => (
                <option key={w.id} value={w.id}>{w.title}</option>
              ))}
            </select>
          </label>
          <div className="view-toggle">
            <button type="button" className={`view-btn ${layoutMode === "today" ? "active" : ""}`} onClick={selectTodayLayout}>Today</button>
            <button type="button" className={`view-btn ${layoutMode === "week" ? "active" : ""}`} onClick={() => setLayoutMode("week")}>Week grid</button>
            <button type="button" className={`view-btn ${layoutMode === "day" ? "active" : ""}`} onClick={() => setLayoutMode("day")}>Day view</button>
          </div>
          <div className="view-toggle">
            <button type="button" className={`view-btn ${interactionMode === "view" ? "active" : ""}`} onClick={() => setMode("view")}>View</button>
            <button type="button" className={`view-btn ${interactionMode === "edit" ? "active" : ""}`} onClick={() => setMode("edit")}>Edit</button>
          </div>
          <label className={`control ${layoutMode === "day" ? "" : "hidden"}`}>
            <span>Day</span>
            <select value={day} onChange={(e) => setDay(e.target.value as DayKey)}>
              {DAY_KEYS.map((d) => (
                <option key={d} value={d}>{DAY_LABELS[d]}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="actions">
          {!isView && (
            <>
              <button type="button" className="btn secondary" onClick={async () => { await api.resetWeek(weekId); await loadWeek(weekId); }}>Reset week</button>
              <button type="button" className="btn secondary" onClick={async () => { await api.clearCompletions(); setDone(new Set()); }}>Reset tracking</button>
              <Link to="/recipes" className="btn secondary">Recipes</Link>
            </>
          )}
          <button type="button" className="btn" onClick={async () => {
            const b = await api.export();
            const blob = new Blob([JSON.stringify(b, null, 2)], { type: "application/json" });
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = `dailydiet-${new Date().toISOString().slice(0, 10)}.json`;
            a.click();
          }}>Export JSON</button>
          {!isView && (
            <label className="btn secondary import-label">
              Import JSON
              <input type="file" accept="application/json" hidden onChange={async (e) => {
                const f = e.target.files?.[0];
                if (!f) return;
                const text = await f.text();
                await api.import(JSON.parse(text));
                await loadWeek(weekId);
              }} />
            </label>
          )}
        </div>
      </header>

      <div className="auth-panel">
        <label className="control"><span>Email</span><input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="optional login" /></label>
        <label className="control"><span>Password</span><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        <button type="button" className="btn secondary" onClick={async () => {
          const t = await api.login(email, password);
          setTokens(t.access_token, t.refresh_token);
          await loadWeek(weekId);
        }}>Login</button>
        <button type="button" className="btn secondary" onClick={async () => {
          const t = await api.register(email, password);
          setTokens(t.access_token, t.refresh_token);
          await loadWeek(weekId);
        }}>Register</button>
        {getToken() && <button type="button" className="btn secondary" onClick={() => { clearTokens(); }}>Logout</button>}
      </div>

      {error && <p className="error">{error}</p>}
      {week && (
        <main className={isView ? "" : "main-edit-mode"}>
          {layoutMode === "today" ? (
            <>
              <h2 className="week-title today-heading">{formatTodayHeading(today)}</h2>
              <p className="today-meta">{week.title}</p>
              {todayOutsideWeek ? (
                <p className="today-warning">Today is not in this week&apos;s date range. Select another week or use Day view.</p>
              ) : (
                <p className="today-progress">{todayProgress(done, weekId, activeDay, cellId)}/8 meals done</p>
              )}
            </>
          ) : (
            <h2 className="week-title">{week.title}</h2>
          )}

          {layoutMode === "week" ? (
            <div className="grid-wrap">
              <table className="meal-grid">
                <thead>
                  <tr>
                    <th>Time slot</th>
                    {DAY_KEYS.map((d) => (
                      <th key={d} className={today === d ? "col-today" : ""}>{DAY_LABELS[d]}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Array.from({ length: 8 }, (_, slot) => (
                    <tr key={slot}>
                      <th className="slot-header" scope="row">
                        {slots[slot]?.label ?? `Meal ${slot + 1}`}
                        <span className="slot-time">{slots[slot]?.time ?? ""}</span>
                      </th>
                      {DAY_KEYS.map((d) => {
                        const cid = cellId(weekId, d, slot);
                        const checked = done.has(cid);
                        return (
                          <td key={d} className={`meal-cell${today === d ? " col-today" : ""}${checked ? " cell-done" : ""}`}>
                            <MealSlotCell
                              items={week.meals[d][slot] ?? []}
                              checked={checked}
                              isView={isView}
                              onToggle={(c) => toggleDone(d, slot, c)}
                              onChange={(items) => debouncedMeal(d, slot, items)}
                            />
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <DayMealsView
              day={activeDay}
              weekMeals={week.meals[activeDay] ?? []}
              slots={slots}
              weekId={weekId}
              done={done}
              isView={isView}
              cellId={cellId}
              onToggle={(slot, c) => toggleDone(activeDay, slot, c)}
              onChange={(slot, items) => debouncedMeal(activeDay, slot, items)}
            />
          )}

          <section className="notes-section">
            <label htmlFor="week-notes">Notes</label>
            {isView ? (
              <p id="week-notes" className="week-notes-readonly">{week.notes || "—"}</p>
            ) : (
              <textarea id="week-notes" className="week-notes" rows={3} value={week.notes} onChange={(e) => debouncedNotes(e.target.value)} />
            )}
          </section>
        </main>
      )}
    </>
  );
}
