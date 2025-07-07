import { useState } from "react";
import { createProject } from "../lib/api"; // We'll check this api call later

// Define a type for the form state for better type safety
interface NewProjectFormState {
  project_name: string; // Matches Supabase schema 'project_name'
  molecule_names: string; // Matches Supabase schema 'molecule_names'
  therapeutic_area: string;
  key_differentiating_benefits: string; // Matches Supabase schema 'key_differentiating_benefits'
  natural_language_prompt: string; // For the natural language input
}

interface NewProjectModalProps {
  onClose: () => void;
  onProjectCreated: (project: any) => void; // Consider defining a Project type later
}

export default function NewProjectModal({ onClose, onProjectCreated }: NewProjectModalProps) {
  const [form, setForm] = useState<NewProjectFormState>({
    project_name: "",
    molecule_names: "",
    therapeutic_area: "",
    key_differentiating_benefits: "",
    natural_language_prompt: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Basic validation: Ensure either structured fields or natural language prompt is provided.
    // Molecule and Therapeutic Area are marked as required if not using natural language prompt.
    if (!form.natural_language_prompt && (!form.molecule_names || !form.therapeutic_area)) {
      setError("Please provide Molecule(s) and Therapeutic Area, or use the natural language prompt.");
      setLoading(false);
      return;
    }

    try {
      // The data sent to the backend should match what the endpoint expects.
      // If natural_language_prompt is filled, it might be the primary source of data.
      const payload = {
        project_name: form.project_name,
        molecule_names: form.molecule_names,
        therapeutic_area: form.therapeutic_area,
        key_differentiating_benefits: form.key_differentiating_benefits,
        natural_language_prompt: form.natural_language_prompt,
      };
      const projectData = await createProject(payload); // createProject should return the created project data
      setLoading(false);
      if (projectData) { // Assuming createProject returns null or throws error on failure
        onProjectCreated(projectData); // Pass project object from backend
        onClose(); // Close modal on successful creation
      } else {
        setError("Failed to create project. Please try again."); // Fallback error
      }
    } catch (err) {
      setLoading(false);
      setError(err.message || "An unexpected error occurred.");
      console.error("Project creation failed:", err);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"> {/* Basic modal styling */}
      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-lg">
        <form onSubmit={handleSubmit}>
          <h2 className="text-2xl font-semibold mb-4">Create New Project</h2>
          {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4" role="alert">{error}</div>}

          <div className="mb-4">
            <label htmlFor="project_name" className="block text-sm font-medium text-gray-700">Product Name (Optional)</label>
            <input
              type="text"
              name="project_name"
              id="project_name"
              placeholder="e.g., CardiaPro"
              value={form.project_name}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>

          <div className="mb-4">
            <label htmlFor="molecule_names" className="block text-sm font-medium text-gray-700">Molecule(s) *</label>
            <input
              type="text"
              name="molecule_names"
              id="molecule_names"
              placeholder="e.g., Empagliflozin 10mg + Linagliptin 5mg"
              value={form.molecule_names}
              onChange={handleChange}
              // `required` is handled by custom validation if natural_language_prompt is empty
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>

          <div className="mb-4">
            <label htmlFor="therapeutic_area" className="block text-sm font-medium text-gray-700">Therapeutic Area *</label>
            <input
              type="text"
              name="therapeutic_area"
              id="therapeutic_area"
              placeholder="e.g., Type 2 Diabetes"
              value={form.therapeutic_area}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>

          <div className="mb-4">
            <label htmlFor="key_differentiating_benefits" className="block text-sm font-medium text-gray-700">Key Differentiating Benefits (Optional)</label>
            <input
              type="text"
              name="key_differentiating_benefits"
              id="key_differentiating_benefits"
              placeholder="e.g., Superior cardiovascular outcomes"
              value={form.key_differentiating_benefits}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>

          <div className="my-4 text-center text-sm text-gray-500">OR</div>

          <div className="mb-6">
            <label htmlFor="natural_language_prompt" className="block text-sm font-medium text-gray-700">Describe in Natural Language</label>
            <textarea
              name="natural_language_prompt"
              id="natural_language_prompt"
              rows={3}
              placeholder='e.g., Launch new T2D product. Molecule: Empagliflozin 10mg + Linagliptin 5mg. Benefits: renal protection.'
              value={form.natural_language_prompt}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>

          <div className="flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? "Creating..." : "Create Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
