// Finder/constants/filterOptions.js
import { 
    Shield, Activity, Syringe, Heart, Brain, Users, 
    Thermometer, Star, AlertTriangle, CheckCircle, Clock, Building 
} from "lucide-react";
import { facilities } from "../data/facilities";

export const filterOptions = [
    {
        id: 'status',
        label: 'Status',
        icon: AlertTriangle,
        options: [
            { label: 'Optimal', icon: CheckCircle, count: facilities.filter(f => f.status === 'optimal').length },
            { label: 'Moderate', icon: Clock, count: facilities.filter(f => f.status === 'moderate').length },
            { label: 'Critical', icon: AlertTriangle, count: facilities.filter(f => f.status === 'critical').length }
        ]
    },
    {
        id: 'equipment',
        label: 'Equipment',
        icon: Activity,
        options: [
            { label: 'ICU Available', icon: Shield, count: facilities.filter(f => f.equipment.includes("ICU")).length },
            { label: 'MRI Available', icon: Activity, count: facilities.filter(f => f.equipment.includes("MRI")).length },
            { label: 'CT Scanner', icon: Activity, count: facilities.filter(f => f.equipment.includes("CT Scanner")).length },
            { label: 'Operating Rooms', icon: Syringe, count: facilities.filter(f => f.equipment.includes("Operating Rooms")).length },
            { label: 'Trauma Bay', icon: Shield, count: facilities.filter(f => f.equipment.includes("Trauma Bay")).length },
            { label: 'Helipad', icon: Activity, count: facilities.filter(f => f.equipment.includes("Helipad")).length },
            { label: 'Radiation', icon: Activity, count: facilities.filter(f => f.equipment.includes("Radiation")).length }
        ]
    },
    {
        id: 'specialty',
        label: 'Specialty',
        icon: Star,
        options: [
            { label: 'Cardiology', icon: Heart, count: facilities.filter(f => f.specialties.includes("Cardiology")).length },
            { label: 'Neurology', icon: Brain, count: facilities.filter(f => f.specialties.includes("Neurology")).length },
            { label: 'Pediatrics', icon: Users, count: facilities.filter(f => f.specialties.includes("Pediatrics")).length },
            { label: 'Emergency', icon: Thermometer, count: facilities.filter(f => f.specialties.includes("Emergency")).length },
            { label: 'Oncology', icon: Activity, count: facilities.filter(f => f.specialties.includes("Oncology")).length },
            { label: 'Orthopedics', icon: Shield, count: facilities.filter(f => f.specialties.includes("Orthopedics")).length },
            { label: 'Surgery', icon: Syringe, count: facilities.filter(f => f.specialties.includes("Surgery")).length }
        ]
    },
    {
        id: 'capacity',
        label: 'Capacity',
        icon: Users,
        options: [
            { label: 'High Capacity (300+)', icon: Building, count: facilities.filter(f => f.patientCapacity >= 300).length },
            { label: 'Medium Capacity (150-299)', icon: Building, count: facilities.filter(f => f.patientCapacity >= 150 && f.patientCapacity < 300).length },
            { label: 'Low Capacity (<150)', icon: Building, count: facilities.filter(f => f.patientCapacity < 150).length }
        ]
    }
];