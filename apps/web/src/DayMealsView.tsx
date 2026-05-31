import { DayKey, MealItem, RecipeSummary, TimeSlot } from "./api";
import MealSlotEditor from "./MealSlotEditor";
import MealSlotViewer from "./MealSlotViewer";

type Props = {
  day: DayKey;
  weekMeals: MealItem[][];
  slots: TimeSlot[];
  weekId: string;
  done: Set<string>;
  isView: boolean;
  recipes: RecipeSummary[];
  cellId: (weekId: string, day: DayKey, slot: number) => string;
  onToggle: (slot: number, checked: boolean) => void;
  onChange: (slot: number, items: MealItem[]) => void;
};

function MealSlotCell({
  items,
  checked,
  isView,
  recipes,
  onToggle,
  onChange,
}: {
  items: MealItem[];
  checked: boolean;
  isView: boolean;
  recipes: RecipeSummary[];
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
  return <MealSlotEditor items={items} recipes={recipes} onChange={onChange} />;
}

export default function DayMealsView({
  day,
  weekMeals,
  slots,
  weekId,
  done,
  isView,
  recipes,
  cellId,
  onToggle,
  onChange,
}: Props) {
  return (
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
            <MealSlotCell
              items={weekMeals[slot] ?? []}
              checked={checked}
              isView={isView}
              recipes={recipes}
              onToggle={(c) => onToggle(slot, c)}
              onChange={(items) => onChange(slot, items)}
            />
          </article>
        );
      })}
    </div>
  );
}

export function todayProgress(done: Set<string>, weekId: string, day: DayKey, cellIdFn: Props["cellId"]): number {
  return Array.from({ length: 8 }, (_, slot) => done.has(cellIdFn(weekId, day, slot))).filter(Boolean).length;
}
