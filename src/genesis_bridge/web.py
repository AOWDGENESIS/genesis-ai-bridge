from __future__ import annotations

import base64
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .config import BridgeConfig
from .orchestrator import BridgeOrchestrator


HTML = r'''<!doctype html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Genesis AI Bridge</title>
<style>
:root{color-scheme:dark;--bg:#10131a;--panel:#181d27;--line:#303847;--text:#edf2f7;--muted:#aab4c2;--accent:#7dd3fc;--ok:#86efac;--bad:#fca5a5;--warn:#fde68a}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px system-ui,sans-serif}main{max-width:1050px;margin:0 auto;padding:28px}section{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px;margin:16px 0}h1{margin:0 0 8px}h2{font-size:18px;margin-top:0}label{display:block;margin:12px 0 6px;color:var(--muted)}input[type=file],input[type=text],textarea,button{font:inherit}input[type=text]{width:100%;background:#0e1117;color:var(--text);border:1px solid var(--line);border-radius:8px;padding:10px}textarea{width:100%;min-height:120px;background:#0e1117;color:var(--text);border:1px solid var(--line);border-radius:8px;padding:10px}button{background:var(--accent);color:#071018;border:0;border-radius:8px;padding:10px 16px;cursor:pointer;font-weight:700;margin:6px 8px 6px 0}button.secondary{background:#334155;color:var(--text)}button.danger{background:#fca5a5;color:#26090b}button:disabled{opacity:.5;cursor:wait}.provider{display:inline-flex;gap:6px;margin:10px 18px 10px 0;color:var(--text)}#status{color:var(--muted);white-space:pre-wrap}.ok{color:var(--ok)}.bad{color:var(--bad)}.warn{color:var(--warn)}small{color:var(--muted)}pre{white-space:pre-wrap;overflow:auto;background:#0b0d12;border:1px solid var(--line);padding:14px;border-radius:8px;max-height:600px}#proposalBox{display:none}.hint{border-left:3px solid var(--accent);padding-left:10px;color:var(--muted)}.files{max-height:170px;overflow:auto;color:var(--muted);font-size:13px}
</style></head>
<body><main><h1>Genesis AI Bridge</h1><p><small>Quelle wählen → Aufgabe eingeben → prüfen → Vorschlag ansehen → Korrektur ausdrücklich bestätigen. Originale werden niemals überschrieben.</small></p>
<section><h2>Neue Prüfung</h2>
<label for="file">Dateien oder Browser-Ordner</label><input id="file" type="file" multiple webkitdirectory directory>
<div id="fileList" class="files">Noch keine Auswahl.</div>
<label for="sourcePath">Optionaler lokaler Quellpfad auf diesem Computer</label><input id="sourcePath" type="text" placeholder="z. B. C:\\Projekte\\Familien AI oder /home/user/projekt">
<p class="hint"><small>Für Korrekturen neben der echten Quelle muss der Bridge-Server diesen Pfad lesen können. Bei reinen Browser-Uploads bleibt der Originalpfad unbekannt; der Korrekturordner wird dann extern unter dem Bridge-Datenordner angelegt.</small></p>
<label for="programName">Programmbezeichnung für den Korrekturordner</label><input id="programName" type="text" placeholder="z. B. Familien AI">
<label for="task">Aufgabe</label><textarea id="task">Prüfe alle ausgewählten Dateien vollständig. Finde Fehler und Warnungen, ändere nichts ungefragt und gib einen ehrlichen GO/NO-GO-Bericht mit Tests und Unsicherheiten.</textarea>
<div><label>Provider</label><label class="provider"><input id="ollama" type="checkbox" checked> Ollama lokal</label><label class="provider"><input id="openclaw" type="checkbox"> OpenClaw</label><label class="provider"><input id="anthropic" type="checkbox"> Anthropic API</label></div>
<button id="run">Prüfung starten</button><p id="status">Bereit.</p></section>
<section><h2>Prüfergebnis</h2><pre id="result">Noch kein Lauf.</pre><div id="proposalBox"><h2>Korrekturvorschlag</h2><p class="hint">Es wurde bisher nichts geändert. Prüfe den Vorschlag. Erst der rote Bestätigungsbutton schreibt einen neuen Korrekturordner.</p><pre id="proposal"></pre><button id="apply" class="danger">Korrektur ausdrücklich bestätigen und neuen Ordner erstellen</button></div></section>
<script>
const el=id=>document.getElementById(id); const status=el('status'); const output=el('result'); const proposalBox=el('proposalBox'); const proposalOutput=el('proposal'); let currentRun=null; let currentProposal=null;
el('file').onchange=()=>{const files=[...el('file').files];el('fileList').textContent=files.length?files.map(x=>x.webkitRelativePath||x.name).join('\n'):'Noch keine Auswahl.'};
async function readFile(file){return await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve({path:file.webkitRelativePath||file.name,content_base64:String(r.result).split(',')[1]||''});r.onerror=reject;r.readAsDataURL(file)})}
async function request(path, body){const res=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await res.json();if(!res.ok)throw new Error(data.error||('HTTP '+res.status));return data}
el('run').onclick=async()=>{const files=[...el('file').files];const sourcePath=el('sourcePath').value.trim();if(!files.length&&!sourcePath){status.textContent='Bitte Dateien, einen Browser-Ordner oder einen lokalen Quellpfad wählen.';status.className='bad';return}const providers=['ollama','openclaw','anthropic'].filter(x=>el(x).checked);el('run').disabled=true;el('apply').disabled=true;proposalBox.style.display='none';status.textContent='Läuft… jedes Bundle-Element wird als eigener Prüfeintrag behandelt.';status.className='';try{const uploads=[];for(const file of files)uploads.push(await readFile(file));const data=await request('/api/run',{uploads,source_path:sourcePath||null,name:files.length===1?files[0].name:'Browser-Auswahl',program_name:el('programName').value.trim()||null,task:el('task').value,providers});currentRun=data;output.textContent=JSON.stringify(data,null,2);await makeProposal()}catch(e){status.textContent='Fehler: '+e;status.className='bad'}finally{el('run').disabled=false}};
async function makeProposal(){if(!currentRun)return;status.textContent='Korrekturvorschlag wird erstellt…';status.className='';try{currentProposal=await request('/api/propose',{run_id:currentRun.run_id,program_name:el('programName').value.trim()||null});proposalOutput.textContent=JSON.stringify(currentProposal,null,2);proposalBox.style.display='block';const hasChanges=Boolean(currentProposal.changes&&currentProposal.changes.length);el('apply').disabled=!hasChanges;status.textContent=hasChanges?'Vorschlag bereit. Es wurde noch nichts geändert.':'Kein sicherer Änderungsvorschlag vorhanden.';status.className=hasChanges?'warn':'ok'}catch(e){el('apply').disabled=true;status.textContent='Fehler beim Vorschlag: '+e;status.className='bad'}}
el('apply').onclick=async()=>{if(!currentProposal)return;if(!confirm('Wirklich anwenden? Es wird ein neuer Korrekturordner erstellt; die Originale bleiben unverändert.'))return;el('apply').disabled=true;status.textContent='Korrektur wird in einem neuen Ordner erstellt…';try{const data=await request('/api/apply',{proposal_id:currentProposal.proposal_id,confirmed:true});proposalOutput.textContent=JSON.stringify(data,null,2);status.textContent='Korrektur erstellt: '+data.target_path;status.className='ok'}catch(e){status.textContent='Korrektur nicht angewendet: '+e;status.className='bad'}finally{el('apply').disabled=false}};
</script></main></body></html>'''


class _Handler(BaseHTTPRequestHandler):
    config: BridgeConfig
    orchestrator: BridgeOrchestrator

    def _send(self, status: int, value: Any, content_type: str = "application/json; charset=utf-8") -> None:
        data = value.encode("utf-8") if isinstance(value, str) else json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        max_length = self.config.max_bundle_bytes * 2 + 2_000_000
        if length <= 0 or length > max_length:
            raise ValueError("Request ist leer oder zu groß.")
        value = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Request muss ein JSON-Objekt sein.")
        return value

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/" or self.path == "/index.html":
            self._send(200, HTML, "text/html; charset=utf-8")
            return
        if self.path == "/api/health":
            self._send(200, {"ok": True, "service": "genesis-ai-bridge"})
            return
        if self.path == "/api/latest":
            value = self.orchestrator.latest()
            self._send(200, value or {"status": "empty"})
            return
        self._send(404, {"error": "Nicht gefunden"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            if self.path == "/api/run":
                body = self._body()
                source_path = str(body.get("source_path") or "").strip()
                providers = body.get("providers")
                task = str(body.get("task") or "Prüfe das Bundle vollständig.")
                program_name = str(body.get("program_name") or "").strip() or None
                if source_path:
                    result = self.orchestrator.run_path(source_path, task, providers, program_name)
                else:
                    raw_uploads = body.get("uploads") or []
                    if not isinstance(raw_uploads, list):
                        raise ValueError("uploads muss eine Liste sein.")
                    uploads: list[tuple[str, bytes]] = []
                    for item in raw_uploads:
                        if not isinstance(item, dict):
                            raise ValueError("Ein Upload-Eintrag ist ungültig.")
                        name = str(item.get("path") or item.get("filename") or "datei.bin")
                        encoded = str(item.get("content_base64") or "")
                        uploads.append((name, base64.b64decode(encoded, validate=True)))
                    result = self.orchestrator.run_uploads(uploads, task, providers, str(body.get("name") or "Browser-Auswahl"), program_name)
                self._send(200, result.as_dict())
                return
            if self.path == "/api/propose":
                body = self._body()
                proposal = self.orchestrator.propose_corrections(str(body.get("run_id") or ""), str(body.get("program_name") or "").strip() or None)
                self._send(200, proposal.as_dict())
                return
            if self.path == "/api/apply":
                body = self._body()
                confirmed = body.get("confirmed") is True
                result = self.orchestrator.apply_corrections(str(body.get("proposal_id") or ""), confirmed)
                self._send(200, result)
                return
            self._send(404, {"error": "Nicht gefunden"})
        except Exception as exc:
            self._send(400, {"error": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def serve(config: BridgeConfig, host: str = "127.0.0.1", port: int = 8787) -> None:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Die Weboberfläche bindet absichtlich nur an Loopback.")
    handler = type("GenesisBridgeHandler", (_Handler,), {})
    handler.config = config
    handler.orchestrator = BridgeOrchestrator(config)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Genesis AI Bridge: http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
