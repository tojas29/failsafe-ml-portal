import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  // Core application state
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  
  // Clean default baseline template data (33 UCI features)
  const [formData, setFormData] = useState({
    school: "GP", sex: "F", age: 18, address: "U", famsize: "GT3", Pstatus: "A",
    Medu: 4, Fedu: 4, Mjob: "at_home", Fjob: "teacher", reason: "course", guardian: "mother",
    traveltime: 2, studytime: 2, failures: 0, schoolsup: "no", famsup: "no", paid: "no",
    activities: "no", nursery: "yes", higher: "yes", internet: "yes", romantic: "no",
    famrel: 4, freetime: 3, goout: 3, Dalc: 1, Walc: 1, health: 3, absences: 2,
    G1: 12, G2: 12
  });

  // Fetch log history on page load
  const fetchHistory = async () => {
    try {
      const response = await axios.get("https://failsafe-ml-portal.onrender.com/history");
      setHistory(response.data);
    } catch (err) {
      console.error("Error connecting to FastAPI database layer", err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  // Quick-load buttons to demonstrate model variance during presentations
  const loadSample = (type) => {
    if (type === 'risk') {
      setFormData(prev => ({ ...prev, absences: 16, studytime: 1, failures: 2, G1: 5, G2: 4 }));
    } else {
      setFormData(prev => ({ ...prev, absences: 1, studytime: 4, failures: 0, G1: 16, G2: 15 }));
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: isNaN(value) ? value : parseInt(value, 10)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post("https://failsafe-ml-portal.onrender.com/predict", { data: formData });
      setResult(response.data);
      fetchHistory(); // Refresh the database timeline component instantly
    } catch (err) {
      alert("Backend API connection failed. Make sure Uvicorn is running on port 8000!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Header Banner */}
      <header style={styles.header}>
        <h1 style={styles.title}>📌 FAILSAFE Portal</h1>
        <p style={styles.subtitle}>Early-Intervention Machine Learning Student Risk Analytics Engine</p>
      </header>

      <div style={styles.dashboardGrid}>
        {/* Left Column: Interactive Form Panel */}
        <div style={styles.card}>
          <div style={styles.rowBetween}>
            <h2 style={styles.cardTitle}>Student Profile Entry</h2>
            <div>
              <button onClick={() => loadSample('safe')} style={styles.btnSampleSafe}>Load Model Student</button>
              <button onClick={() => loadSample('risk')} style={styles.btnSampleRisk}>Load At-Risk Student</button>
            </div>
          </div>
          
          <form onSubmit={handleSubmit} style={styles.form}>
            <div style={styles.inputGroup}>
              <label style={styles.label}>Weekly Study Time</label>
              <select name="studytime" value={formData.studytime} onChange={handleInputChange} style={styles.select}>
                <option value={1}>1: Under 2 Hours</option>
                <option value={2}>2: 2 to 5 Hours</option>
                <option value={3}>3: 5 to 10 Hours</option>
                <option value={4}>4: Over 10 Hours</option>
              </select>
            </div>

            <div style={styles.inputGroup}>
              <label style={styles.label}>Total Semester Absences</label>
              <input type="number" name="absences" min="0" max="93" value={formData.absences} onChange={handleInputChange} style={styles.input} />
            </div>

            <div style={styles.inputGroup}>
              <label style={styles.label}>Past Class Failures</label>
              <input type="number" name="failures" min="0" max="4" value={formData.failures} onChange={handleInputChange} style={styles.input} />
            </div>

            <div style={styles.grid2Col}>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Midterm Grade 1 (0-20)</label>
                <input type="number" name="G1" min="0" max="20" value={formData.G1} onChange={handleInputChange} style={styles.input} />
              </div>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Midterm Grade 2 (0-20)</label>
                <input type="number" name="G2" min="0" max="20" value={formData.G2} onChange={handleInputChange} style={styles.input} />
              </div>
            </div>

            <button type="submit" disabled={loading} style={styles.btnSubmit}>
              {loading ? "Processing AI Weights..." : "Run Predictive Diagnostics"}
            </button>
          </form>
        </div>

        {/* Right Column: Dynamic Real-time AI Output Panel */}
        <div style={styles.rightColumn}>
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>Live Inference Output</h2>
            {result ? (
              <div>
                <div style={result.at_risk_prediction === 1 ? styles.alertRisk : styles.alertSafe}>
                  <h3 style={{ margin: 0, fontSize: '20px' }}>
                    Status: {result.at_risk_prediction === 1 ? "⚠️ CRITICAL FAILURE RISK DETECTED" : "✅ ACADEMICALLY SECURE"}
                  </h3>
                  <p style={{ margin: '8px 0 0 0', fontSize: '28px', fontWeight: 'bold' }}>
                    Failure Probability: {result.failure_probability}%
                  </p>
                  {/* SHAP Explainable AI Real-time Root Cause Graph */}
{result.shap_analysis && (
  <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
    <h4 style={{ margin: '0 0 4px 0', color: '#1e293b', fontSize: '14px', fontWeight: '600' }}>
      🔍 SHAP Root-Cause Analysis (XAI Transparency)
    </h4>
    <p style={{ fontSize: '12px', color: '#64748b', margin: '0 0 15px 0' }}>
      Positive values increase failure risk; negative values pull risk down.
    </p>
    
    {Object.entries(result.shap_analysis).map(([feature, value]) => {
      const isRiskDriver = value > 0;
      const barWidth = Math.min(Math.abs(value) * 25, 100); // Scaling factor for the visual bars
      
      return (
        <div key={feature} style={{ marginBottom: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
            <span style={{ fontWeight: '500', color: '#475569' }}>{feature}</span>
            <span style={{ fontWeight: '600', color: isRiskDriver ? '#dc2626' : '#16a34a' }}>
              {isRiskDriver ? '▲' : '▼'} {Math.abs(value).toFixed(2)}
            </span>
          </div>
          <div style={{ width: '100%', height: '6px', backgroundColor: '#e2e8f0', borderRadius: '3px', position: 'relative' }}>
            <div style={{
              width: `${barWidth}%`,
              height: '100%',
              backgroundColor: isRiskDriver ? '#df2c18' : '#22c55e',
              borderRadius: '3px',
              transition: 'width 0.4s ease-in-out',
              // Visual split-bar layout mechanics:
              marginLeft: isRiskDriver ? '50%' : 'auto',
              marginRight: isRiskDriver ? 'auto' : '50%'
            }} />
          </div>
        </div>
      );
    })}
  </div>
)}
                </div>
                <div style={styles.interventionBox}>
                  {result.interventions && result.interventions.length > 0 ? (
  <ul style={{ paddingLeft: '20px', color: '#334155', fontSize: '14px', lineHeight: '1.6', margin: '8px 0 0 0' }}>
    {result.interventions.map((item, idx) => (
      <li key={idx} style={{ marginBottom: '6px' }}>{item}</li>
    ))}
  </ul>
) : (
  <p style={{ margin: '8px 0 0 0', fontSize: '14px', color: '#64748b' }}>
    None required. Maintain current tracking.
  </p>
)}
                  <p style={{ margin: 0, color: '#475569', lineHeight: '1.5' }}>{result.suggested_intervention}</p>
                </div>
              </div>
            ) : (
              <p style={styles.placeholderText}>Awaiting input. Select a profile layout or manually alter fields to prompt real-time XGBoost matrix evaluation.</p>
            )}
          </div>

          {/* Database History Log Component */}
          <div style={styles.card}>
            <h3 style={styles.cardSubTitle}>Historical Database Ledger (Live SQLite)</h3>
            <div style={styles.tableWrapper}>
              <table style={styles.table}>
                <thead>
                  <tr style={styles.thRow}>
                    <th style={styles.th}>ID</th>
                    <th style={styles.th}>Study</th>
                    <th style={styles.th}>Absences</th>
                    <th style={styles.th}>Probability</th>
                    <th style={styles.th}>Prediction</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item) => (
                    <tr key={item.id} style={styles.tr}>
                      <td style={styles.td}>#{item.id}</td>
                      <td style={styles.td}>{item.studytime}h</td>
                      <td style={styles.td}>{item.absences} days</td>
                      <td style={styles.td, { ...styles.td, fontWeight: 'bold', color: item.failure_probability > 50 ? '#ef4444' : '#10b981' }}>
                        {item.failure_probability}%
                      </td>
                      <td style={styles.td}>
                        <span style={item.at_risk_prediction === 1 ? styles.badgeRisk : styles.badgeSafe}>
                          {item.at_risk_prediction === 1 ? 'Risk' : 'Safe'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Inline Production-Grade UI Theme Stylesheet
const styles = {
  container: { fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', padding: '30px', backgroundColor: '#f8fafc', minHeight: '100vh', color: '#0f172a' },
  header: { borderBottom: '2px solid #e2e8f0', paddingBottom: '16px', marginBottom: '30px' },
  title: { fontSize: '32px', fontWeight: '800', color: '#1e3a8a', margin: '0 0 6px 0' },
  subtitle: { fontSize: '15px', color: '#64748b', margin: 0 },
  dashboardGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' },
  rightColumn: { display: 'flex', flexDirection: 'column', gap: '30px' },
  card: { backgroundColor: '#ffffff', borderRadius: '12px', padding: '24px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03)', border: '1px solid #e2e8f0' },
  cardTitle: { fontSize: '20px', fontWeight: '700', color: '#0f172a', margin: '0 0 20px 0' },
  cardSubTitle: { fontSize: '16px', fontWeight: '700', color: '#334155', margin: '0 0 12px 0' },
  rowBetween: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' },
  form: { display: 'flex', flexDirection: 'column', gap: '18px' },
  inputGroup: { 
    display: 'flex', 
    flexDirection: 'column', 
    gap: '8px', 
    marginBottom: '10px',
    position: 'relative' 
  },
  grid2Col: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' },
  label: { fontSize: '13px', fontWeight: '600', color: '#475569' },
  input: { 
    padding: '12px 14px', 
    borderRadius: '8px', 
    border: '1px solid #cbd5e1', 
    fontSize: '15px', 
    backgroundColor: '#ffffff', 
    color: '#0f172a',
    width: '100%',
    boxSizing: 'border-box'
  },
  select: { 
    padding: '12px 14px', 
    borderRadius: '8px', 
    border: '1px solid #cbd5e1', 
    fontSize: '15px', 
    backgroundColor: '#ffffff', 
    color: '#0f172a', 
    width: '100%',
    boxSizing: 'border-box',
    cursor: 'pointer',
    appearance: 'auto' // Forces the native browser dropdown arrow to render cleanly
  },
  btnSubmit: { backgroundColor: '#2563eb', color: '#fff', border: 'none', padding: '12px', borderRadius: '8px', fontWeight: '600', cursor: 'pointer', fontSize: '15px', marginTop: '10px', transition: 'background-color 0.2s' },
  btnSampleSafe: { backgroundColor: '#ecfdf5', color: '#047857', border: '1px solid #a7f3d0', padding: '6px 12px', borderRadius: '6px', fontWeight: '600', marginRight: '8px', cursor: 'pointer', fontSize: '13px' },
  btnSampleRisk: { backgroundColor: '#fef2f2', color: '#b91c1c', border: '1px solid #fecaca', padding: '6px 12px', borderRadius: '6px', fontWeight: '600', cursor: 'pointer', fontSize: '13px' },
  placeholderText: { color: '#94a3b8', fontStyle: 'italic', textAlign: 'center', padding: '40px 0', margin: 0 },
  alertRisk: { backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', padding: '20px', borderRadius: '8px', marginBottom: '20px' },
  alertSafe: { backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534', padding: '20px', borderRadius: '8px', marginBottom: '20px' },
  interventionBox: { backgroundColor: '#f1f5f9', borderLeft: '4px solid #475569', padding: '16px', borderRadius: '0 8px 8px 0' },
  tableWrapper: { maxHeight: '200px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '8px' },
  table: { width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' },
  thRow: { backgroundColor: '#f8fafc', position: 'sticky', top: 0, borderBottom: '1px solid #e2e8f0' },
  th: { padding: '10px 12px', color: '#64748b', fontWeight: '600' },
  tr: { borderBottom: '1px solid #f1f5f9' },
  td: { padding: '10px 12px', color: '#334155' },
  badgeRisk: { backgroundColor: '#fee2e2', color: '#ef4444', padding: '2px 8px', borderRadius: '12px', fontSize: '12px', fontWeight: '600' },
  badgeSafe: { backgroundColor: '#d1fae5', color: '#10b981', padding: '2px 8px', borderRadius: '12px', fontSize: '12px', fontWeight: '600' }
};

export default App;
