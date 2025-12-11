import React, { useState, useEffect } from "react";
import { api } from "../api";
import { Users, Building2, MessageSquare, Activity } from "lucide-react";
import "./AdminDashboard.css";

export default function AdminDashboard() {
    const [stats, setStats] = useState({
        total_organizations: 0,
        total_users: 0,
        active_conversations_24h: 0,
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            const data = await api.getAdminStats();
            setStats(data);
        } catch (err) {
            setError("Failed to load dashboard statistics");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="loading">Loading dashboard...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="admin-dashboard">
            <header className="dashboard-header">
                <h2>System Dashboard</h2>
                <p className="subtitle">Instance Overview</p>
            </header>

            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon orgs">
                        <Building2 size={24} />
                    </div>
                    <div className="stat-content">
                        <span className="stat-value">{stats.total_organizations}</span>
                        <span className="stat-label">Organizations</span>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon users">
                        <Users size={24} />
                    </div>
                    <div className="stat-content">
                        <span className="stat-value">{stats.total_users}</span>
                        <span className="stat-label">Total Users</span>
                    </div>
                </div>

                {/* 
        <div className="stat-card">
          <div className="stat-icon activity">
            <Activity size={24} />
          </div>
          <div className="stat-content">
            <span className="stat-value">{stats.active_conversations_24h}</span>
            <span className="stat-label">Active (24h)</span>
          </div>
        </div>
        */}
            </div>

            {/* Future: Add graphs or recent activity logs here */}
        </div>
    );
}
