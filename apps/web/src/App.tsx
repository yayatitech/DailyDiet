import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  cellId,
  clearTokens,
  DAY_KEYS,
  DAY_LABELS,
  DayKey,
  getToken,
  MealItem,
  setTokens,
  TimeSlot,
  todayDayKey,
  WeekDetail,
  WeekSummary,
} from "./api";
import MealSlotEditor, { itemsToContent } from "./MealSlotEditor";

type ViewMode = "week" | "day";

function completionSet(
  weekId: string,
  rows: { day: DayKey; slot_index: number }[]
): Set<string> {
  return new Set(rows.map((r) => cellId(weekId, r.day, r.slot_index)));
}

export default function App() {
  const [weeks, setWeeks] = useState<WeekSummary[]>([]);
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [weekId, setWeekId] = useState("");
  const [week, setWeek] = useState<WeekDetail | null>(null);
  const [done, setDone] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<ViewMode>("week");
  const [day, setDay] = useState<DayKey>("monday");
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadWeek = useCallback(async (id: string) => {
    const [w, c] = await Promise.all([api.week(id), api.completions(id)]);
    setWeek(w);
    setDone(completionSet(id, c));
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const [wList, sList] = await Promise.all([api.weeks(), api.timeSlots()]);
        setWeeks(wList);
        setSlots(sList);
        const first = wList[0]?.id ?? "";
        setWeekId(first);
        if (first) await loadWeek(first);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    })();
  }, [loadWeek]);

  const onWeekChange = async (id: string) => {
    setWeekId(id);
    try {
      await loadWeek(id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
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

  if (error && !week) return <p className="error">{error}</p>;

  return (
    <>
      <header className="app-header">
        <div className="brand">
          <h1>DailyDiet</h1>
          <p className="subtitle">Fitelo Weekly Meal Plan · v2</p>
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
            <button type="button" className={`view-btn ${viewMode === "week" ? "active" : ""}`} onClick={() => setViewMode("week")}>Week grid</button>
            <button type="button" className={`view-btn ${viewMode === "day" ? "active" : ""}`} onClick={() => setViewMode("day")}>Day view</button>
          </div>
          <label className={`control ${viewMode === "day" ? "" : "hidden"}`}>
            <span>Day</span>
            <select value={day} onChange={(e) => setDay(e.target.value as DayKey)}>
              {DAY_KEYS.map((d) => (
                <option key={d} value={d}>{DAY_LABELS[d]}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="actions">
          <button type="button" className="btn secondary" onClick={async () => { await api.resetWeek(weekId); await loadWeek(weekId); }}>Reset week</button>
          <button type="button" className="btn secondary" onClick={async () => { await api.clearCompletions(); setDone(new Set()); }}>Reset tracking</button>
          <button type="button" className="btn" onClick={async () => {
            const b = await api.export();
            const blob = new Blob([JSON.stringify(b, null, 2)], { type: "application/json" });
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = `dailydiet-${new Date().toISOString().slice(0, 10)}.json`;
            a.click();
          }}>Export JSON</button>
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
        <main>
          <h2 className="week-title">{week.title}</h2>
          {viewMode === "week" ? (
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
                            <label className="cell-label">
                              <input type="checkbox" className="track-cb" checked={checked} onChange={(e) => toggleDone(d, slot, e.target.checked)} />
                              <MealSlotEditor
                                items={week.meals[d][slot] ?? []}
                                onChange={(items) => debouncedMeal(d, slot, items)}
                              />
                            </label>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="day-view">
              {Array.from({ length: 8 }, (_, slot) => {
                const cid = cellId(weekId, day, slot);
                const checked = done.has(cid);
                return (
                  <article key={slot} className={`day-slot${checked ? " cell-done" : ""}`}>
                    <header className="day-slot-header">
                      <span>{slots[slot]?.label ?? `Meal ${slot + 1}`}</span>
                      <span className="day-slot-time">{slots[slot]?.time ?? ""}</span>
                    </header>
                    <label className="cell-label">
                      <input type="checkbox" className="track-cb" checked={checked} onChange={(e) => toggleDone(day, slot, e.target.checked)} />
                      <MealSlotEditor
                        items={week.meals[day][slot] ?? []}
                        onChange={(items) => debouncedMeal(day, slot, items)}
                      />
                    </label>
                  </article>
                );
              })}
            </div>
          )}
          <section className="notes-section">
            <label htmlFor="week-notes">Notes</label>
            <textarea id="week-notes" className="week-notes" rows={3} value={week.notes} onChange={(e) => debouncedNotes(e.target.value)} />
          </section>
        </main>
      )}
    </>
  );
}
