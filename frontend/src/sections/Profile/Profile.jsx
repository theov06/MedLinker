// Profile.jsx - User Account Settings
import { Mail, Phone, Building, Shield, Bell, Globe } from "lucide-react";

export function Profile() {
    return (
        <div className="h-full overflow-y-auto p-6">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-[20px] font-semibold mb-2">Account Settings</h1>
                <p className="text-[14px] text-secondary">Manage your profile and account preferences</p>
            </div>

            <div className="flex gap-8">
                {/* Left Column - Personal Information */}
                <div className="flex-1">
                    <div className="bg-panel border border-main">
                        <div className="p-6 border-b border-main">
                            <h2 className="text-[16px] font-semibold mb-4">Personal Information</h2>

                            <div className="space-y-5">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-[13px] text-secondary mb-1">First Name</label>
                                        <input
                                            type="text"
                                            defaultValue="Sarah"
                                            className="w-full p-3 border border-main bg-white text-[14px] focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-[13px] text-secondary mb-1">Last Name</label>
                                        <input
                                            type="text"
                                            defaultValue="Mitchell"
                                            className="w-full p-3 border border-main bg-white text-[14px] focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-[13px] text-secondary mb-1 flex items-center gap-2">
                                        <Mail size={12} />
                                        Email Address
                                    </label>
                                    <input
                                        type="email"
                                        defaultValue="sarah.mitchell@email.com"
                                        className="w-full p-3 border border-main bg-white text-[14px] focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                                    />
                                </div>

                                <div>
                                    <label className="block text-[13px] text-secondary mb-1 flex items-center gap-2">
                                        <Phone size={12} />
                                        Phone Number
                                    </label>
                                    <input
                                        type="tel"
                                        defaultValue="+1 (555) 123-4567"
                                        className="w-full p-3 border border-main bg-white text-[14px] focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                                    />
                                </div>

                                <div>
                                    <label className="block text-[13px] text-secondary mb-1 flex items-center gap-2">
                                        <Building size={12} />
                                        Organization
                                    </label>
                                    <select className="w-full p-3 border border-main bg-white text-[14px] focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary">
                                        <option>Department of Health & Human Services</option>
                                        <option>Regional Health Authority</option>
                                        <option>Hospital Network Admin</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-[13px] text-secondary mb-1 flex items-center gap-2">
                                        <Globe size={12} />
                                        Region
                                    </label>
                                    <select className="w-full p-3 border border-main bg-white text-[14px] focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary">
                                        <option>North America</option>
                                        <option>Europe</option>
                                        <option>Asia Pacific</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div className="p-6">
                            <button className="px-5 py-2.5 bg-primary text-white hover-primary transition-colors duration-150 font-medium">
                                Save Changes
                            </button>
                        </div>
                    </div>

                    {/* Notification Preferences */}
                    <div className="bg-panel border border-main mt-6">
                        <div className="p-6 border-b border-main">
                            <div className="flex items-center gap-3 mb-4">
                                <Bell size={18} className="text-secondary" />
                                <h2 className="text-[16px] font-semibold">Notification Preferences</h2>
                            </div>

                            <div className="space-y-4">
                                {['Critical facility alerts', 'Weekly digest reports', 'New data available', 'System maintenance'].map((pref) => (
                                    <div key={pref} className="flex items-center justify-between">
                                        <span className="text-[14px]">{pref}</span>
                                        <label className="relative inline-flex items-center cursor-pointer">
                                            <input type="checkbox" className="sr-only peer" defaultChecked={pref === 'Critical facility alerts'} />
                                            <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:border-main after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
                                        </label>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column - Avatar & Security */}
                <div className="w-[320px]">
                    {/* Avatar Upload */}
                    <div className="bg-panel border border-main p-6 mb-6">
                        <div className="flex flex-col items-center">
                            <div className="w-24 h-24 bg-primary text-white flex items-center justify-center text-[32px] font-semibold mb-4">
                                SM
                            </div>

                            <button className="px-4 py-2 border border-main text-[13px] text-secondary hover:bg-slate-50 transition-colors duration-150 mb-2">
                                Upload New Photo
                            </button>
                            <p className="text-[12px] text-placeholder text-center">JPG, PNG or GIF, max 2MB</p>
                        </div>
                    </div>

                    {/* Security */}
                    <div className="bg-panel border border-main p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <Shield size={18} className="text-secondary" />
                            <h2 className="text-[16px] font-semibold">Security</h2>
                        </div>

                        <div className="space-y-6">
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-[14px] font-medium">Two-Factor Authentication</span>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input type="checkbox" className="sr-only peer" defaultChecked />
                                        <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:border-main after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
                                    </label>
                                </div>
                                <p className="text-[13px] text-secondary">Add an extra layer of security to your account</p>
                            </div>

                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-[14px] font-medium">Active Sessions</span>
                                    <span className="text-[13px] text-primary">3 devices</span>
                                </div>
                                <p className="text-[13px] text-secondary mb-3">Review and manage active sessions</p>
                                <button className="text-[13px] text-primary hover:text-primary-hover transition-colors duration-150">
                                    View All Sessions →
                                </button>
                            </div>

                            <div>
                                <h3 className="text-[14px] font-medium mb-2">Change Password</h3>
                                <p className="text-[13px] text-secondary mb-3">Last changed 30 days ago</p>
                                <button className="px-4 py-2 border border-main text-[13px] text-secondary hover:bg-slate-50 transition-colors duration-150">
                                    Update Password
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Account Status */}
                    <div className="bg-panel border border-main p-6 mt-6">
                        <h3 className="text-[14px] font-medium mb-4">Account Status</h3>
                        <div className="space-y-3">
                            <div className="flex justify-between">
                                <span className="text-[13px] text-secondary">Member Since</span>
                                <span className="text-[13px]">Jan 2023</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-[13px] text-secondary">Role</span>
                                <span className="text-[13px]">Administrator</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-[13px] text-secondary">Data Access</span>
                                <span className="text-[13px]">Full Access</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}