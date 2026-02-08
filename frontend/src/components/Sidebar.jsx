import { Home, Search, FileText, User, MessageSquare, Database } from "lucide-react";
import { useNavigate } from "react-router-dom";

export function Sidebar() {
    const navigate = useNavigate();
    const currentPath = window.location.pathname.split('/').pop() || 'home';

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

    return (
        <aside className="w-[240px] h-full bg-panel border-r border-main flex flex-col">

            {/* Logo */}
            <div className="px-6 pt-6 pb-5">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-primary flex items-center justify-center text-white font-semibold text-[18px]">
                        +
                    </div>
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
                        SM
                    </div>
                    <div className="leading-tight">
                        <p className="text-[13px] font-medium">Sarah Mitchell</p>
                        <p className="text-[12px] text-secondary">sarah.mitchell@email.com</p>
                    </div>
                </div>
            </div>

        </aside>
    );
}