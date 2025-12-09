import { useState } from "react";
import axios from "axios";

export default function FileUpload({ onResult }) {
  const [file, setFile] = useState(null);

  const handleUpload = async () => {
    if (!file) return alert("Select a file first!");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://localhost:8000/process", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onResult(res.data);
    } catch (err) {
      console.error(err);
      alert("Upload failed");
    }
  };

  return (
    <div style={{ marginBottom: "20px" }}>
      <h3>Upload File</h3>
      <input
        type="file"
        onChange={(e) => setFile(e.target.files[0])}
        style={{ marginRight: "10px" }}
      />
      <button onClick={handleUpload}>Process</button>
    </div>
  );
}