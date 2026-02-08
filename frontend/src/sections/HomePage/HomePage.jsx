// HomePage.jsx - Dashboard Summary
import { Activity, AlertCircle, TrendingUp, Users } from "lucide-react";
import { useState, useEffect } from "react";
import { apiService } from "../../services/api";

export function HomePage() {
    const [facilities, setFacilities] = useState([]);
    const [regions, setRegions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({
        totalFacilities: 0,
        criticalRegions: 0,
        avgDesertScore: 0,
        missingServices: 0
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [facilitiesData, regionsData] = await Promise.all([
                apiService.getFacilities(),
                apiService.getRegions()
            ]);

            setFacilities(facilitiesData);
            setRegions(regionsData);

            // Calculate stats
            const criticalRegions = regionsData.filter(r => r.desert_score >= 70).length;
            const avgDesertScore = regionsData.length > 0
                ? Math.round(regionsData.reduce((sum, r) => sum + r.desert_score, 0) / regionsData.length)
                : 0;
            
            // Count unique missing services across all regions
            const allMissingServices = new Set();
            regionsData.forEach(r => {
                r.missing_critical?.forEach(service => allMissingServices.add(service));
            });

            setStats({
                totalFacilities: facilitiesData.length,
                criticalRegions,
                avgDesertScore,
                missingServices: allMissingServices.size
            });
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    const StatCard = ({ title, value, icon: Icon, change, isPositive }) => (
        <div className="bg-panel border border-main p-4">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-[13px] text-secondary mb-1">{title}</p>
                    <p className="text-[24px] font-semibold">{value}</p>
                    {change && (
                        <div className="flex items-center gap-1 mt-1">
                            <span className={`text-[12px] ${isPositive ? 'text-primary' : 'text-rose-600'}`}>
                                {isPositive ? '+' : ''}{change}
                            </span>
                            <span className="text-[12px] text-secondary">vs last month</span>
                        </div>
                    )}
                </div>
                <div className={`p-2 ${isPositive ? 'bg-primary-soft' : 'bg-rose-50'}`}>
                    <Icon size={20} className={isPositive ? 'text-primary' : 'text-rose-600'} />
                </div>
            </div>
        </div>
    );

    const FacilityRow = ({ rank, name, location, metric, status, isCritical }) => (
        <div className="flex items-center justify-between py-3 px-1 border-b border-soft last:border-b-0 hover:bg-slate-50/50 transition-colors duration-150">
            <div className="flex items-center gap-3">
                <div className={`w-6 h-6 flex items-center justify-center text-[12px] font-medium
          ${isCritical ? 'bg-rose-50 text-rose-700' : 'bg-primary-soft text-primary'}`}>
                    {rank}
                </div>
                <div>
                    <p className="text-[14px] font-medium">{name}</p>
                    <p className="text-[12px] text-secondary">{location}</p>
                </div>
            </div>
            <div className="text-right">
                <p className="text-[14px] font-medium">{metric}</p>
                <div className={`inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium mt-1
          ${isCritical ? 'bg-rose-50 text-rose-700' : 'bg-emerald-50 text-emerald-700'}`}>
                    <div className={`w-1.5 h-1.5 rounded-sm ${isCritical ? 'bg-rose-500' : 'bg-emerald-500'}`} />
                    {status}
                </div>
            </div>
        </div>
    );

    // Get top verified facilities
    const topFacilities = facilities
        .filter(f => f.status === 'VERIFIED')
        .slice(0, 5);

    // Get facilities needing attention (suspicious or incomplete)
    const needsAttention = facilities
        .filter(f => f.status === 'SUSPICIOUS' || f.status === 'INCOMPLETE')
        .slice(0, 5);

    // Get critical regions (high desert score)
    const criticalRegions = regions
        .filter(r => r.desert_score >= 70)
        .sort((a, b) => b.desert_score - a.desert_score)
        .slice(0, 5);

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center">
                <div className="text-center">
                    <div className="text-[16px] text-secondary">Loading dashboard...</div>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto p-6">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-[20px] font-semibold mb-1">Dashboard Overview</h1>
                <p className="text-[14px] text-secondary">Last updated: {new Date().toLocaleString()}</p>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-4 gap-4 mb-8">
                <StatCard
                    title="Total Facilities"
                    value={stats.totalFacilities}
                    icon={Activity}
                    isPositive={true}
                />
                <StatCard
                    title="Critical Regions"
                    value={stats.criticalRegions}
                    icon={AlertCircle}
                    isPositive={false}
                />
                <StatCard
                    title="Avg. Desert Score"
                    value={`${stats.avgDesertScore}%`}
                    icon={TrendingUp}
                    isPositive={stats.avgDesertScore < 50}
                />
                <StatCard
                    title="Missing Services"
                    value={stats.missingServices}
                    icon={Users}
                    isPositive={false}
                />
            </div>

            {/* Main Content - Two Panels */}
            <div className="grid grid-cols-2 gap-6">
                {/* Top Verified Facilities */}
                <div className="bg-panel border border-main">
                    <div className="p-4 border-b border-main">
                        <h2 className="text-[16px] font-semibold">Top Verified Facilities</h2>
                        <p className="text-[13px] text-secondary mt-1">Facilities with complete and verified data</p>
                    </div>
                    <div className="p-2">
                        {topFacilities.length > 0 ? (
                            topFacilities.map((facility, idx) => (
                                <FacilityRow
                                    key={facility.facility_id}
                                    rank={idx + 1}
                                    name={facility.facility_name}
                                    location={facility.location || `${facility.region}, ${facility.country}`}
                                    metric={facility.confidence}
                                    status="Verified"
                                    isCritical={false}
                                />
                            ))
                        ) : (
                            <div className="p-4 text-center text-secondary text-[14px]">
                                No verified facilities found
                            </div>
                        )}
                    </div>
                </div>

                {/* Facilities Needing Attention */}
                <div className="bg-panel border border-main">
                    <div className="p-4 border-b border-main">
                        <h2 className="text-[16px] font-semibold">Facilities Needing Attention</h2>
                        <p className="text-[13px] text-secondary mt-1">Incomplete or suspicious data requiring review</p>
                    </div>
                    <div className="p-2">
                        {needsAttention.length > 0 ? (
                            needsAttention.map((facility, idx) => (
                                <FacilityRow
                                    key={facility.facility_id}
                                    rank={idx + 1}
                                    name={facility.facility_name}
                                    location={facility.location || `${facility.region}, ${facility.country}`}
                                    metric={facility.confidence}
                                    status={facility.status === 'SUSPICIOUS' ? 'Suspicious' : 'Incomplete'}
                                    isCritical={true}
                                />
                            ))
                        ) : (
                            <div className="p-4 text-center text-secondary text-[14px]">
                                All facilities verified
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Critical Regions Section */}
            {criticalRegions.length > 0 && (
                <div className="mt-6">
                    <div className="bg-panel border border-main">
                        <div className="p-4 border-b border-main">
                            <h2 className="text-[16px] font-semibold">Critical Medical Desert Regions</h2>
                            <p className="text-[13px] text-secondary mt-1">Regions with highest healthcare gaps (desert score ≥ 70)</p>
                        </div>
                        <div className="p-2">
                            {criticalRegions.map((region, idx) => (
                                <FacilityRow
                                    key={`${region.country}-${region.region}`}
                                    rank={idx + 1}
                                    name={region.region}
                                    location={region.country}
                                    metric={`${region.desert_score}/100`}
                                    status={region.desert_score >= 80 ? 'Critical' : 'High Risk'}
                                    isCritical={true}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}