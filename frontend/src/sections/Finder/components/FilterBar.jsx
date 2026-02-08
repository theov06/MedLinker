// src/sections/Finder/components/FilterBar.jsx
import { useState } from "react";
import {
    Filter, ChevronDown, AlertCircle, Activity,
    Star, Users, Shield, CheckCircle
} from "lucide-react";
import { filterOptions } from "../constants/filterOptions";

export default function FilterBar({
    selectedFilters,
    onFiltersChange,
    additionalFilters = []
}) {
    const [activeDropdown, setActiveDropdown] = useState(null);

    const allFilterOptions = [
        ...filterOptions,
        ...(additionalFilters.length > 0 ? [{
            id: 'confidence',
            label: 'Confidence',
            icon: Shield,
            options: additionalFilters
        }] : [])
    ];

    const handleFilterToggle = (category, filter) => {
        const filterKey = `${category}_${filter.label}`;

        if (selectedFilters.some(f => f.key === filterKey)) {
            onFiltersChange(selectedFilters.filter(f => f.key !== filterKey));
        } else {
            onFiltersChange([
                ...selectedFilters,
                {
                    key: filterKey,
                    category,
                    label: filter.label,
                    icon: filter.icon
                }
            ]);
        }
    };

    const clearAllFilters = () => {
        onFiltersChange([]);
        setActiveDropdown(null);
    };

    return (
        <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
                <Filter size={16} className="text-secondary" />
                <span className="text-[13px] text-secondary">Filter by:</span>
            </div>

            {/* Filter Buttons Row */}
            <div className="flex items-center gap-2">
                {allFilterOptions.map((category) => (
                    <div key={category.id} className="relative">
                        <button
                            onClick={() => setActiveDropdown(activeDropdown === category.id ? null : category.id)}
                            className="px-4 py-2 border border-main bg-white text-[13px] flex items-center gap-2 hover:bg-slate-50 transition-colors duration-150"
                        >
                            <category.icon size={14} />
                            <span>{category.label}</span>
                            <ChevronDown size={14} className={`transition-transform duration-150 ${activeDropdown === category.id ? 'rotate-180' : ''}`} />
                        </button>

                        {/* Dropdown Menu */}
                        {activeDropdown === category.id && (
                            <div className="absolute top-full left-0 mt-1 w-56 bg-panel border border-main shadow-lg z-50 rounded-lg overflow-hidden">
                                <div className="p-3 max-h-80 overflow-y-auto">
                                    <div className="space-y-2">
                                        {category.options.map((option, idx) => {
                                            const filterKey = `${category.id}_${option.label}`;
                                            const isSelected = selectedFilters.some(f => f.key === filterKey);
                                            const Icon = option.icon;

                                            return (
                                                <button
                                                    key={idx}
                                                    onClick={() => handleFilterToggle(category.id, option)}
                                                    className={`w-full text-left px-3 py-2 text-[13px] flex items-center justify-between rounded-sm transition-colors duration-150
                                                        ${isSelected ? 'bg-primary-soft text-primary' : 'hover:bg-slate-50'}`}
                                                >
                                                    <div className="flex items-center gap-2">
                                                        <Icon size={14} />
                                                        <span>{option.label}</span>
                                                    </div>
                                                    {option.count !== undefined && (
                                                        <span className="text-[11px] text-secondary bg-slate-100 px-2 py-0.5 rounded">
                                                            {option.count}
                                                        </span>
                                                    )}
                                                </button>
                                            );
                                        })}
                                    </div>

                                    <div className="mt-3 pt-3 border-t border-soft">
                                        <button
                                            onClick={clearAllFilters}
                                            className="w-full px-3 py-1.5 text-[12px] text-primary hover:text-primary-hover text-center"
                                        >
                                            Clear all filters
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Active filters count badge */}
            {selectedFilters.length > 0 && (
                <div className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-primary text-white text-[12px] font-medium rounded-sm">
                        {selectedFilters.length} active
                    </span>
                    <button
                        onClick={clearAllFilters}
                        className="text-[12px] text-primary hover:text-primary-hover"
                    >
                        Clear all
                    </button>
                </div>
            )}
        </div>
    );
}