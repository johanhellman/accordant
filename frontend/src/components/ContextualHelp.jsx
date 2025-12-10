import React, { useState } from 'react';
import { HelpCircle, X } from 'lucide-react';
import './ContextualHelp.css';

const HELP_CONTENT = {
    "stages": {
        title: "The 3-Stage Process",
        content: (
            <>
                <p>Accordant Ensures high quality through a multi-stage workflow:</p>
                <ul>
                    <li><strong>Stage 1 (Consultation):</strong> Your query is sent to multiple AI Personalities. They answer independently.</li>
                    <li><strong>Stage 2 (Peer Review):</strong> The personalities critique and rank each other's answers based on accuracy and helpfulness.</li>
                    <li><strong>Stage 3 (Synthesis):</strong> The Chairman AI compiles the best parts of the top-ranked answers into a final response.</li>
                </ul>
            </>
        )
    },
    "evolution": {
        title: "Personality Evolution",
        content: (
            <>
                <p>You can create new custom personalities by combining existing ones.</p>
                <p><strong>How it works:</strong></p>
                <ol>
                    <li>Select 2 or 3 "Parent" personalities.</li>
                    <li>The system analyzes their traits (instructions, tone, strengths).</li>
                    <li>A new "Offspring" is generated that inherits a blend of these traits.</li>
                </ol>
                <p>Use this to create specialized agents, e.g., combining a "Coder" and a "Teacher" to make a "Coding Tutor".</p>
            </>
        )
    },
    "ranking": {
        title: "League Table & Rankings",
        content: (
            <>
                <p>The League Table shows which personalities are performing best.</p>
                <ul>
                    <li><strong>Win Rate:</strong> The percentage of times this personality's answer was ranked #1 by its peers in Stage 2.</li>
                    <li><strong>Average Rank:</strong> The average position (1st, 2nd, 3rd...) it achieves. Lower is better.</li>
                    <li><strong>Sessions:</strong> Total conversations participated in.</li>
                </ul>
                <p>Personalities with low win rates may need their instructions refined.</p>
            </>
        )
    },
    "default": {
        title: "Help",
        content: "No help content available for this topic."
    }
};

export default function ContextualHelp({ topic, type = "icon" }) {
    const [isOpen, setIsOpen] = useState(false);
    const data = HELP_CONTENT[topic] || HELP_CONTENT["default"];

    if (type === "banner") {
        return (
            <div className="help-banner">
                <div className="help-banner-icon"><HelpCircle size={20} /></div>
                <div className="help-banner-content">
                    <strong>{data.title}:</strong> {data.content}
                </div>
            </div>
        );
    }

    return (
        <>
            <button
                className="contextual-help-btn"
                onClick={(e) => { e.stopPropagation(); setIsOpen(true); }}
                aria-label={`Help about ${data.title}`}
                title={`Learn about ${data.title}`}
            >
                <HelpCircle size={16} />
            </button>

            {isOpen && (
                <div className="help-modal-overlay" onClick={() => setIsOpen(false)}>
                    <div className="help-modal" onClick={e => e.stopPropagation()}>
                        <div className="help-modal-header">
                            <h3>{data.title}</h3>
                            <button className="help-close-btn" onClick={() => setIsOpen(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <div className="help-modal-body">
                            {data.content}
                        </div>
                        <div className="help-modal-footer">
                            <a href="/help" className="help-full-link">View Full User Manual</a>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
