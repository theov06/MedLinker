// HomePage.jsx - Dashboard Summary
import { Activity, AlertCircle, TrendingUp, Users } from "lucide-react";

export function HomePage() {
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

    return (
        <div className="h-full overflow-y-auto p-6">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-[20px] font-semibold mb-1">Dashboard Overview</h1>
                <p className="text-[14px] text-secondary">Last updated: Today, 14:30</p>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-4 gap-4 mb-8">
                <StatCard
                    title="Total Facilities"
                    value="1,247"
                    icon={Activity}
                    change="+2.3%"
                    isPositive={true}
                />
                <StatCard
                    title="Critical Alerts"
                    value="18"
                    icon={AlertCircle}
                    change="+3"
                    isPositive={false}
                />
                <StatCard
                    title="Avg. Bed Occupancy"
                    value="78%"
                    icon={TrendingUp}
                    change="-1.2%"
                    isPositive={true}
                />
                <StatCard
                    title="Doctor Shortage"
                    value="127"
                    icon={Users}
                    change="+8"
                    isPositive={false}
                />
            </div>

            {/* Main Content - Two Panels */}
            <div className="grid grid-cols-2 gap-6">
                {/* Top Performing Facilities */}
                <div className="bg-panel border border-main">
                    <div className="p-4 border-b border-main">
                        <h2 className="text-[16px] font-semibold">Top Performing Facilities</h2>
                        <p className="text-[13px] text-secondary mt-1">Based on resource utilization score</p>
                    </div>
                    <div className="p-2">
                        <FacilityRow
                            rank="1"
                            name="Metropolitan General"
                            location="New York, NY"
                            metric="94/100"
                            status="Optimal"
                            isCritical={false}
                        />
                        <FacilityRow
                            rank="2"
                            name="Central Memorial"
                            location="Chicago, IL"
                            metric="91/100"
                            status="Optimal"
                            isCritical={false}
                        />
                        <FacilityRow
                            rank="3"
                            name="Westview Medical"
                            location="Los Angeles, CA"
                            metric="89/100"
                            status="Good"
                            isCritical={false}
                        />
                        <FacilityRow
                            rank="4"
                            name="Riverside Hospital"
                            location="Austin, TX"
                            metric="87/100"
                            status="Good"
                            isCritical={false}
                        />
                        <FacilityRow
                            rank="5"
                            name="Northwest Medical"
                            location="Seattle, WA"
                            metric="85/100"
                            status="Good"
                            isCritical={false}
                        />
                    </div>
                </div>

                {/* Facilities Needing Attention */}
                <div className="bg-panel border border-main">
                    <div className="p-4 border-b border-main">
                        <h2 className="text-[16px] font-semibold">Facilities Needing Attention</h2>
                        <p className="text-[13px] text-secondary mt-1">Immediate resource allocation required</p>
                    </div>
                    <div className="p-2">
                        <FacilityRow
                            rank="1"
                            name="Southside Clinic"
                            location="Detroit, MI"
                            metric="32/100"
                            status="Critical"
                            isCritical={true}
                        />
                        <FacilityRow
                            rank="2"
                            name="Valley Regional"
                            location="Phoenix, AZ"
                            metric="41/100"
                            status="Critical"
                            isCritical={true}
                        />
                        <FacilityRow
                            rank="3"
                            name="Appalachian Care"
                            location="Charleston, WV"
                            metric="45/100"
                            status="High Risk"
                            isCritical={true}
                        />
                        <FacilityRow
                            rank="4"
                            name="Midwest General"
                            location="Kansas City, MO"
                            metric="52/100"
                            status="High Risk"
                            isCritical={true}
                        />
                        <FacilityRow
                            rank="5"
                            name="Gulf Coast Medical"
                            location="New Orleans, LA"
                            metric="58/100"
                            status="Moderate"
                            isCritical={true}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}