"use client";

import { useEffect, useState } from "react";
import { usePlaceSearch } from "@/lib/geocoding";
import type { PlaceResultResponse } from "@/lib/types";

interface Props {
  value: string;
  onChange: (text: string) => void;
  onSelect: (place: PlaceResultResponse) => void;
  disabled?: boolean;
}

/**
 * Debounced place-name search with a results dropdown. Selecting a
 * result is the only way this component communicates a resolved
 * place — free-typed text alone never becomes coordinates, since that
 * would silently submit unresolved/wrong data.
 */
export function BirthPlaceSearch({ value, onChange, onSelect, disabled }: Props) {
  const [debounced, setDebounced] = useState(value);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), 400);
    return () => clearTimeout(timer);
  }, [value]);

  const { data, isFetching, isError } = usePlaceSearch(debounced);
  const results = data?.results ?? [];

  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        onBlur={() => setIsOpen(false)}
        placeholder="Search a city, e.g. Pune, Maharashtra, India"
        className="field-input"
        disabled={disabled}
        autoComplete="off"
      />

      {isFetching && (
        <span className="absolute right-3 top-1/2 -translate-y-1/2">
          <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-amber-400 border-t-transparent" />
        </span>
      )}

      {isOpen && debounced.trim().length >= 2 && (
        <div className="absolute z-20 mt-1 w-full overflow-hidden rounded-lg border border-white/10 bg-cosmos-900 shadow-xl">
          {results.length > 0 ? (
            <ul>
              {results.map((place, i) => (
                <li key={`${place.latitude}-${place.longitude}-${i}`}>
                  <button
                    type="button"
                    // onMouseDown (not onClick) fires before the input's
                    // onBlur closes the dropdown, so the selection isn't
                    // lost to a race between the two events.
                    onMouseDown={(e) => {
                      e.preventDefault();
                      onSelect(place);
                      setIsOpen(false);
                    }}
                    className="block w-full px-4 py-2 text-left text-sm text-slate-200 hover:bg-white/10"
                  >
                    {place.display_name}
                  </button>
                </li>
              ))}
            </ul>
          ) : !isFetching ? (
            <p className="px-4 py-2 text-sm text-slate-500">
              {isError ? "Place search is temporarily unavailable." : "No matching places found."}
            </p>
          ) : null}
        </div>
      )}
    </div>
  );
}
