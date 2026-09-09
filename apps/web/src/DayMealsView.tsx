import { DayKey, MealItem, RecipeSummary, TimeSlot } from "./api";
import MealSlotEditor from "./MealSlotEditor";
import MealSlotViewer from "./MealSlotViewer";

type Props = {
  day: DayKey;
  weekMeals: MealItem[][];
  slots: TimeSlot[];
  isView: boolean;
  recipes: RecipeSummary[];
  onChange: (slot: number, items: MealItem[]) => void;
};

function MealSlotCell({
  items,
  isView,
  recipes,
  onChange,
}: {
  items: MealItem[];
  isView: boolean;
  recipes: RecipeSummary[];
  onChange: (items: MealItem[]) => void;
}) {
  if (isView) {
    return <MealSlotViewer items={items} />;
  }
  return <MealSlotEditor items={items} recipes={recipes} onChange={onChange} />;
}

export default function DayMealsView({
  weekMeals,
  slots,
  isView,
  recipes,
  onChange,
}: Props) {
  return (
    <div className="day-view">
      {Array.from({ length: 8 }, (_, slot) => (
        <article key={slot} className="day-slot">
          <header className="day-slot-header">
            <span>{slots[slot]?.label ?? `Meal ${slot + 1}`}</span>
            <span className="day-slot-time">{slots[slot]?.time ?? ""}</span>
          </header>
          <MealSlotCell
            items={weekMeals[slot] ?? []}
            isView={isView}
            recipes={recipes}
            onChange={(items) => onChange(slot, items)}
          />
        </article>
      ))}
    </div>
  );
}
