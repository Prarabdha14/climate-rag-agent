export default function SummaryViewer({ result }) {
  if (!result) return null;

  const s = result.summaries || {};

  return (
    <div style={{ marginTop: "20px" }}>
      <h2>Summary Output</h2>

      <h3>One Line</h3>
      <p>{s.one_line || "—"}</p>

      <h3>Three Bullets</h3>
      <ul>
        {(s.three_bullets || "")
          .split("\n")
          .filter((x) => x.trim() !== "")
          .map((b, i) => (
            <li key={i}>{b}</li>
          ))}
      </ul>

      <h3>Five Sentences</h3>
      <p>{s.five_sentence || "—"}</p>

      <h3>Sentiment</h3>
      <p>
        {result.sentiment?.label} ({result.sentiment?.score})
      </p>

      <h3>Follow-Up Needed?</h3>
      <p>{String(result.follow_up_needed)}</p>

      <h3>Processing Logs</h3>
      <pre>{JSON.stringify(result.processing_log, null, 2)}</pre>
    </div>
  );
}