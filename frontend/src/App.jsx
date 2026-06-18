import React, { useState, useEffect } from "react";
import axios from "axios";

const API_BASE = "https://failsafe-ml-portal.onrender.com";

function App() {
  const [formData, setFormData] = useState({
    study_time: 2,
    failures: 0,
    absences: 2,
    g1: 12,
    g2: 12
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  // Load persistent history entries straight from the browser on boot
  useEffect(() => {
    const savedHistory = localStorage.getItem("failsafe_history");
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  const handlePreset = (type) => {
    if (type === "model") {
      setFormData({ study_time: 4, failures: 0, absences: 0, g1: 18, g2: 19 });
    } else {
      setFormData({ study_time: 1, failures: 2, absences: 16, g1: 5, g2: 4 });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/predict`, formData);
      setResult(res.data);
      
      // Construct a unified card payload mapping local values
      const newRecord = {
        id: Date.now(),
        study_time: formData.study_time,
        absences: formData.absences,
        probability: res.data.failure_probability,
        prediction: res.data.at_risk_prediction
      };
      
      const updatedHistory = [newRecord, ...history];
      setHistory(updatedHistory);
      localStorage.setItem("failsafe_history", JSON.stringify(updatedHistory));
    } catch (err) {
      console.error(err);
      alert("Backend network diagnostic channel failed.");
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: "100%",
    boxSizing: "border-box",
    padding: "10px",
    borderRadius: "8px",
    border: "1px solid #cbd5e1",
    backgroundColor: "#ffffff",
    color: "#1e293b",
    fontSize: "14px"
  };

  return (
    <div style={{ padding: "24px", fontFamily: "system-ui, -apple-system, sans-serif", backgroundColor: "#f1f5f9", minHeight: "100vh", color: "#334155" }}>
      <div style={{ maxWidth: "1100px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
        
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "24px" }}>
          
          {/* Profile Input Column */}
          <div style={{ backgroundColor: "#ffffff", padding: "24px", borderRadius: "16px", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)", display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h2 style={{ fontSize: "20px", fontWeight: "700", color: "#1e293b", margin: 0 }}>Student Profile Entry</h2>
              <div style={{ display: "flex", gap: "8px" }}>
                <button type="button" onClick={() => handlePreset("model")} style={{ backgroundColor: "#e6f4ea", color: "#137333", border: "1px solid #ceead6", borderRadius: "6px", padding: "6px 10px", fontSize: "11px", fontWeight: "600", cursor: "pointer" }}>Load Model Student</button>
                <button type="button" onClick={() => handlePreset("at_risk")} style={{ backgroundColor: "#fce8e6", color: "#c5221f", border: "1px solid #fad2cf", borderRadius: "6px", padding: "6px 10px", fontSize: "11px", fontWeight: "600", cursor: "pointer" }}>Load At-Risk Student</button>
              </div>
            </div>

            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", color: "#64748b", marginBottom: "4px" }}>Weekly Study Time</label>
                <select value={formData.study_time} onChange={(e) => setFormData({...formData, study_time: parseInt(e.target.value)})} style={inputStyle}>
                  <option value={1}>1: Under 2 Hours</option>
                  <option value={2}>2: 2 to 5 Hours</option>
                  <option value={3}>3: 5 to 10 Hours</option>
                  <option value={4}>4: Over 10 Hours</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", color: "#64748b", marginBottom: "4px" }}>Total Semester Absences</label>
                <input type="number" value={formData.absences} onChange={(e) => setFormData({...formData, absences: parseInt(e.target.value) || 0})} style={inputStyle} />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", color: "#64748b", marginBottom: "4px" }}>Past Class Failures</label>
                <input type="number" value={formData.failures} onChange={(e) => setFormData({...formData, failures: parseInt(e.target.value) || 0})} style={inputStyle} />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "11px", fontWeight: "600", color: "#64748b", marginBottom: "4px" }}>Midterm 1 (0-20)</label>
                  <input type="number" value={formData.g1} onChange={(e) => setFormData({...formData, g1: parseInt(e.target.value) || 0})} style={inputStyle} />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "11px", fontWeight: "600", color: "#64748b", marginBottom: "4px" }}>Midterm 2 (0-20)</label>
                  <input type="number" value={formData.g2} onChange={(e) => setFormData({...formData, g2: parseInt(e.target.value) || 0})} style={inputStyle} />
                </div>
              </div>

              <button type="submit" disabled={loading} style={{ marginTop: "10px", width: "100%", padding: "12px", backgroundColor: "#2563eb", color: "#ffffff", border: "none", borderRadius: "10px", fontWeight: "700", fontSize: "14px", cursor: "pointer" }}>
                {loading ? "Processing AI Weights..." : "Run Predictive Diagnostics"}
              </button>
            </form>
          </div>

          {/* Diagnostic Metrics Matrix */}
          <div style={{ backgroundColor: "#ffffff", padding: "24px", borderRadius: "16px", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)", display: "flex", flexDirection: "column" }}>
            <h2 style={{ fontSize: "20px", fontWeight: "700", color: "#1e293b", margin: "0 0 16px 0", borderBottom: "1px solid #e2e8f0", paddingBottom: "8px", textAlign: "center" }}>Live Inference Output</h2>
            
            {!result ? (
              <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#94a3b8", fontStyle: "italic", textAlign: "center" }}>
                Awaiting input data. Click run to prompt real-time XGBoost matrix evaluation.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px", flex: 1, justifyContent: "space-between" }}>
                <div style={{ padding: "14px", borderRadius: "10px", textAlign: "center", backgroundColor: result.at_risk_prediction === 1 ? "#fef2f2" : "#ecfdf5", color: result.at_risk_prediction === 1 ? "#991b1b" : "#065f46", border: `1px solid ${result.at_risk_prediction === 1 ? "#fca5a5" : "#6ee7b7"}` }}>
                  <span style={{ fontWeight: "700" }}>Status: {result.at_risk_prediction === 1 ? "❌ AT ACADEMIC RISK" : "✅ ACADEMICALLY SECURE"}</span>
                  <div style={{ fontSize: "22px", fontWeight: "800", marginTop: "4px" }}>Failure Probability: {result.failure_probability}%</div>
                </div>

                <div style={{ backgroundColor: "#f8fafc", padding: "14px", borderRadius: "10px", border: "1px solid #e2e8f0" }}>
                  <div style={{ fontWeight: "700", fontSize: "13px", color: "#334155", marginBottom: "8px" }}>🔍 SHAP Root-Cause Analysis</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "12px" }}>
                    {Object.entries(result.shap_analysis || {}).map(([feat, val]) => (
                      <div key={feat} style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px dashed #e2e8f0", paddingBottom: "6px" }}>
                        <span style={{ color: "#64748b" }}>{feat}</span>
                        <span style={{ fontFamily: "monospace", fontWeight: "700", color: val >= 0 ? "#dc2626" : "#16a34a" }}>
                          {val >= 0 ? `▲ +${Number(val).toFixed(2)}` : `▼ ${Number(val).toFixed(2)}`}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ borderLeft: "4px solid #3b82f6", backgroundColor: "#eff6ff", padding: "14px", borderRadius: "0 10px 10px 0", fontSize: "13px" }}>
                  <div style={{ fontWeight: "700", color: "#1e3a8a", marginBottom: "4px" }}>Interventions:</div>
                  <ul style={{ margin: 0, paddingLeft: "16px", color: "#1e40af" }}>
                    {result.interventions?.map((item, idx) => <li key={idx}>{item}</li>)}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Database Table Layout (Fueled by localStorage) */}
        <div style={{ backgroundColor: "#ffffff", padding: "24px", borderRadius: "16px", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)" }}>
          <h2 style={{ fontSize: "18px", fontWeight: "700", color: "#1e293b", margin: "0 0 14px 0", borderBottom: "1px solid #e2e8f0", paddingBottom: "8px" }}>Historical Database Ledger (Browser Persisted)</h2>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px", textAlign: "left" }}>
              <thead>
                <tr style={{ backgroundColor: "#f8fafc", borderBottom: "2px solid #e2e8f0", color: "#64748b" }}>
                  <th style={{ padding: "12px" }}>Timestamp Hash</th>
                  <th style={{ padding: "12px" }}>Study Option</th>
                  <th style={{ padding: "12px" }}>Absences</th>
                  <th style={{ padding: "12px" }}>Probability</th>
                  <th style={{ padding: "12px" }}>Prediction</th>
                </tr>
              </thead>
              <tbody style={{ fontWeight: "500", color: "#475569" }}>
                {history.length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ padding: "20px", textAlign: "center", color: "#94a3b8", fontStyle: "italic" }}>No previous entries recorded in local web storage.</td>
                  </tr>
                ) : (
                  history.map((row) => (
                    <tr key={row.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "12px", fontFamily: "monospace", color: "#94a3b8" }}>#{row.id}</td>
                      <td style={{ padding: "12px" }}>Option {row.study_time}</td>
                      <td style={{ padding: "12px" }}>{row.absences}</td>
                      <td style={{ padding: "12px", color: "#2563eb" }}>{row.probability}%</td>
                      <td style={{ padding: "12px" }}>
                        <span style={{ padding: "3px 8px", borderRadius: "4px", fontSize: "11px", fontWeight: "700", backgroundColor: row.prediction === 1 ? "#fee2e2" : "#d1fae5", color: row.prediction === 1 ? "#991b1b" : "#065f46" }}>
                          {row.prediction === 1 ? "At Risk" : "Secure"}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}

export default App;