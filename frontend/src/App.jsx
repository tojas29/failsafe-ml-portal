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

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/history`);
      if (res.data && res.data.history) {
        setHistory(res.data.history);
      } else if (Array.isArray(res.data)) {
        setHistory(res.data);
      }
    } catch (err) {
      console.error("Failed to sync database ledger", err);
    }
  };

  useEffect(() => {
    fetchHistory();
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
      await fetchHistory(); // Automatically updates the history table on screen instantly!
    } catch (err) {
      alert("Backend API connection failed. Make sure Uvicorn is active!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Main Operational Hub */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Left Panel: Profile Input */}
          <div className="bg-white text-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold tracking-tight">Student Profile Entry</h2>
              <div className="flex flex-col gap-2">
                <button onClick={() => handlePreset("model")} className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-3 py-1 rounded hover:bg-emerald-200 transition">Load Model Student</button>
                <button onClick={() => handlePreset("at_risk")} className="bg-rose-100 text-rose-800 text-xs font-semibold px-3 py-1 rounded hover:bg-rose-200 transition">Load At-Risk Student</button>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block font-medium text-slate-600 mb-1">Weekly Study Time</label>
                <select value={formData.study_time} onChange={(e) => setFormData({...formData, study_time: parseInt(e.target.value)})} className="w-full p-2 border border-slate-300 rounded-lg bg-slate-50 text-slate-800">
                  <option value={1}>1: Under 2 Hours</option>
                  <option value={2}>2: 2 to 5 Hours</option>
                  <option value={3}>3: 5 to 10 Hours</option>
                  <option value={4}>4: Over 10 Hours</option>
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-600 mb-1">Total Semester Absences</label>
                <input type="number" value={formData.absences} onChange={(e) => setFormData({...formData, absences: parseInt(e.target.value) || 0})} className="w-full p-2 border border-slate-300 rounded-lg bg-slate-50" />
              </div>

              <div>
                <label className="block font-medium text-slate-600 mb-1">Past Class Failures</label>
                <input type="number" value={formData.failures} onChange={(e) => setFormData({...formData, failures: parseInt(e.target.value) || 0})} className="w-full p-2 border border-slate-300 rounded-lg bg-slate-50" />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-medium text-slate-600 mb-1">Midterm Grade 1 (0-20)</label>
                  <input type="number" value={formData.g1} onChange={(e) => setFormData({...formData, g1: parseInt(e.target.value) || 0})} className="w-full p-2 border border-slate-300 rounded-lg bg-slate-50" />
                </div>
                <div>
                  <label className="block font-medium text-slate-600 mb-1">Midterm Grade 2 (0-20)</label>
                  <input type="number" value={formData.g2} onChange={(e) => setFormData({...formData, g2: parseInt(e.target.value) || 0})} className="w-full p-2 border border-slate-300 rounded-lg bg-slate-50" />
                </div>
              </div>

              <button type="submit" disabled={loading} className="w-full py-3 bg-blue-600 text-white font-bold rounded-xl shadow-md hover:bg-blue-700 transition disabled:bg-blue-400">
                {loading ? "Processing AI Weights..." : "Run Predictive Diagnostics"}
              </button>
            </form>
          </div>

          {/* Right Panel: Output Engine */}
          <div className="bg-white text-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
            <h2 className="text-2xl font-bold tracking-tight border-b pb-2 mb-4 text-center">Live Inference Output</h2>
            
            {!result ? (
              <div className="flex-1 flex items-center justify-center text-center p-6 text-slate-400 italic">
                Awaiting input. Select a profile layout or manually alter fields to prompt real-time XGBoost matrix evaluation.
              </div>
            ) : (
              <div className="space-y-6 flex-1 flex flex-col justify-between">
                <div className={`p-4 rounded-xl text-center font-bold text-lg ${result.at_risk_prediction === 1 ? "bg-rose-50 text-rose-700 border border-rose-200" : "bg-emerald-50 text-emerald-700 border border-emerald-200"}`}>
                  Status: {result.at_risk_prediction === 1 ? "? AT ACADEMIC RISK" : "? ACADEMICALLY SECURE"}
                  <div className="text-2xl font-extrabold mt-1">Failure Probability: {result.failure_probability}%</div>
                </div>

                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                  <div className="font-bold text-sm text-slate-700 flex items-center gap-1">?? SHAP Root-Cause Analysis (XAI Transparency)</div>
                  <div className="text-xs text-slate-400">Positive values increase failure risk; negative values pull risk down.</div>
                  <div className="space-y-2 text-xs">
                    {Object.entries(result.shap_analysis || {}).map(([feature, val]) => (
                      <div key={feature} className="flex justify-between items-center border-b pb-1">
                        <span className="text-slate-600 font-medium">{feature}</span>
                        <span className={`font-mono font-bold ${val >= 0 ? "text-rose-600" : "text-emerald-600"}`}>
                          {val >= 0 ? `? +${val.toFixed(2)}` : `? ${val.toFixed(2)}`}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="border-l-4 border-blue-500 bg-blue-50 p-4 rounded-r-xl text-sm">
                  <div className="font-bold text-blue-900 mb-1">Tailored Action Interventions:</div>
                  <ul className="list-disc pl-4 text-blue-800 space-y-1 font-medium">
                    {result.interventions?.map((item, idx) => <li key={idx}>{item}</li>)}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Section: SQLite Database Ledger */}
        <div className="bg-white text-slate-800 p-6 rounded-2xl shadow-xl">
          <h2 className="text-xl font-bold mb-4 tracking-tight border-b pb-2 text-center">Historical Database Ledger (Live SQLite)</h2>
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-100 text-slate-600 font-bold border-b">
                <tr>
                  <th className="p-3">ID</th>
                  <th className="p-3">Study (Hrs)</th>
                  <th className="p-3">Absences</th>
                  <th className="p-3">Probability</th>
                  <th className="p-3">Prediction</th>
                </tr>
              </thead>
              <tbody className="divide-y font-medium text-slate-700">
                {history.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="p-4 text-center text-slate-400 italic">No recorded matrix entries found inside failsafe.db</td>
                  </tr>
                ) : (
                  history.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-50 transition">
                      <td className="p-3 font-mono text-slate-400">#{row.id}</td>
                      <td className="p-3">{row.study || row.study_time}</td>
                      <td className="p-3">{row.absences}</td>
                      <td className="p-3 font-mono text-blue-600">{row.probability || row.failure_probability}%</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${(row.prediction === 1 || row.at_risk_prediction === 1) ? "bg-rose-100 text-rose-800" : "bg-emerald-100 text-emerald-800"}`}>
                          {(row.prediction === 1 || row.at_risk_prediction === 1) ? "Risk" : "Safe"}
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
