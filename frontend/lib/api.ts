// Define an interface for the project creation payload for type safety
interface CreateProjectPayload {
  project_name?: string;
  molecule_names?: string;
  therapeutic_area?: string;
  key_differentiating_benefits?: string;
  natural_language_prompt?: string;
}

export async function createProject(data: CreateProjectPayload) {
  const res = await fetch("http://localhost:5040/api/projects/create", { // TODO: Use environment variable for API base URL
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ message: "Failed to create project. Server response not readable." }));
    throw new Error(errorData.message || `Failed to create project. Status: ${res.status}`);
  }
  return await res.json();
}

export async function fetchProjects(userId?: string) {
  let url = "http://localhost:5040/api/projects/list";
  if (userId) {
    url += `?user_id=${userId}`;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch projects");
  return await res.json();
}

export async function fetchProjectById(id: string) {
  const res = await fetch(`http://localhost:5040/api/projects/${id}`);
  if (!res.ok) throw new Error("Failed to fetch project");
  return await res.json();
}

export async function updateBrandName(projectId: string, brandName: string) {
  const res = await fetch(`http://localhost:5040/api/projects/${projectId}/brand_name`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(brandName)
  });
  if (!res.ok) throw new Error("Failed to update brand name");
  return await res.json();
}

export async function updateSlogan(projectId: string, slogan: string) {
  const res = await fetch(`http://localhost:5040/api/projects/${projectId}/slogan`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(slogan)
  });
  if (!res.ok) throw new Error("Failed to update slogan");
  return await res.json();
}

export async function updateLeaflet(projectId: string, leaflet: string) {
  const res = await fetch(`http://localhost:5040/api/projects/${projectId}/leaflet`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(leaflet)
  });
  if (!res.ok) throw new Error("Failed to update leaflet");
  return await res.json();
}

export async function requestCompliance(projectId: string) {
  const res = await fetch(`http://localhost:5040/api/projects/${projectId}/compliance_check`, {
    method: "POST"
  });
  if (!res.ok) throw new Error("Failed to request compliance check");
  return await res.json();
}

export async function exportLeafletPDF(projectId: string) {
  const res = await fetch(`http://localhost:5040/api/projects/${projectId}/export/pdf`);
  if (!res.ok) throw new Error("Failed to export PDF");
  return await res.json();
}
