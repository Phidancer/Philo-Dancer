'use client';

import { useState } from 'react';

const steps = ['A. Background', 'B. Form/Interruption', 'C. Harmonic Pillars', 'D. Voice-leading', 'E. Embellishments', 'F. Surface Render'];

export default function Home() {
  const [projectId, setProjectId] = useState<string>('');
  const [active, setActive] = useState(0);
  const [artifact, setArtifact] = useState<any>(null);

  async function createProject() {
    const res = await fetch('http://localhost:8000/projects', {method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({})});
    const p = await res.json();
    setProjectId(p.id);
  }

  async function runStep() {
    if (!projectId) await createProject();
    const step = Math.min(active + 1, 6);
    const pid = projectId || (await (await fetch('http://localhost:8000/projects', {method:'POST', headers:{'content-type':'application/json'}, body:'{}'})).json()).id;
    setProjectId(pid);
    const res = await fetch(`http://localhost:8000/projects/${pid}/generate/step/${step}`, {method:'POST'});
    const data = await res.json();
    setArtifact(data.artifact);
    setActive(step - 1);
  }

  return (
    <>
      <div className="topbar">
        <button onClick={runStep}>Run Step</button>
        <span>Project: {projectId || 'not created'}</span>
        <span>BPM 96 · Loop 1-8</span>
      </div>
      <main>
        <section className="panel">
          <h3>Stepper</h3>
          {steps.map((s, i) => <div key={s} className={`step ${i===active?'active':''}`}>{s}</div>)}
        </section>
        <section className="panel">
          <h3>Visualization</h3>
          <p>Tabs: Graph · Piano-roll · Score</p>
          <div className="canvas">Graph placeholder with interruption notation: // + broken beam at bar 8.</div>
          <pre>{artifact ? JSON.stringify(artifact.validation, null, 2) : 'Run a step to view artifact + validator report.'}</pre>
        </section>
        <section className="panel">
          <h3>Layer Stack</h3>
          <p>Background / Middleground / Foreground / Surface</p>
          <ul>
            <li>Mute/Solo + Volume + Instrument controls (scaffolded)</li>
          </ul>
          {artifact?.validation?.issues?.map((x:any, idx:number) => <div key={idx} className="issue">{x.validator}: {x.message}</div>)}
        </section>
      </main>
    </>
  );
}
