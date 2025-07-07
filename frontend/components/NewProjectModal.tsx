import { useState } from "react";
import { createProject } from "../lib/api";

export default function NewProjectModal({ onClose, onProjectCreated }) {
  const [form, setForm] = useState({
    product_name: "",
    molecule: "",
    therapeutic_area: "",
    benefits: "",
    prompt: ""
  });
  const [loading, setLoading] = useState(false);

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    const res = await createProject(form);
    setLoading(false);
    onProjectCreated(res.project); // Pass project object from backend
  };

  return (
    <div className="modal">
      <form onSubmit={handleSubmit}>
        <h2>New Project</h2>
        <input name="product_name" placeholder="Product Name (optional)" value={form.product_name} onChange={handleChange} />
        <input name="molecule" placeholder='Molecule(s) e.g. "Empagliflozin 10mg + Linagliptin 5mg"' value={form.molecule} onChange={handleChange} required />
        <input name="therapeutic_area" placeholder='Therapeutic Area e.g. "Type 2 Diabetes"' value={form.therapeutic_area} onChange={handleChange} required />
        <input name="benefits" placeholder="Key Differentiating Benefits (optional)" value={form.benefits} onChange={handleChange} />
        <textarea name="prompt" placeholder='Or describe in natural language...' value={form.prompt} onChange={handleChange} />
        <button type="submit" disabled={loading}>{loading ? "Creating..." : "Create"}</button>
        <button type="button" onClick={onClose}>Cancel</button>
      </form>
    </div>
  );
}
