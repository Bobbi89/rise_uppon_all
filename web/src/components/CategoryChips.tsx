import { categories } from "../data/products";
import type { CategoryFilter } from "../types";

type Props = {
  active: CategoryFilter;
  onChange: (category: CategoryFilter) => void;
};

export function CategoryChips({ active, onChange }: Props) {
  return (
    <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 py-1">
      {categories.map((category) => {
        const selected = active === category.id;
        return (
          <button
            key={category.id}
            onClick={() => onChange(category.id)}
            className={`shrink-0 rounded-full px-3.5 py-2 text-[13px] font-bold transition-colors ${
              selected
                ? "bg-olive-900 text-cream"
                : "border border-olive-100 bg-white text-olive-700"
            }`}
          >
            <span className="mr-1">{category.emoji}</span>
            {category.label}
          </button>
        );
      })}
    </div>
  );
}
