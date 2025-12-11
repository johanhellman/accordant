import React, { useState, useEffect } from "react";
import { api } from "../api";
import { Download, Trash2, Shield, User, Lock, Key } from "lucide-react";
import "./UserSettings.css";

export default function UserSettings() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [exporting, setExporting] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [error, setError] = useState(null);
    const [successMsg, setSuccessMsg] = useState(null);
    const [confirmDelete, setConfirmDelete] = useState(false);

    // Password Change State
    const [pwdForm, setPwdForm] = useState({
        currentPassword: "",
        newPassword: "",
        confirmPassword: ""
    });
    const [changingPwd, setChangingPwd] = useState(false);

    useEffect(() => {
        loadUser();
    }, []);

    const loadUser = async () => {
        try {
            const userData = await api.getCurrentUser();
            setUser(userData);
        } catch (err) {
            setError("Failed to load user profile");
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async () => {
        try {
            setExporting(true);
            await api.exportUserData();
        } catch (err) {
            alert("Failed to export data: " + err.message);
        } finally {
            setExporting(false);
        }
    };

    const handleDeleteAccount = async () => {
        if (!confirmDelete) {
            setConfirmDelete(true);
            return;
        }

        try {
            setDeleting(true);
            await api.deleteAccount();
            window.location.reload();
        } catch (err) {
            setError("Failed to delete account: " + err.message);
            setDeleting(false);
        }
    };

    const handleChangePassword = async (e) => {
        e.preventDefault();
        setError(null);
        setSuccessMsg(null);

        if (pwdForm.newPassword !== pwdForm.confirmPassword) {
            setError("New passwords do not match");
            return;
        }

        if (pwdForm.newPassword.length < 8) {
            setError("New password must be at least 8 characters long");
            return;
        }

        try {
            setChangingPwd(true);
            await api.changePassword(pwdForm.currentPassword, pwdForm.newPassword);
            setSuccessMsg("Password changed successfully");
            setPwdForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
        } catch (err) {
            setError(err.message);
        } finally {
            setChangingPwd(false);
        }
    };

    if (loading) return <div className="settings-loading">Loading profile...</div>;

    return (
        <div className="user-settings-container">
            <header className="settings-header">
                <h2>User Settings</h2>
            </header>

            {/* Profile Section */}
            <div className="settings-section">
                <div className="section-header">
                    <User size={20} className="section-icon" />
                    <h3>Profile Information</h3>
                </div>
                <div className="profile-card">
                    <div className="profile-row">
                        <span className="label">Username</span>
                        <span className="value">{user?.username}</span>
                    </div>
                    <div className="profile-row">
                        <span className="label">User ID</span>
                        <span className="value monospace">{user?.id}</span>
                    </div>
                    <div className="profile-row">
                        <span className="label">Role</span>
                        <span className="value">
                            {user?.is_instance_admin ? "Instance Admin" : user?.is_admin ? "Org Admin" : "User"}
                        </span>
                    </div>
                </div>
            </div>

            {/* Security Section */}
            <div className="settings-section">
                <div className="section-header">
                    <Lock size={20} className="section-icon" />
                    <h3>Security</h3>
                </div>
                <div className="security-card">
                    <form onSubmit={handleChangePassword} className="password-form">
                        <h4>Change Password</h4>
                        <div className="form-group">
                            <label>Current Password</label>
                            <div className="input-wrapper">
                                <Key size={16} />
                                <input
                                    type="password"
                                    value={pwdForm.currentPassword}
                                    onChange={(e) => setPwdForm({ ...pwdForm, currentPassword: e.target.value })}
                                    required
                                />
                            </div>
                        </div>
                        <div className="form-group">
                            <label>New Password</label>
                            <div className="input-wrapper">
                                <Lock size={16} />
                                <input
                                    type="password"
                                    value={pwdForm.newPassword}
                                    onChange={(e) => setPwdForm({ ...pwdForm, newPassword: e.target.value })}
                                    required
                                />
                            </div>
                        </div>
                        <div className="form-group">
                            <label>Confirm New Password</label>
                            <div className="input-wrapper">
                                <Lock size={16} />
                                <input
                                    type="password"
                                    value={pwdForm.confirmPassword}
                                    onChange={(e) => setPwdForm({ ...pwdForm, confirmPassword: e.target.value })}
                                    required
                                />
                            </div>
                        </div>
                        <button type="submit" className="btn btn-primary" disabled={changingPwd}>
                            {changingPwd ? "Updating..." : "Update Password"}
                        </button>
                    </form>
                </div>
            </div>

            {/* Privacy Section */}
            <div className="settings-section">
                <div className="section-header">
                    <Shield size={20} className="section-icon" />
                    <h3>Data Privacy & GDPR</h3>
                </div>

                <div className="privacy-actions">
                    <div className="action-card">
                        <h4>Data Portability</h4>
                        <p>Download a copy of all your data, including profile information and conversation history, in JSON format.</p>
                        <button
                            className="btn btn-secondary action-btn"
                            onClick={handleExport}
                            disabled={exporting}
                        >
                            <Download size={16} />
                            {exporting ? "Exporting..." : "Export My Data"}
                        </button>
                    </div>

                    <div className="action-card danger-zone">
                        <h4>Right to Erasure</h4>
                        <p>Permanently delete your account and all associated conversations. This action cannot be undone.</p>

                        {!confirmDelete ? (
                            <button
                                className="btn btn-danger action-btn"
                                onClick={() => setConfirmDelete(true)}
                            >
                                <Trash2 size={16} />
                                Delete Account
                            </button>
                        ) : (
                            <div className="delete-confirm">
                                <p className="warning-text">Are you sure? All data will be lost forever.</p>
                                <div className="confirm-buttons">
                                    <button
                                        className="btn btn-danger"
                                        onClick={handleDeleteAccount}
                                        disabled={deleting}
                                    >
                                        {deleting ? "Deleting..." : "Yes, Delete Everything"}
                                    </button>
                                    <button
                                        className="btn btn-secondary"
                                        onClick={() => setConfirmDelete(false)}
                                        disabled={deleting}
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {error && <div className="error-message">{error}</div>}
            {successMsg && <div className="success-message">{successMsg}</div>}
        </div>
    );
}
