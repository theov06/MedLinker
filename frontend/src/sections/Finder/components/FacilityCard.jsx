// src/sections/Finder/components/FacilityCard.jsx
import { MapPin, Star, Users, Thermometer, Shield, AlertCircle, CheckCircle } from "lucide-react";

export default function FacilityCard({ facility, showConfidence = false }) {
    const {
        id,
        name,
        specialty,
        rating,
        distance,
        status,
        doctors,
        patientCapacity,
        waitTime,
        equipment = [],
        specialties = [],
        lastUpdated,
        confidence,
        citationsCount = 0
    } = facility;

    const confidenceIcon = confidence === 'HIGH' ? CheckCircle :
        confidence === 'MEDIUM' ? AlertCircle :
            Shield;

    const confidenceColor = confidence === 'HIGH' ? 'text-emerald-600' :
        confidence === 'MEDIUM' ? 'text-amber-600' :
            'text-rose-600';

    return (
        <div className="bg-panel border border-main rounded-lg overflow-hidden hover:border-primary transition-colors duration-150">
            {/* Header with confidence badge */}
            <div className="flex items-center justify-between px-4 pt-3 pb-2 border-b border-soft bg-slate-50">
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${status === 'optimal' ? 'bg-emerald-500' :
                            status === 'critical' ? 'bg-rose-500' :
                                'bg-amber-500'
                        }`}></div>
                    <span className="text-[12px] font-medium text-secondary">ID: {id}</span>
                </div>

                {showConfidence && confidence && (
                    <div className="flex items-center gap-1">
                        <confidenceIcon size={12} className={confidenceColor} />
                        <span className={`text-[11px] font-medium ${confidenceColor}`}>
                            {confidence} Confidence
                        </span>
                    </div>
                )}
            </div>

            <div className="p-4">
                <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                        <h3 className="text-[15px] font-semibold mb-1 truncate">{name}</h3>
                        <p className="text-[13px] text-secondary mb-2">{specialty}</p>

                        {/* Equipment tags */}
                        <div className="flex flex-wrap gap-1 mb-2">
                            {equipment.slice(0, 3).map((item, idx) => (
                                <span key={idx} className="px-2 py-0.5 bg-slate-100 text-[10px] text-secondary">
                                    {item}
                                </span>
                            ))}
                            {equipment.length > 3 && (
                                <span className="px-2 py-0.5 bg-slate-100 text-[10px] text-secondary">
                                    +{equipment.length - 3}
                                </span>
                            )}
                        </div>
                    </div>

                    <div className="flex flex-col items-end">
                        <div className="flex items-center gap-1 mb-1">
                            <Star size={14} className="text-secondary" />
                            <span className="text-[14px] font-medium">{rating.toFixed(1)}</span>
                        </div>
                        <div className="flex items-center gap-1 text-[12px] text-secondary">
                            <MapPin size={12} />
                            <span>{distance}</span>
                        </div>
                    </div>
                </div>

                {/* Stats row */}
                <div className="flex items-center justify-between mb-4 px-1">
                    <div className="flex flex-col items-center">
                        <Users size={16} className="text-secondary mb-1" />
                        <div className="text-[13px] font-medium">{doctors}</div>
                        <div className="text-[11px] text-secondary">Doctors</div>
                    </div>

                    <div className="flex flex-col items-center">
                        <div className="w-5 h-5 bg-primary flex items-center justify-center rounded-sm mb-1">
                            <Users size={12} className="text-white" />
                        </div>
                        <div className="text-[13px] font-medium">{patientCapacity}</div>
                        <div className="text-[11px] text-secondary">Capacity</div>
                    </div>

                    <div className="flex flex-col items-center">
                        <Thermometer size={16} className="text-secondary mb-1" />
                        <div className="text-[13px] font-medium">{waitTime}</div>
                        <div className="text-[11px] text-secondary">Wait Time</div>
                    </div>

                    <div className="flex flex-col items-center">
                        <Shield size={16} className="text-secondary mb-1" />
                        <div className="text-[13px] font-medium">{citationsCount}</div>
                        <div className="text-[11px] text-secondary">Sources</div>
                    </div>
                </div>

                {/* Status badge */}
                <div className="flex items-center justify-between pt-3 border-t border-soft">
                    <div className="flex items-center gap-2">
                        <div className={`px-2 py-1 text-[11px] font-semibold text-white
                            ${status === 'optimal' ? 'bg-emerald-600' :
                                status === 'critical' ? 'bg-rose-600' :
                                    'bg-amber-600'}`}>
                            {status.toUpperCase()}
                        </div>
                        <div className="text-[11px] text-secondary">
                            Updated {lastUpdated}
                        </div>
                    </div>

                    <button className="px-3 py-1.5 bg-primary text-white text-[12px] font-medium hover-primary transition-colors duration-150">
                        View Details
                    </button>
                </div>
            </div>
        </div>
    );
}