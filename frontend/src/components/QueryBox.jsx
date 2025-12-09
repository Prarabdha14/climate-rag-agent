import { useState } from "react";
import axios from "axios";

export default function QueryBox({ onResults }) {
  const [query, setQuery] = useState("");

  const runQuery = async () => {
    if (!query) return;

    const res = await axios.post("http://localhost:8000/query", {
      query,
    });

    onResults(res.data);
  };

  return (
    <div style={{ marginTop: "40px" }}>
      <h3>Search Knowledge Base</h3>
      <input
        placeholder="Ask a climate question..."
        style={{ width: "320px", marginRight: "10px" }}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={runQuery}>Search</button>
    </div>
  );
}