import { Home, Search, FileText, User, MessageSquare, Database } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";

const STORAGE_KEY = 'medlinker_user_profile';

export function Sidebar() {
    const navigate = useNavigate();
    const currentPath = window.location.pathname.split('/').pop() || 'home';
    
    const [userProfile, setUserProfile] = useState({
        firstName: 'Sarah',
        lastName: 'Mitchell',
        email: 'sarah.mitchell@email.com'
    });

    // Load profile from localStorage
    useEffect(() => {
        loadProfile();
        
        // Listen for storage changes (when profile is saved)
        const handleStorageChange = () => {
            loadProfile();
        };
        
        window.addEventListener('storage', handleStorageChange);
        // Also listen for custom event from same window
        window.addEventListener('profileUpdated', handleStorageChange);
        
        return () => {
            window.removeEventListener('storage', handleStorageChange);
            window.removeEventListener('profileUpdated', handleStorageChange);
        };
    }, []);

    const loadProfile = () => {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                const data = JSON.parse(saved);
                if (data.profile) {
                    setUserProfile({
                        firstName: data.profile.firstName || 'Sarah',
                        lastName: data.profile.lastName || 'Mitchell',
                        email: data.profile.email || 'sarah.mitchell@email.com'
                    });
                }
            }
        } catch (error) {
            console.error('Failed to load profile:', error);
        }
    };

    const navItems = [
        { icon: Home, label: "Home", path: "home" },
        { icon: Search, label: "Finder", path: "finder" },
        { icon: Database, label: "Chatbot", path: "chatbot" },
        { icon: User, label: "Profile", path: "profile" },
    ];

    const Item = ({ icon: Icon, label, path }) => {
        const isActive = currentPath === path;
        return (
            <button
                onClick={() => navigate(`/${path}`)}
                className={`group flex items-center gap-3 px-4 py-2.5 w-full text-left transition-colors duration-150
                ${isActive
                        ? "bg-primary text-white"
                        : "text-secondary hover:bg-slate-100"}`}
            >
                <Icon size={18} className={`${isActive ? "" : "opacity-70 group-hover:opacity-100"}`} />
                <span className="text-[13.5px] font-medium tracking-tight">{label}</span>
            </button>
        );
    };

    const initials = `${userProfile.firstName[0]}${userProfile.lastName[0]}`;
    const fullName = `${userProfile.firstName} ${userProfile.lastName}`;

    return (
        <aside className="w-[240px] h-full bg-panel border-r border-main flex flex-col">

            {/* Logo */}
            <div className="px-6 pt-6 pb-5">
                <div className="flex items-center gap-3">
                    <img 
                        src="/logo.png" 
                        alt="MedLinker Logo" 
                        className="w-16 h-16 object-contain"
                    />
                    <span className="font-semibold text-[16px] tracking-tight">
                        MedLinker
                    </span>
                </div>
            </div>

            {/* Separator under logo */}
            <div className="border-b border-main mx-6 mb-6" />

            {/* Navigation */}
            <nav className="flex flex-col gap-1">
                {navItems.map((item) => (
                    <Item
                        key={item.path}
                        icon={item.icon}
                        label={item.label}
                        path={item.path}
                    />
                ))}
            </nav>

            {/* User */}
            <div className="mt-auto border-t border-main p-6">
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-primary text-white flex items-center justify-center font-semibold text-[13px]">
                        {initials}
                    </div>
                    <div className="leading-tight">
                        <p className="text-[13px] font-medium">{fullName}</p>
                        <p className="text-[12px] text-secondary">{userProfile.email}</p>
                    </div>
                </div>
            </div>

        </aside>
    );
}