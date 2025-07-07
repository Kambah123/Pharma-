import { useState, useEffect } from "react";
import NewProjectModal from "../components/NewProjectModal";
import { useRouter } from "next/router";
import { fetchProjects } from "../lib/api";
import { supabase } from "../utils/supabaseClient";

export default function Dashboard() {
  const [showModal, setShowModal] = useState(false);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    const session = supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.replace("/login");
      } else {
        setUser(data.session.user);
        fetchProjects(data.session.user.id)
          .then((data) => setProjects(data.projects || []))
          .finally(() => setLoading(false));
      }
    });
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.replace("/login");
  };

  const handleProjectCreated = (project: any) => {
    setShowModal(false);
    router.push(`/project/${project.id}`);
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>PharmaBrand AI Dashboard</h1>
      <button onClick={() => setShowModal(true)}>Create New Project</button>
      {showModal && (
        <NewProjectModal
          onClose={() => setShowModal(false)}
          onProjectCreated={handleProjectCreated}
        />
      )}
      <h2>My Projects</h2>
      {loading ? (
        <p>Loading...</p>
      ) : projects.length === 0 ? (
        <p>No projects found.</p>
      ) : (
        <ul>
          {projects.map((project) => (
            <li key={project.id}>
              <a href={`/project/${project.id}`} style={{ textDecoration: 'underline', color: 'blue' }}>
                {project.name || project.molecule || "Untitled Project"} - {project.therapeutic_area}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
