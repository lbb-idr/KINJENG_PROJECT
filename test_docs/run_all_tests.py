"""
Run all 5 simulation types (Academic, Business, Political, Social, Custom)
Each: ontology -> graph -> simulation -> survey
PDF generation will be done on Railway after deploy.
"""
import requests
import json
import os
import sys
import time
import re

BASE = "http://localhost:5001"
DOC_DIR = os.path.join(os.path.dirname(__file__))
RESULTS = {}

def log(step, msg, color="cyan"):
    colors = {"cyan": "\033[96m", "green": "\033[92m", "yellow": "\033[93m", "red": "\033[91m", "reset": "\033[0m"}
    c = colors.get(color, "")
    r = colors["reset"]
    print(f"{c}[{step}]{r} {msg}")

def api(method, path, **kwargs):
    url = f"{BASE}{path}"
    timeout = kwargs.pop("timeout", 30)
    for attempt in range(3):
        try:
            r = requests.request(method, url, timeout=timeout, **kwargs)
            if r.status_code >= 500:
                log("RETRY", f"Got {r.status_code}, retry {attempt+1}/3", "yellow")
                time.sleep(3)
                continue
            return r
        except requests.Timeout:
            log("RETRY", f"Timeout after {timeout}s, retry {attempt+1}/3", "yellow")
            time.sleep(5)
        except Exception as e:
            log("ERROR", f"{e}", "red")
            return None
    return None

def step1_ontology(sim_type, requirement, filename):
    log("STEP1", f"Ontology for {sim_type}...")
    filepath = os.path.join(DOC_DIR, filename)
    with open(filepath, "rb") as f:
        files = {"files": (filename, f, "text/plain")}
        data = {
            "simulation_requirement": requirement,
            "simulation_type": sim_type,
            "project_name": f"Test {sim_type.title()}",
        }
        r = api("POST", "/api/graph/ontology/generate", files=files, data=data, timeout=180)
        if r and r.json().get("success"):
            j = r.json()["data"]
            log("STEP1", f"Project: {j['project_id']}, entities: {len(j['ontology']['entity_types'])}", "green")
            types = [e["name"] for e in j["ontology"]["entity_types"]]
            log("STEP1", f"  Types: {types}", "yellow")
            return j["project_id"]
        else:
            err = r.json() if r else "No response"
            log("STEP1", f"FAILED: {err}", "red")
            return None

def step2_graph(project_id):
    log("STEP2", f"Build graph for {project_id}...")
    r = api("POST", "/api/graph/build", json={"project_id": project_id}, timeout=10)
    if not r or not r.json().get("success"):
        log("STEP2", f"FAILED: {r.text if r else 'No response'}", "red")
        return None
    
    task_id = r.json()["data"]["task_id"]
    for _ in range(60):
        time.sleep(2)
        r = api("GET", f"/api/graph/task/{task_id}")
        if not r: continue
        j = r.json()
        if j.get("data", {}).get("status") == "completed":
            graph_id = j["data"]["result"]["graph_id"]
            log("STEP2", f"Graph built: {graph_id}", "green")
            return graph_id
        if j.get("data", {}).get("status") == "failed":
            log("STEP2", f"FAILED: {j['data'].get('error', '')}", "red")
            return None
    log("STEP2", "TIMEOUT", "red")
    return None

def step3_simulation(project_id, graph_id, sim_type):
    log("STEP3", f"Create simulation...")
    r = api("POST", "/api/simulation/create", json={
        "project_id": project_id, "graph_id": graph_id,
        "enable_twitter": True, "enable_reddit": False, "sim_type": sim_type
    })
    if not r or not r.json().get("success"):
        log("STEP3", f"Create FAILED: {r.text if r else 'No response'}", "red")
        return None
    sim_id = r.json()["data"]["simulation_id"]
    log("STEP3", f"Sim: {sim_id}", "green")

    log("STEP3", f"Prepare simulation...")
    r = api("POST", "/api/simulation/prepare", json={
        "simulation_id": sim_id, "use_llm_for_profiles": False, "parallel_profile_count": 3
    }, timeout=30)
    if not r or not r.json().get("success"):
        log("STEP3", f"Prepare FAILED: {r.text if r else 'No response'}", "red")
        return None

    task_id = r.json()["data"]["task_id"]
    for _ in range(30):
        time.sleep(3)
        r = api("POST", "/api/simulation/prepare/status", json={"task_id": task_id})
        if not r: continue
        j = r.json()
        status = j.get("data", {}).get("status")
        progress = j.get("data", {}).get("progress", 0)
        if status == "completed":
            log("STEP3", f"Prepare done!", "green")
            break
        if status == "failed":
            log("STEP3", f"Prepare FAILED: {j['data'].get('error','')}", "red")
            return None
        log("STEP3", f"Preparing... {progress}%", "yellow")
    
    log("STEP3", f"Run simulation (2 rounds)...")
    r = api("POST", "/api/simulation/start", json={
        "simulation_id": sim_id, "platform": "parallel",
        "force": True, "enable_graph_memory_update": False, "max_rounds": 2
    })
    if not r:
        log("STEP3", "Start call failed", "red")
        return None

    for _ in range(120):
        time.sleep(5)
        r = api("GET", f"/api/simulation/{sim_id}/run-status")
        if not r: continue
        j = r.json().get("data", {})
        status = j.get("runer_status") or j.get("runner_status", "")
        err = j.get("error", "")
        if err and "Callable" in err:
            log("STEP3", "Callable bug detected - need to fix!", "red")
            return None
        if status == "completed":
            log("STEP3", "Simulation completed!", "green")
            return sim_id
        if status == "failed":
            log("STEP3", f"FAILED: {err}", "red")
            return None
    log("STEP3", "TIMEOUT", "red")
    return None

def step4_survey(project_id, requirement, sim_type):
    log("STEP4", f"Generate survey for {sim_type}...")
    r = api("POST", "/api/survey/generate", json={
        "requirement": requirement, "sim_type": sim_type,
        "params": {"likertScale": 5, "agentCount": 5}
    }, timeout=120)
    if not r or not r.json().get("success"):
        err = r.text if r else "No response"
        if "not defined" in err:
            log("STEP4", f"NameError bug detected: {err[:100]}", "red")
        else:
            log("STEP4", f"FAILED: {err[:200]}", "red")
        return None
    
    survey_data = r.json()["data"]
    log("STEP4", f"Survey: {survey_data.get('title', '?')}, {len(survey_data.get('sections',[]))} sections", "green")
    
    # Save raw survey
    survey_only = json.dumps(survey_data)
    
    log("STEP4", f"Run survey...")
    body = f'{{"project_id": "{project_id}", "survey": {survey_only}, "agent_count": 5, "use_llm": false, "save_results": true}}'
    headers = {"Content-Type": "application/json"}
    r = api("POST", "/api/survey/run", data=body, headers=headers, timeout=120)
    if r and r.json().get("success"):
        j = r.json()["data"]
        log("STEP4", f"Survey done! {j.get('total_agents','?')} agents, {j.get('total_questions','?')} questions", "green")
        return True
    else:
        log("STEP4", f"FAILED: {r.text[:200] if r else 'No response'}", "red")
        return None

# ====== Run all types ======
TYPES = [
    ("academic", "Dampak kebijakan merdeka belajar terhadap mahasiswa dan dosen", "academic.txt"),
    ("business", "Analisis persaingan e-commerce di Indonesia: strategi perusahaan dan perilaku konsumen", "business.txt"),
    ("political", "Pengaruh media sosial terhadap polarisasi politik pemilih pemula", "political.txt"),
    ("social", "Dampak media sosial terhadap gaya hidup dan interaksi sosial masyarakat", "social.txt"),
    ("custom", "Pengembangan aplikasi AI untuk deteksi dini bencana alam menggunakan machine learning", "custom.txt"),
]

ALL_RESULTS = {}

for sim_type, requirement, filename in TYPES:
    log("---", f"\n{'='*60}\nRUNNING: {sim_type.upper()}\n{'='*60}", "cyan")
    
    pid = step1_ontology(sim_type, requirement, filename)
    if not pid:
        ALL_RESULTS[sim_type] = {"status": "FAILED", "step": "ontology"}
        continue
    
    gid = step2_graph(pid)
    if not gid:
        ALL_RESULTS[sim_type] = {"status": "FAILED", "step": "graph", "project_id": pid}
        continue
    
    sid = step3_simulation(pid, gid, sim_type)
    if not sid:
        ALL_RESULTS[sim_type] = {"status": "FAILED", "step": "simulation", "project_id": pid, "graph_id": gid}
        continue
    
    ok = step4_survey(pid, requirement, sim_type)
    if not ok:
        ALL_RESULTS[sim_type] = {"status": "FAILED", "step": "survey", "project_id": pid, "graph_id": gid, "sim_id": sid}
        continue
    
    ALL_RESULTS[sim_type] = {
        "status": "COMPLETED",
        "project_id": pid,
        "graph_id": gid,
        "sim_id": sid
    }
    log("---", f"{sim_type.upper()} COMPLETED! ✅", "green")

# Print summary
print("\n" + "="*60)
print("FINAL RESULTS")
print("="*60)
for t, r in ALL_RESULTS.items():
    s = r["status"]
    color = "\033[92m" if s == "COMPLETED" else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{t:12s}: {s:12s} | project={r.get('project_id',''):20s}{reset}")
