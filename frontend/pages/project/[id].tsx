import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { fetchProjectById } from "../../lib/api";

import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { fetchProjectById, updateBrandName, updateSlogan, updateLeaflet, requestCompliance, exportLeafletPDF } from "../../lib/api";

export default function ProjectPage() {
  const router = useRouter();
  const { id } = router.query;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [brandName, setBrandName] = useState("");
  const [slogan, setSlogan] = useState("");
  const [leafletContent, setLeafletContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [complianceStatus, setComplianceStatus] = useState(""); // TODO: Re-evaluate how complianceStatus is fetched and updated with new backend schema

  // TODO: The save/update/export functions below are linked to backend endpoints
  // that might need updating to align with the new brand_elements schema.
  // For now, they might not work as expected. This needs to be addressed in a future step.

  useEffect(() => {
    if (!id) return;
    fetchProjectById(id as string)
      .then(res => {
        setData(res);
        setBrandName(res?.brand_package?.brand_names?.[0] || "");
        setSlogan(res?.brand_package?.slogans?.[0]?.en || "");
        setLeafletContent(res?.brand_package?.leaflet_json?.sections?.[0]?.content || "");
        setComplianceStatus(res?.brand_package?.compliance_status || "pending");
      })
      .catch(() => setError("Failed to fetch project."))
      .finally(() => setLoading(false));
  }, [id]);

  const handleSaveBrandName = async () => {
    setSaving(true); setFeedback("");
    try {
      await updateBrandName(id as string, brandName);
      setFeedback("Brand name saved!");
    } catch {
      setFeedback("Failed to save brand name.");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveSlogan = async () => {
    setSaving(true); setFeedback("");
    try {
      await updateSlogan(id as string, slogan);
      setFeedback("Slogan saved!");
    } catch {
      setFeedback("Failed to save slogan.");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveLeaflet = async () => {
    setSaving(true); setFeedback("");
    try {
      await updateLeaflet(id as string, leafletContent);
      setFeedback("Leaflet saved!");
    } catch {
      setFeedback("Failed to save leaflet.");
    } finally {
      setSaving(false);
    }
  };

  const handleRequestCompliance = async () => {
    setSaving(true); setFeedback("");
    try {
      const res = await requestCompliance(id as string);
      setFeedback("Compliance check requested!");
      setComplianceStatus(res.status || "approved");
    } catch {
      setFeedback("Failed to request compliance check.");
    } finally {
      setSaving(false);
    }
  };

  const handleExportPDF = async () => {
    setFeedback("");
    try {
      const res = await exportLeafletPDF(id as string);
      if (res.url) window.open(res.url, "_blank");
      else setFeedback("Export failed.");
    } catch {
      setFeedback("Export failed.");
    }
  };

  const handleExportLogo = (url: string) => {
    window.open(url, "_blank");
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;
  if (!data || !data.project) return <div>Project not found.</div>;

  const { project, insights, brand_package } = data;

  return (
    <div>
      <h1>{project.name || project.molecule || "Untitled Project"}</h1>
      <h3>Therapeutic Area: {project.therapeutic_area}</h3>
      <h4>Molecule(s): {project.molecule}</h4>
      {project.benefits && <p><b>Benefits:</b> {project.benefits}</p>}
      <hr />
      <h2>Strategic Insights</h2>
      <ul>
        <li><b>Competitors:</b> {insights?.competitors?.join(", ")}</li>
        <li><b>Brand Positioning:</b> {insights?.brand_positioning}</li>
        <li><b>Color Palette:</b> {insights?.color_palette?.map((c: any) => (
          <span key={c.hex} style={{ background: c.hex, color: '#fff', padding: '2px 8px', marginRight: 8, borderRadius: 4 }}>
            {c.name}
          </span>
        ))}</li>
        <li><b>Clinical Trials:</b> {insights?.clinical_trials?.map((t: any) => t.name).join(", ")}</li>
      </ul>
      <hr />
      <h2>Brand Package</h2>
      <div>
        <b>Brand Name:</b>
        <input
          style={{ margin: '0 8px 8px 0', padding: 4 }}
          value={brand_package?.brand_names?.[0] || ''}
          onChange={e => setBrandName(e.target.value)}
        />
        <button onClick={handleSaveBrandName}>Save</button>
        <br />
        <b>Logo:</b>
        <div style={{ display: 'flex', gap: 16, marginBottom: 8 }}>
          {brand_package?.logo_concepts?.map((logo: any, idx: number) => (
            <div key={idx} style={{ border: '1px solid #eee', padding: 8, borderRadius: 8 }}>
              <img src={logo.url} alt={`Logo concept ${idx + 1}`} style={{ width: 100, height: 100, objectFit: 'contain', background: '#f9f9f9' }} />
              <button onClick={() => handleExportLogo(logo.url)}>Export Logo</button>
            </div>
          ))}
        </div>
        <b>Slogan:</b>
        <input
          style={{ margin: '0 8px 8px 0', padding: 4 }}
          value={brand_package?.slogans?.[0]?.en || ''}
          onChange={e => setSlogan(e.target.value)}
        />
        <button onClick={handleSaveSlogan}>Save</button>
        <br />
        <b>Leaflet Draft:</b>
        <textarea
          style={{ width: '100%', minHeight: 80, marginBottom: 8 }}
          value={leafletContent}
          onChange={e => setLeafletContent(e.target.value)}
        />
        <button onClick={handleSaveLeaflet}>Save</button>
        <button onClick={handleExportPDF} style={{ marginLeft: 8 }}>Export as PDF</button>
        <div style={{ border: '1px solid #eee', padding: 12, marginTop: 8, borderRadius: 6 }}>
          {brand_package?.leaflet_json?.sections?.map((section: any, idx: number) => (
            <div key={idx} style={{ marginBottom: 14 }}>
              <h4 style={{ margin: 0 }}>{section.title}</h4>
              <div>{section.content}</div>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 16 }}>
          <b>Compliance Status:</b> {brand_package?.compliance_status || 'pending'}
          <button onClick={handleRequestCompliance} style={{ marginLeft: 8 }}>Request Compliance Check</button>
        </div>
      </div>
    </div>
  );
}
