import React, { useState, useEffect } from "react";
import axios from "axios";

// Target your live Render api backend gateway instance
const API_BASE = "https://failsafe-ml-portal.onrender.com";

function App() {
  // 1. Session & Routing Core State Hooks (With Crash-Proof Safe Initialization)
  const [token, setToken] = useState(() => localStorage.getItem("failsafe_token") || "");
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem("failsafe_user");
      // If it's empty, null, or a literal string "undefined", safely default to null
      if (!saved || saved === "undefined") return null;
      return JSON.parse(saved);
    } catch (e) {
      console.error("Clearing corrupted legacy local storage cache records:", e);
      localStorage.clear();
      return null;
    }
  });

  const [view, setView] = useState(token ? "DASHBOARD" : "LOGIN");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [result, setResult] = useState(null);

  // 2. Authentication Form Fields State
  const [authForm, setAuthForm] = useState({ email: "", password: "", name: "" });

  // 3. Complete 21-Feature Academic, Behavioral, and Household Data Contracts
  const [studentForm, setStudentForm] = useState({
    student_id: "STU-101",
    G1: 12, G2: 12, absences: 2, failures: 0, studytime: 2,
    traveltime: 1, famrel: 4, freetime: 3, goout: 2, Dalc: 1, Walc: 1, health: 4,
    Medu: 3, Fedu: 3, schoolsup: 0, famsup: 1, paid: 0, activities: 1, higher: 1, internet: 1, romantic: 0
  });

  // Automated Authorization Network Header Configuration
  const authConfig = { headers: { Authorization: `Bearer ${token}` } };

  // Sync historical logging from cloud infrastructure database cluster on view change
  useEffect(() => {
    if (token && view === "DASHBOARD") {
      fetchHistory();
    }
  }, [token, view]);

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/dashboard/history`, authConfig);
      setHistory(res.data);
    } catch (err) {
      console.error("Database sync diagnostic failure:", err);
    }
  };

  // 4. Session Authentication Handling Logic
  const handleAuthSubmit = async (e, type) => {
    e.preventDefault();
    setLoading(true);
    try {
      let res;
      if (type === "LOGIN") {
        const params = new URLSearchParams();
        params.append("username", authForm.email);
        params.append("password", authForm.password);
        res = await axios.post(`${API_BASE}/auth/login`, params, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" }
        });
      } else {
        res = await axios.post(`${API_BASE}/auth/register`, authForm);
      }
      
      localStorage.setItem("failsafe_token", res.data.access_token);
      localStorage.setItem("failsafe_user", JSON.stringify(res.data));
      setToken(res.data.access_token);
      setUser(res.data);
      setView("DASHBOARD");
    } catch (err) {
      alert(err.response?.data?.detail || "Authentication sequence mismatch.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    setToken("");
    setUser(null);
    setView("LOGIN");
  };

  // 5. Predictive ML Pipeline Execution Client Channel
  const handlePredictSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/predict`, studentForm, authConfig);
      setResult(res.data);
    } catch (err) {
      alert(err.response?.data?.detail || "Prediction transmission dropped.");
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (profile) => {
    if (profile === "EXCELLENT") {
      setStudentForm({
        student_id: "STU-GOOD", G1: 18, G2: 17, absences: 0, failures: 0, studytime: 4,
        traveltime: 1, famrel: 5, freetime: 2, goout: 1, Dalc: 1, Walc: 1, health: 5,
        Medu: 4, Fedu: 4, schoolsup: 0, famsup: 1, paid: 1, activities: 1, higher: 1, internet: 1, romantic: 0
      });
    } else {
      setStudentForm({
        student_id: "STU-RISK", G1: 6, G2: 5, absences: 18, failures: 2, studytime: 1,
        traveltime: 3, famrel: 2, freetime: 4, goout: 5, Dalc: 3, Walc: 4, health: 2,
        Medu: 1, Fedu: 1, schoolsup: 1, famsup: 0, paid: 0, activities: 0, higher: 0, internet: 0, romantic: 1
      });
    }
  };

  const styles = {
    input: { width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "14px", boxSizing: "border-box" },
    label: { display: "block", fontSize: "12px", fontWeight: "600", color: "#475569", marginBottom: "4px" },
    sectionTitle: { fontSize: "14px", fontWeight: "700", color: "#1e293b", margin: "12px 0 6px 0", borderBottom: "1px solid #f1f5f9", paddingBottom: "4px" }
  };

  if (view === "LOGIN" || view === "SIGNUP") {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", backgroundColor: "#0f172a", fontFamily: "system-ui" }}>
        <form onSubmit={(e) => handleAuthSubmit(e, view)} style={{ backgroundColor: "#ffffff", padding: "32px", borderRadius: "12px", width: "100%", maxWidth: "380px", boxShadow: "0 10px 25px -5px rgba(0,0,0,0.3)" }}>
          <h2 style={{ margin: "0 0 4px 0", color: "#1e293b", fontSize: "24px", fontWeight: "800", textAlign: "center" }}>FAILSAFE</h2>
          <p style={{ margin: "0 0 24px 0", color: "#64748b", fontSize: "13px", textAlign: "center" }}>AI-Assisted Faculty Academic Intervention System</p>
          
          {view === "SIGNUP" && (
            <div style={{ marginBottom: "14px" }}>
              <label style={styles.label}>Full Name</label>
              <input type="text" required style={styles.input} onChange={e => setAuthForm({...authForm, name: e.target.value})} />
            </div>
          )}
          <div style={{ marginBottom: "14px" }}>
            <label style={styles.label}>Faculty Email</label>
            <input type="email" required style={styles.input} onChange={e => setAuthForm({...authForm, email: e.target.value})} />
          </div>
          <div style={{ marginBottom: "20px" }}>
            <label style={styles.label}>Security Password</label>
            <input type="password" required style={styles.input} onChange={e => setAuthForm({...authForm, password: e.target.value})} />
          </div>

          <button type="submit" disabled={loading} style={{ width: "100%", padding: "10px", backgroundColor: "#2563eb", color: "#ffffff", border: "none", borderRadius: "6px", fontWeight: "700", cursor: "pointer" }}>
            {loading ? "Authenticating Platform Weights..." : view === "LOGIN" ? "Sign In to Workspace" : "Register Faculty Account"}
          </button>
          
          <p style={{ textAlign: "center", fontSize: "13px", color: "#64748b", marginTop: "16px", marginBottom: 0 }}>
            {view === "LOGIN" ? "New to the portal?" : "Already registered?"} {" "}
            <span style={{ color: "#2563eb", cursor: "pointer", fontWeight: "600" }} onClick={() => setView(view === "LOGIN" ? "SIGNUP" : "LOGIN")}>
              {view === "LOGIN" ? "Create an account" : "Sign in instead"}
            </span>
          </p>
        </form>
      </div>
    );
  }

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", backgroundColor: "#f8fafc", minHeight: "100vh", color: "#334155" }}>
      <nav style={{ backgroundColor: "#0f172a", color: "#ffffff", padding: "14px 24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
          <span style={{ fontSize: "18px", fontWeight: "800", letterSpacing: "0.5px" }}>🛡️ FAILSAFE HUB</span>
          <button onClick={() => setView("DASHBOARD")} style={{ background: "none", border: "none", color: view === "DASHBOARD" ? "#3b82f6" : "#94a3b8", fontWeight: "600", cursor: "pointer" }}>Dashboard View</button>
          <button onClick={() => { setView("PREDICT"); setResult(null); }} style={{ background: "none", border: "none", color: view === "PREDICT" ? "#3b82f6" : "#94a3b8", fontWeight: "600", cursor: "pointer" }}>+ Run Risk Assessment</button>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <span style={{ fontSize: "13px", color: "#94a3b8" }}>Advisor: <b style={{ color: "#fff" }}>{user?.user_name || "Faculty Member"}</b></span>
          <button onClick={handleLogout} style={{ backgroundColor: "#334155", color: "#f8fafc", border: "none", padding: "6px 12px", borderRadius: "4px", fontSize: "12px", fontWeight: "600", cursor: "pointer" }}>Logout</button>
        </div>
      </nav>

      <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "24px" }}>
        {view === "DASHBOARD" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
              <div style={{ backgroundColor: "#fff", padding: "16px", borderRadius: "8px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", borderLeft: "4px solid #3b82f6" }}>
                <div style={{ fontSize: "12px", color: "#64748b", fontWeight: "700" }}>TOTAL ASSESSMENTS RUN</div>
                <div style={{ fontSize: "28px", fontWeight: "800", color: "#1e293b" }}>{history.length} Students</div>
              </div>
              <div style={{ backgroundColor: "#fff", padding: "16px", borderRadius: "8px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", borderLeft: "4px solid #ef4444" }}>
                <div style={{ fontSize: "12px", color: "#64748b", fontWeight: "700" }}>CRITICAL ALERTS FLAGGED</div>
                <div style={{ fontSize: "28px", fontWeight: "800", color: "#b91c1c" }}>{history.filter(h => h.prediction === 1).length} Students</div>
              </div>
            </div>

            <div style={{ backgroundColor: "#ffffff", padding: "24px", borderRadius: "8px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
              <h3 style={{ margin: "0 0 16px 0", fontSize: "16px", fontWeight: "700" }}>Supabase Cloud Database History Audit Ledger</h3>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px", textAlign: "left" }}>
                  <thead>
                    <tr style={{ backgroundColor: "#f8fafc", borderBottom: "2px solid #e2e8f0", color: "#64748b" }}>
                      <th style={{ padding: "12px" }}>Student Identifier ID</th>
                      <th style={{ padding: "12px" }}>Absences Tracker</th>
                      <th style={{ padding: "12px" }}>Study Scaling</th>
                      <th style={{ padding: "12px" }}>AI Tree Score</th>
                      <th style={{ padding: "12px" }}>Operational Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.length === 0 ? (
                      <tr><td colSpan="5" style={{ padding: "24px", textAlign: "center", color: "#94a3b8", fontStyle: "italic" }}>No diagnostic entries found inside your remote PostgreSQL cluster tables.</td></tr>
                    ) : (
                      history.map((row) => (
                        <tr key={row.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                          <td style={{ padding: "12px", fontWeight: "700" }}>{row.student_id}</td>
                          <td style={{ padding: "12px" }}>{row.absences} Days missed</td>
                          <td style={{ padding: "12px" }}>Option Tier {row.study_time}</td>
                          <td style={{ padding: "12px", fontWeight: "700", color: "#2563eb" }}>{row.probability}%</td>
                          <td style={{ padding: "12px" }}>
                            <span style={{ padding: "4px 8px", borderRadius: "4px", fontSize: "11px", fontWeight: "700", backgroundColor: row.prediction === 1 ? "#fee2e2" : "#d1fae5", color: row.prediction === 1 ? "#991b1b" : "#065f46" }}>
                              {row.prediction === 1 ? "⚠️ AT RISK" : "✅ SECURE"}
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
        )}

        {view === "PREDICT" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", alignItems: "start" }}>
            <div style={{ backgroundColor: "#ffffff", padding: "24px", borderRadius: "8px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "700" }}>Student Diagnostic Metric Profiler</h3>
                <div style={{ display: "flex", gap: "6px" }}>
                  <button onClick={() => loadPreset("EXCELLENT")} style={{ padding: "4px 8px", fontSize: "11px", fontWeight: "600", backgroundColor: "#e2e8f0", border: "none", borderRadius: "4px", cursor: "pointer" }}>Model Student</button>
                  <button onClick={() => loadPreset("FAILING")} style={{ padding: "4px 8px", fontSize: "11px", fontWeight: "600", backgroundColor: "#fee2e2", color: "#b91c1c", border: "none", borderRadius: "4px", cursor: "pointer" }}>At-Risk Student</button>
                </div>
              </div>

              <form onSubmit={handlePredictSubmit} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <div>
                  <label style={styles.label}>Student Unique Identifier Reference ID</label>
                  <input type="text" value={studentForm.student_id} style={styles.input} onChange={e => setStudentForm({...studentForm, student_id: e.target.value})} />
                </div>

                <div style={styles.sectionTitle}>1. Academic Ledger Ingress</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px" }}>
                  <div>
                    <label style={styles.label}>Midterm 1 (0-20)</label>
                    <input type="number" value={studentForm.G1} style={styles.input} onChange={e => setStudentForm({...studentForm, G1: parseInt(e.target.value) || 0})} />
                  </div>
                  <div>
                    <label style={styles.label}>Midterm 2 (0-20)</label>
                    <input type="number" value={studentForm.G2} style={styles.input} onChange={e => setStudentForm({...studentForm, G2: parseInt(e.target.value) || 0})} />
                  </div>
                  <div>
                    <label style={styles.label}>Past Failures</label>
                    <input type="number" value={studentForm.failures} style={styles.input} onChange={e => setStudentForm({...studentForm, failures: parseInt(e.target.value) || 0})} />
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                  <div>
                    <label style={styles.label}>Study Scale (1-4)</label>
                    <input type="number" value={studentForm.studytime} style={styles.input} onChange={e => setStudentForm({...studentForm, studytime: parseInt(e.target.value) || 1})} />
                  </div>
                  <div>
                    <label style={styles.label}>Semester Absences</label>
                    <input type="number" value={studentForm.absences} style={styles.input} onChange={e => setStudentForm({...studentForm, absences: parseInt(e.target.value) || 0})} />
                  </div>
                </div>

                <div style={styles.sectionTitle}>2. Behavioral Framework Ingress</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr", gap: "6px" }}>
                  <div><label style={styles.label}>Travel</label><input type="number" value={studentForm.traveltime} style={styles.input} onChange={e => setStudentForm({...studentForm, traveltime: parseInt(e.target.value) || 1})} /></div>
                  <div><label style={styles.label}>Family</label><input type="number" value={studentForm.famrel} style={styles.input} onChange={e => setStudentForm({...studentForm, famrel: parseInt(e.target.value) || 1})} /></div>
                  <div><label style={styles.label}>Free</label><input type="number" value={studentForm.freetime} style={styles.input} onChange={e => setStudentForm({...studentForm, freetime: parseInt(e.target.value) || 1})} /></div>
                  <div><label style={styles.label}>Out</label><input type="number" value={studentForm.goout} style={styles.input} onChange={e => setStudentForm({...studentForm, goout: parseInt(e.target.value) || 1})} /></div>
                  <div><label style={styles.label}>Health</label><input type="number" value={studentForm.health} style={styles.input} onChange={e => setStudentForm({...studentForm, health: parseInt(e.target.value) || 1})} /></div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                  <div><label style={styles.label}>Weekday Alcohol (1-5)</label><input type="number" value={studentForm.Dalc} style={styles.input} onChange={e => setStudentForm({...studentForm, Dalc: parseInt(e.target.value) || 1})} /></div>
                  <div><label style={styles.label}>Weekend Alcohol (1-5)</label><input type="number" value={studentForm.Walc} style={styles.input} onChange={e => setStudentForm({...studentForm, Walc: parseInt(e.target.value) || 1})} /></div>
                </div>

                <div style={styles.sectionTitle}>3. Household & Support Vectors (Binary Toggle: 1=Yes, 0=No)</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "6px" }}>
                  <div><label style={styles.label}>SchSupport</label><input type="number" value={studentForm.schoolsup} style={styles.input} onChange={e => setStudentForm({...studentForm, schoolsup: parseInt(e.target.value) || 0})} /></div>
                  <div><label style={styles.label}>FamSupport</label><input type="number" value={studentForm.famsup} style={styles.input} onChange={e => setStudentForm({...studentForm, famsup: parseInt(e.target.value) || 0})} /></div>
                  <div><label style={styles.label}>PaidClass</label><input type="number" value={studentForm.paid} style={styles.input} onChange={e => setStudentForm({...studentForm, paid: parseInt(e.target.value) || 0})} /></div>
                  <div><label style={styles.label}>Activities</label><input type="number" value={studentForm.activities} style={styles.input} onChange={e => setStudentForm({...studentForm, activities: parseInt(e.target.value) || 0})} /></div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "6px" }}>
                  <div><label style={styles.label}>Higher Edu</label><input type="number" value={studentForm.higher} style={styles.input} onChange={e => setStudentForm({...studentForm, higher: parseInt(e.target.value) || 0})} /></div>
                  <div><label style={styles.label}>Web Access</label><input type="number" value={studentForm.internet} style={styles.input} onChange={e => setStudentForm({...studentForm, internet: parseInt(e.target.value) || 0})} /></div>
                  <div><label style={styles.label}>Romantic</label><input type="number" value={studentForm.romantic} style={styles.input} onChange={e => setStudentForm({...studentForm, romantic: parseInt(e.target.value) || 0})} /></div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                  <div><label style={styles.label}>Mother Edu (0-4)</label><input type="number" value={studentForm.Medu} style={styles.input} onChange={e => setStudentForm({...studentForm, Medu: parseInt(e.target.value) || 0})} /></div>
                  <div><label style={styles.label}>Father Edu (0-4)</label><input type="number" value={studentForm.Fedu} style={styles.input} onChange={e => setStudentForm({...studentForm, Fedu: parseInt(e.target.value) || 0})} /></div>
                </div>

                <button type="submit" disabled={loading} style={{ marginTop: "12px", padding: "12px", backgroundColor: "#10b981", color: "#ffffff", border: "none", borderRadius: "6px", fontWeight: "700", cursor: "pointer" }}>
                  {loading ? "Running 21-Feature Matrix Weights..." : "Execute Real-Time XGBoost Diagnostic"}
                </button>
              </form>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
              <div style={{ backgroundColor: "#ffffff", padding: "24px", borderRadius: "8px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", minHeight: "260px" }}>
                <h3 style={{ margin: "0 0 16px 0", fontSize: "16px", fontWeight: "700", textAlign: "center", borderBottom: "1px solid #f1f5f9", paddingBottom: "8px" }}>Live Core Inference Matrix Engine Output</h3>
                
                {!result ? (
                  <div style={{ color: "#94a3b8", fontStyle: "italic", textAlign: "center", marginTop: "60px" }}>Awaiting parameter data processing inputs. Click engine execute button to load vectors.</div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                    <div style={{ padding: "16px", borderRadius: "6px", textAlign: "center", backgroundColor: result.prediction === "AT-RISK" ? "#fef2f2" : "#ecfdf5", border: `1px solid ${result.prediction === "AT-RISK" ? "#fca5a5" : "#6ee7b7"}` }}>
                      <div style={{ fontSize: "12px", fontWeight: "800", color: result.prediction === "AT-RISK" ? "#991b1b" : "#065f46" }}>CLASSIFICATION ASSIGNMENT: {result.prediction}</div>
                      <div style={{ fontSize: "26px", fontWeight: "900", color: result.prediction === "AT-RISK" ? "#dc2626" : "#059669", marginTop: "4px" }}>Risk Weight: {result.risk_score}%</div>
                      <div style={{ display: "inline-block", marginTop: "6px", padding: "2px 8px", borderRadius: "10px", fontSize: "11px", fontWeight: "700", backgroundColor: "#fff", color: "#334155" }}>Band: {result.risk_band}</div>
                    </div>

                    <div style={{ backgroundColor: "#f8fafc", padding: "14px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                      <div style={{ fontSize: "13px", fontWeight: "700", marginBottom: "8px" }}>🔍 Top 5 SHAP Root-Cause Factor Variance Impact Vectors</div>
                      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                        {result.top_factors?.map(([feat, weight]) => (
                          <div key={feat} style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", borderBottom: "1px dashed #e2e8f0", paddingBottom: "4px" }}>
                            <span style={{ color: "#475569", fontWeight: "600" }}>{feat}</span>
                            <span style={{ fontFamily: "monospace", fontWeight: "700", color: weight >= 0 ? "#ef4444" : "#10b981" }}>
                              {weight >= 0 ? `▲ +${weight.toFixed(3)}` : `▼ ${weight.toFixed(3)}`}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div style={{ borderLeft: "4px solid #3b82f6", backgroundColor: "#eff6ff", padding: "12px", borderRadius: "4px" }}>
                      <div style={{ fontSize: "13px", fontWeight: "700", color: "#1e40af", marginBottom: "4px" }}>Triggered Rule Interventions:</div>
                      <p style={{ margin: 0, fontSize: "13px", color: "#1e3a8a", lineHeight: "1.4" }}>{result.intervention_plan}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;