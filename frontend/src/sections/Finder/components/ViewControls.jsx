// Finder/components/ViewControls.jsx
import { MapPin, Grid3x3 } from "lucide-react";

export default function ViewControls({ viewMode, onViewModeChange }) {
    return (
        <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
                <span className="text-[13px] text-secondary">View mode:</span>
                <div className="flex border border-main">
                    <button
                        onClick={() => onViewModeChange('map')}
                        className={`px-4 py-2 text-[13px] font-medium flex items-center gap-2 transition-colors duration-150
                            ${viewMode === 'map' ? 'bg-primary text-white' : 'bg-white text-secondary hover:bg-slate-50'}`}
                    >
                        <MapPin size={14} />
                        Map View
                    </button>
                    <button
                        onClick={() => onViewModeChange('grid')}
                        className={`px-4 py-2 text-[13px] font-medium flex items-center gap-2 transition-colors duration-150
                            ${viewMode === 'grid' ? 'bg-primary text-white' : 'bg-white text-secondary hover:bg-slate-50'}`}
                    >
                        <Grid3x3 size={14} />
                        Grid View
                    </button>
                </div>
            </div>
        </div>
    );
}