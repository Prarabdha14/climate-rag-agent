// frontend/src/App.js
import React, { useState } from "react";
import axios from "axios";
import "./App.css";

// Use the Render URL you just copied (ensure no trailing slash)

const API_BASE = "https://climate-rag-backend.onrender.com";

// --- ICONS ---
const IconUpload = () => <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>;
const IconSearch = () => <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>;
const IconFile = () => <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>;
const IconCheck = () => <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>;
const IconBrain = () => <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>;
const IconChart = () => <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>;
const IconCode = () => <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>;
const IconGithub = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>;

// --- SIDEBAR COMPONENT ---
function Sidebar({ onUploadResult, onSearchResults }) {
  const [file, setFile] = useState(null);
  const [q, setQ] = useState("");
  const [loadingUpload, setLoadingUpload] = useState(false);
  const [loadingSearch, setLoadingSearch] = useState(false);

  const handleUpload = async () => {
    if (!file) return alert("Please select a file first.");
    setLoadingUpload(true);
    try {
      const form = new FormData();
      form.append("file", file, file.name);
      const res = await axios.post(`${API_BASE}/process`, form, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
      });
      onUploadResult(res.data);
    } catch (e) {
      alert("Upload failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setLoadingUpload(false);
    }
  };

  const handleSearch = async () => {
    if (!q.trim()) return;
    setLoadingSearch(true);
    try {
      const res = await axios.post(`${API_BASE}/query`, { query: q });
      onSearchResults(res.data);
    } catch (e) {
      alert("Search failed");
    } finally {
      setLoadingSearch(false);
    }
  };

  return (
    <div className="sidebar">
      <div>
        <div className="panel-title">Data Ingestion</div>
        <label className="upload-zone">
          <input type="file" onChange={(e) => setFile(e.target.files[0])} style={{display:'none'}} />
          {file ? (
            <div className="file-selected">
              <IconFile />
              <span style={{overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>
                {file.name}
              </span>
            </div>
          ) : (
            <>
              <div style={{color: '#94a3b8', marginBottom: '8px', display: 'flex', justifyContent: 'center'}}>
                <IconUpload />
              </div>
              <div className="upload-text">Click to upload</div>
              <div className="upload-subtext">PDF, Audio, Image, Text</div>
            </>
          )}
        </label>
        {file && (
          <button onClick={handleUpload} disabled={loadingUpload} className="btn-primary" style={{marginTop: '15px'}}>
            {loadingUpload ? <div className="spinner"></div> : "Analyze Document"}
          </button>
        )}
      </div>

      <div style={{marginTop: '30px'}}>
        <div className="panel-title">Knowledge Retrieval</div>
        <div className="search-container">
          <IconSearch />
          <input 
            className="search-input" 
            placeholder="Ask a question..." 
            value={q} 
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
        </div>
        <button onClick={handleSearch} disabled={loadingSearch} className="btn-primary" style={{marginTop: '10px', background: '#3b82f6'}}>
          {loadingSearch ? <div className="spinner"></div> : "Search Knowledge Base"}
        </button>
      </div>

      <div className="sidebar-footer">
        <a href="https://github.com/prarabdhapandey" target="_blank" rel="noopener noreferrer" className="github-link">
          <IconGithub />
          <span>Developed by Prarabdha Pandey</span>
        </a>
      </div>
    </div>
  );
}

// --- RESULT VIEW COMPONENT ---
function ResultView({ data, searchResults }) {
  const [tab, setTab] = useState("summary");

  if (searchResults) {
    return (
      <div className="content-area">
        <h2 style={{marginTop:0, display:'flex', alignItems:'center', gap:'10px'}}>
          <IconSearch /> Search Results
        </h2>
        {searchResults.results.length === 0 ? (
          <p style={{color: '#64748b'}}>No relevant documents found.</p>
        ) : (
          searchResults.results.map((r, i) => (
            <div key={i} className="search-result-card">
              <div className="search-meta">
                SOURCE: {r.source.split('/').pop()}
              </div>
              <p style={{margin:0, lineHeight: 1.6}}>{r.content}</p>
            </div>
          ))
        )}
      </div>
    );
  }

  if (!data) return (
    <div className="content-area empty-state">
      <div className="empty-icon" style={{color: '#cbd5e1'}}><IconBrain /></div>
      <h3>Climate Agent Ready</h3>
      <p>Upload a policy document, scientific chart, or podcast to begin analysis.</p>
    </div>
  );

  const s = data.summaries || {};
  const cost = data.cost_analysis || { estimated_cost_usd: 0, tokens: 0 };

  return (
    <div className="content-area">
      <div className="result-container">
        
        {/* Header Stats */}
        <div className="metrics-bar">
          <div className="metric">
            <span className="metric-label">File:</span>
            <span style={{fontWeight:600}}>{data.file.split('/').pop()}</span>
          </div>
          <div className="metric">
            <span className="metric-label">Type:</span>
            <span>{data.method}</span>
          </div>
          
          <div style={{flex:1}}></div>
          
          {/* COST AND TOKENS DISPLAY */}
          <div className="metric">
            <span className="metric-label">Est. Cost:</span>
            <span className="metric-value" style={{color: '#0d9488'}}>${cost.estimated_cost_usd}</span>
          </div>
          <div className="metric">
            <span className="metric-label">Tokens:</span>
            <span className="metric-value">{cost.tokens}</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs-nav">
          <button className={`tab-btn ${tab === 'summary' ? 'active' : ''}`} onClick={() => setTab('summary')}>
            <IconChart /> Executive Summary
          </button>
          <button className={`tab-btn ${tab === 'details' ? 'active' : ''}`} onClick={() => setTab('details')}>
            <IconFile /> Full Details
          </button>
          <button className={`tab-btn ${tab === 'logs' ? 'active' : ''}`} onClick={() => setTab('logs')}>
            <IconCode /> Agent Logs
          </button>
        </div>

        {/* Content */}
        <div className="tab-content">
          {tab === "summary" && (
            <div>
              <div className="panel-title" style={{marginBottom:'10px'}}>One-Line Overview</div>
              <div className="summary-one-liner">{s.one_line || "No summary available."}</div>
              
              <div className="panel-title" style={{marginBottom:'15px'}}>Key Takeaways</div>
              {(s.three_bullets || "").split("\n").map((b, i) => b.trim() && (
                <div key={i} className="bullet-item">
                  <div className="check-icon"><IconCheck /></div>
                  <div>{b}</div>
                </div>
              ))}

              <div style={{marginTop: '30px'}}>
                <span style={{background: data.sentiment?.label === 'positive' ? '#d1fae5' : '#f1f5f9', padding: '6px 12px', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 600, color: '#0f172a'}}>
                  Sentiment: {data.sentiment?.label?.toUpperCase()} ({data.sentiment?.score})
                </span>
              </div>
            </div>
          )}

          {tab === "details" && (
            <div>
              <div className="panel-title">Detailed Analysis</div>
              <p style={{lineHeight: 1.8, color: '#334155'}}>{s.five_sentence || "No details available."}</p>
            </div>
          )}

          {tab === "logs" && (
            <div className="logs-box">
              <div>// Agent Execution Path</div>
              <br/>
              {data.processing_log?.map((l, i) => (
                <div key={i}>&gt; {l}</div>
              ))}
              <br/>
              <div>&gt; Follow_up_needed: {String(data.follow_up_needed)}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// --- MAIN APP ---
function App() {
  const [analysisData, setAnalysisData] = useState(null);
  const [searchData, setSearchData] = useState(null);

  const handleUploadResult = (data) => {
    setAnalysisData(data);
    setSearchData(null);
  };

  const handleSearchResults = (data) => {
    setSearchData(data);
    setAnalysisData(null);
  };

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="logo">
          <div className="logo-icon"><IconBrain /></div>
          Climate RAG Agent
        </div>
        <div className="tagline">v1.0.0 • React + FastAPI + Vosk</div>
      </header>

      <div className="main-grid">
        <Sidebar onUploadResult={handleUploadResult} onSearchResults={handleSearchResults} />
        <ResultView data={analysisData} searchResults={searchData} />
      </div>
    </div>
  );
}

export default App;