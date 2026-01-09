import React, { useState, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api } from "../api";
import "./DocViewer.css";
import Logo from "./Logo"; // You might need to adjust import path
import { ArrowLeft } from "lucide-react";

export default function DocViewer({ docId, onBack, title }) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDoc();
  }, [loadDoc]);

  const loadDoc = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getDocumentation(docId);
      setContent(data.content);
    } catch (err) {
      console.error(err);
      setError("Failed to load document.");
    } finally {
      setLoading(false);
    }
  }, [docId]);

  return (
    <div className="doc-viewer-page">
      <header className="doc-header">
        <div className="container header-container">
          <button className="back-btn" onClick={onBack}>
            <ArrowLeft size={16} /> Back
          </button>
          <div className="brand">
            <Logo size="sm" />
            <span className="doc-title-badge">{title || "Documentation"}</span>
          </div>
        </div>
      </header>

      <main className="container doc-content-wrapper">
        {loading ? (
          <div className="doc-loading">Loading documentation...</div>
        ) : error ? (
          <div className="doc-error">{error}</div>
        ) : (
          <article className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </article>
        )}
      </main>

      <footer className="doc-footer">
        <div className="container">
          <p>© 2025 Accordant LLM Council</p>
        </div>
      </footer>
    </div>
  );
}
