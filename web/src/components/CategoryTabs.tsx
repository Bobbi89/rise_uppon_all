import type { CategoryId } from "../types";
import { categories } from "../data/mockData";

type Props = {
  active: CategoryId;
  onChange: (category: CategoryId) => void;
};

export function CategoryTabs({ active, onChange }: Props) {
  return (
    <div className="flex gap-2 overflow-x-auto border-b border-olive-100 pb-3">
      {categories.map((category) => (
        <button
          key={category.id}
          onClick={() => onChange(category.id)}
          className={`shrink-0 rounded px-4 py-2 text-sm font-bold ${
            active === category.id
              ? "bg-olive-900 text-cream"
              : "bg-white text-olive-900 shadow-sm hover:bg-olive-50"
          }`}
        >
          <span className="hidden sm:inline">{category.label}</span>
          <span className="sm:hidden">{category.short}</span>
        </button>
      ))}
    </div>
  );
}
