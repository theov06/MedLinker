import { Search } from "lucide-react";


export function TopNavbar() {
    return (
        <header className="h-[64px] bg-panel border-b border-main px-6 flex items-center justify-between">
            <h1 className="text-[20px] font-semibold">Find Doctors & Clinics</h1>

            {/* Avatar */}
            <div className="w-9 h-9 bg-primary text-white flex items-center justify-center font-semibold">
                SM
            </div>
        </header>
    );
}