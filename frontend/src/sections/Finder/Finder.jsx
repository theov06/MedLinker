// src/sections/Finder/Finder.jsx
import { useState, useEffect, useCallback } from "react";
import { Search, MapPin, Grid3x3, AlertCircle, Loader2, RefreshCw } from "lucide-react";
import FacilityCard from "./components/FacilityCard";
import FilterBar from "./components/FilterBar";
import MapView from "./components/MapView";
import { apiService } from "../../services/api";
import { transformFacility, transformRegion } from "../../utils/dataTransformers";

export function Finder() {
    const [viewMode, setViewMode] = useState('map');
    const [selectedFilters, setSelectedFilters] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedFacility, setSelectedFacility] = useState(null);

    // Backend states
    const [facilities, setFacilities] = useState([]);
    const [regions, setRegions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [apiHealth, setApiHealth] = useState(false);

    // Check API health on mount
    useEffect(() => {
        checkApiHealth();
    }, []);

    // Load data when API is healthy
    useEffect(() => {
        if (apiHealth) {
            loadData();
        }
    }, [apiHealth]);

    const checkApiHealth = async () => {
        try {
            await apiService.checkHealth();
            setApiHealth(true);
            setError(null);
        } catch (error) {
            setApiHealth(false);
            setError('Backend API is not available. Please ensure the server is running on http://localhost:8000');
            console.error('API health check failed:', error);
        }
    };

    const loadData = async () => {
        setLoading(true);
        setError(null);

        try {
            // Load facilities and regions in parallel
            const [facilitiesData, regionsData] = await Promise.all([
                apiService.getFacilities(),
                apiService.getRegions()
            ]);

            // Transform data for frontend
            const transformedFacilities = facilitiesData.map(transformFacility);
            const transformedRegions = regionsData.map(transformRegion);

            setFacilities(transformedFacilities);
            setRegions(transformedRegions);

        } catch (error) {
            setError(`Failed to load data: ${error.message}`);
            console.error('Data loading error:', error);

            // Fallback to mock data if API fails
            if (error.message.includes('Facilities data not found')) {
                setError('No data available. Please run data processing first.');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleAskQuestion = async (question) => {
        try {
            const result = await apiService.askQuestion(question);
            console.log('AI Response:', result);
            // You can display this in a modal or notification
            alert(`AI Answer: ${result.answer}`);
        } catch (error) {
            console.error('Ask question error:', error);
            alert(`Error: ${error.message}`);
        }
    };

    // Filter facilities based on search and selected filters
    const filteredFacilities = facilities.filter(facility => {
        // Search filter
        const matchesSearch = searchQuery === '' ||
            facility.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            facility.specialty.toLowerCase().includes(searchQuery.toLowerCase()) ||
            facility.equipment.some(eq => eq.toLowerCase().includes(searchQuery.toLowerCase()));

        // Filter by selected categories
        const matchesFilters = selectedFilters.length === 0 ||
            selectedFilters.some(filter => {
                if (filter.category === 'equipment') {
                    return facility.equipment.some(eq =>
                        eq.toLowerCase().includes(filter.label.toLowerCase())
                    );
                }
                if (filter.category === 'specialty') {
                    return facility.specialties.some(sp =>
                        sp.toLowerCase().includes(filter.label.toLowerCase())
                    );
                }
                if (filter.category === 'status') {
                    return facility.status === filter.label.toLowerCase();
                }
                if (filter.category === 'confidence') {
                    return facility.confidence === filter.label.toUpperCase();
                }
                return false;
            });

        return matchesSearch && matchesFilters;
    });

    // Add confidence filter options
    const confidenceOptions = [
        { label: 'High Confidence', icon: AlertCircle },
        { label: 'Medium Confidence', icon: AlertCircle },
        { label: 'Low Confidence', icon: AlertCircle }
    ];

    if (loading) {
        return (
            <div className="h-full flex flex-col items-center justify-center p-6">
                <Loader2 className="h-8 w-8 text-primary animate-spin mb-4" />
                <p className="text-[14px] text-secondary">Loading healthcare facilities...</p>
                <p className="text-[12px] text-secondary mt-1">Connecting to backend API</p>
            </div>
        );
    }

    if (error && !apiHealth) {
        return (
            <div className="h-full flex flex-col items-center justify-center p-6">
                <AlertCircle className="h-12 w-12 text-rose-500 mb-4" />
                <h3 className="text-[16px] font-semibold mb-2">Backend Unavailable</h3>
                <p className="text-[14px] text-secondary text-center max-w-md mb-4">
                    {error}
                </p>
                <button
                    onClick={checkApiHealth}
                    className="px-4 py-2 bg-primary text-white text-[13px] font-medium flex items-center gap-2 hover-primary transition-colors duration-150"
                >
                    <RefreshCw size={14} />
                    Retry Connection
                </button>
                <div className="mt-6 p-4 bg-slate-50 border border-main rounded-sm">
                    <p className="text-[12px] text-secondary mb-2">To start the backend:</p>
                    <code className="text-[11px] bg-white p-2 border border-soft rounded-sm block">
                        uvicorn medlinker_ai.api:app --reload
                    </code>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex flex-col items-center justify-center p-6">
                <AlertCircle className="h-12 w-12 text-amber-500 mb-4" />
                <h3 className="text-[16px] font-semibold mb-2">Data Loading Error</h3>
                <p className="text-[14px] text-secondary text-center max-w-md mb-4">
                    {error}
                </p>
                <button
                    onClick={loadData}
                    className="px-4 py-2 bg-primary text-white text-[13px] font-medium flex items-center gap-2 hover-primary transition-colors duration-150"
                >
                    <RefreshCw size={14} />
                    Retry Loading Data
                </button>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col p-6">
            {/* Header */}
            <div className="mb-6">
                <div className="flex justify-between items-start mb-2">
                    <div>
                        <h1 className="text-[20px] font-semibold">Healthcare Facility Finder</h1>
                        <div className="flex items-center gap-4 mt-1">
                            <div className="flex items-center gap-2 text-[13px]">
                                <div className="flex items-center gap-1">
                                    <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                                    <span className="text-secondary">Optimal: {facilities.filter(f => f.status === 'optimal').length}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                    <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                                    <span className="text-secondary">Moderate: {facilities.filter(f => f.status === 'moderate').length}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                    <div className="w-2 h-2 rounded-full bg-rose-500"></div>
                                    <span className="text-secondary">Critical: {facilities.filter(f => f.status === 'critical').length}</span>
                                </div>
                            </div>
                            {apiHealth && (
                                <div className="flex items-center gap-2 text-[12px]">
                                    <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                                    <span className="text-secondary">API Connected</span>
                                </div>
                            )}
                        </div>
                    </div>

                    <button
                        onClick={() => handleAskQuestion('Show me facilities that need urgent attention')}
                        className="px-4 py-2 bg-primary text-white text-[13px] font-medium hover-primary transition-colors duration-150"
                    >
                        Ask AI Assistant
                    </button>
                </div>

                {/* Search Bar */}
                <div className="relative mb-4">
                    <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-placeholder" size={18} />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search facilities by name, specialty, equipment..."
                        className="w-full pl-12 pr-4 py-3 border border-main bg-white text-[14px] focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                    />
                </div>

                {/* Filter Row */}
                <div className="flex items-center justify-between mb-4">
                    <FilterBar
                        selectedFilters={selectedFilters}
                        onFiltersChange={setSelectedFilters}
                        additionalFilters={confidenceOptions}
                    />
                    <div className="text-[13px] text-secondary">
                        {filteredFacilities.length} of {facilities.length} facilities • {regions.length} regions
                    </div>
                </div>

                {/* View Controls */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <span className="text-[13px] text-secondary">View mode:</span>
                        <div className="flex border border-main">
                            <button
                                onClick={() => setViewMode('map')}
                                className={`px-4 py-2 text-[13px] font-medium flex items-center gap-2 transition-colors duration-150
                                    ${viewMode === 'map' ? 'bg-primary text-white' : 'bg-white text-secondary hover:bg-slate-50'}`}
                            >
                                <MapPin size={14} />
                                Map View
                            </button>
                            <button
                                onClick={() => setViewMode('grid')}
                                className={`px-4 py-2 text-[13px] font-medium flex items-center gap-2 transition-colors duration-150
                                    ${viewMode === 'grid' ? 'bg-primary text-white' : 'bg-white text-secondary hover:bg-slate-50'}`}
                            >
                                <Grid3x3 size={14} />
                                Grid View
                            </button>
                        </div>
                    </div>

                    {selectedFacility && (
                        <button
                            onClick={() => setSelectedFacility(null)}
                            className="px-3 py-1.5 border border-main text-[13px] hover:bg-slate-50 transition-colors duration-150"
                        >
                            Clear Selection
                        </button>
                    )}
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 overflow-hidden">
                {viewMode === 'map' ? (
                    /* Map View - Two Columns */
                    <div className="h-full flex gap-6">
                        {/* Left Column - Facility Cards */}
                        <div className="w-96 overflow-y-auto">
                            <div className="space-y-4">
                                {filteredFacilities.map((facility) => (
                                    <div
                                        key={facility.id}
                                        onClick={() => setSelectedFacility(facility)}
                                        className={`cursor-pointer transition-all duration-150
                                            ${selectedFacility?.id === facility.id ? 'ring-1 ring-primary' : ''}`}
                                    >
                                        <FacilityCard
                                            facility={facility}
                                            showConfidence={true}
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right Column - Map */}
                        <div className="flex-1">
                            <MapView
                                facilities={filteredFacilities}
                                selectedFacility={selectedFacility}
                                onSelectFacility={setSelectedFacility}
                            />
                        </div>
                    </div>
                ) : (
                    /* Grid View - Full Width */
                    <div className="overflow-y-auto">
                        <div className="grid grid-cols-3 gap-6">
                            {filteredFacilities.map((facility) => (
                                <div
                                    key={facility.id}
                                    onClick={() => setSelectedFacility(facility)}
                                    className="cursor-pointer"
                                >
                                    <FacilityCard
                                        facility={facility}
                                        showConfidence={true}
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Quick AI Question Bar */}
            <div className="mt-6 pt-4 border-t border-main">
                <div className="flex items-center gap-3">
                    <span className="text-[13px] text-secondary">Quick questions:</span>
                    <div className="flex gap-2">
                        {[
                            'Show critical facilities',
                            'Find facilities with surgery',
                            'Regions lacking ultrasound',
                            'High desert score areas'
                        ].map((question, index) => (
                            <button
                                key={index}
                                onClick={() => handleAskQuestion(question)}
                                className="px-3 py-1.5 border border-main text-[12px] hover:bg-slate-50 transition-colors duration-150"
                            >
                                {question}
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}