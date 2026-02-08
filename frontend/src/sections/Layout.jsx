import { Sidebar } from '../components/Sidebar'
import { TopNavbar } from '../components/TopNavbar'

export function Layout({ children }) {
    return (
        <div className="h-screen flex bg-[var(--color-bg-main)]">
            <Sidebar />

            {/* Right side */}
            <div className="flex-1 flex flex-col">
                <TopNavbar />

                <main className="flex-1 overflow-auto">
                    {children}
                </main>
            </div>
        </div>
    )
}
