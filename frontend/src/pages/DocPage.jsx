import React from "react";
import { useNavigate } from "react-router-dom";
import DocViewer from "../components/DocViewer";

const DocPage = ({ docId, title }) => {
  const navigate = useNavigate();

  return <DocViewer docId={docId} title={title} onBack={() => navigate("/")} />;
};

export default DocPage;
