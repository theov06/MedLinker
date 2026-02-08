import React from 'react';
import { Map, Grid } from 'lucide-react';

const FinderViewToggle = ({ viewMode, setViewMode }) => {
    return (
        <div className="flex border border-gray-300 w-fit">
            <button
                onClick={() => setViewMode('grid')}
                className={`flex items-center gap-2 px-4 py-2 text-sm ${viewMode === 'grid'
                    ? 'bg-[#2BB59A] text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'}`}
            >
                <Grid size={16} />
                Grid View
            </button>
            <button
                onClick={() => setViewMode('map')}
                className={`flex items-center gap-2 px-4 py-2 text-sm ${viewMode === 'map'
                    ? 'bg-[#2BB59A] text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'}`}
            >
                <Map size={16} />
                Map View
            </button>
        </div>
    );
};

export default FinderViewToggle;