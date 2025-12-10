import React from "react";
import { Sparkles } from "lucide-react";
import "./Logo.css";

/**
 * Logo component for the Accordant brand.
 * 
 * @param {string} className - Additional classes for the container
 * @param {boolean} iconOnly - Whether to show only the icon
 * @param {string} size - Size variant: "sm", "md" (default), "lg", "xl"
 */
const Logo = ({ className = "", iconOnly = false, size = "md" }) => {
    return (
        <div className={`accordant-logo size-${size} ${className}`}>
            <Sparkles className="logo-icon" />
            {!iconOnly && <span className="logo-text">Accordant</span>}
        </div>
    );
};

export default Logo;
