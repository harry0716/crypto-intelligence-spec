from __future__ import annotations

import json
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Type
from urllib.parse import urlparse

from crypto_intel.config import AppConfig
from crypto_intel.services.rapid_assessment import ManualAssessmentInput, RapidAssessmentService


def create_server(config: AppConfig, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    service = RapidAssessmentService(config)
    handler = _handler_for(service)
    return ThreadingHTTPServer((host, port), handler)


def run_server(config: AppConfig, host: str = "127.0.0.1", port: int = 8765) -> None:
    server = create_server(config, host, port)
    print(f"Crypto Intelligence 工作台已啟動：http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n工作台已停止。")
    finally:
        server.server_close()


def _handler_for(service: RapidAssessmentService) -> Type[BaseHTTPRequestHandler]:
    class WorkbenchHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - standard library handler method.
            path = urlparse(self.path).path
            if path == "/":
                self._send_html(WORKBENCH_HTML)
                return
            if path == "/api/recent":
                self._send_json({"items": service.recent_assessments()})
                return
            if path.startswith("/artifacts/"):
                filename = path.removeprefix("/artifacts/")
                if not re.fullmatch(r"rapid-\d{8}T\d{6}-[a-f0-9]{8}\.html", filename):
                    self._send_json({"error": "找不到指定報告。"}, HTTPStatus.NOT_FOUND)
                    return
                artifact = service.config.report_output_dir / "rapid" / filename
                if not artifact.is_file():
                    self._send_json({"error": "找不到指定報告。"}, HTTPStatus.NOT_FOUND)
                    return
                self._send_html(artifact.read_text(encoding="utf-8"))
                return
            self._send_json({"error": "找不到指定頁面。"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802 - standard library handler method.
            if urlparse(self.path).path != "/api/assess":
                self._send_json({"error": "找不到指定頁面。"}, HTTPStatus.NOT_FOUND)
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                if content_length <= 0 or content_length > 16_384:
                    raise ValueError("請提交有效且小於 16KB 的內容。")
                payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("請提交 JSON 物件。")
                result = service.assess(ManualAssessmentInput.from_payload(payload))
                self._send_json(result, HTTPStatus.CREATED)
            except (ValueError, json.JSONDecodeError) as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except Exception:  # noqa: BLE001 - keep local UI errors from exposing internals.
                self._send_json({"error": "研判暫時無法完成，請稍後重試。"}, HTTPStatus.INTERNAL_SERVER_ERROR)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003 - avoid request logs containing user input.
            return

        def _send_html(self, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

        def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

    return WorkbenchHandler


WORKBENCH_HTML = r'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crypto Intelligence 即時工作台</title>
<style>
:root{--ink:#17232c;--muted:#60717c;--paper:#f5f6f2;--line:#d5ddd8;--panel:#fff;--green:#087d6b;--green-soft:#e4f4ed;--red:#b5464b;--amber:#a86e00;--amber-soft:#fff2cf}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif;letter-spacing:0}header{height:64px;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;padding:0 max(20px,calc((100vw - 1220px)/2));justify-content:space-between}.brand{font-weight:700;font-size:18px}.status{font-size:13px;color:var(--green);background:var(--green-soft);padding:6px 10px;border-radius:4px}main{max-width:1220px;margin:0 auto;padding:28px 20px 44px;display:grid;grid-template-columns:minmax(0,1.04fr) minmax(320px,.96fr);gap:24px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:24px}h1{font-size:24px;margin:0 0 6px}h2{font-size:17px;margin:0 0 18px}.sub{color:var(--muted);font-size:14px;margin:0 0 24px}.field{margin:0 0 17px}label{display:block;font-size:14px;font-weight:700;margin:0 0 7px}input,textarea,select{width:100%;font:inherit;color:inherit;border:1px solid #bfcac4;border-radius:5px;background:#fff;padding:10px 11px}textarea{min-height:118px;resize:vertical}.choice{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}.choice input{position:absolute;opacity:0}.choice label{margin:0;border:1px solid #bfcac4;border-radius:5px;padding:9px 6px;text-align:center;font-size:13px;font-weight:500;cursor:pointer}.choice input:checked+label{border-color:var(--green);background:var(--green-soft);color:#075a4d;font-weight:700}.urgency{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.urgency input{position:absolute;opacity:0}.urgency label{margin:0;border:1px solid #bfcac4;border-radius:5px;padding:9px 6px;text-align:center;font-size:13px;font-weight:500;cursor:pointer}.urgency input:checked+label{border-color:var(--amber);background:var(--amber-soft);color:#724900;font-weight:700}button{border:0;border-radius:5px;background:var(--green);color:#fff;font:inherit;font-weight:700;padding:11px 16px;cursor:pointer;width:100%}button:hover{background:#056b5b}button:disabled{opacity:.65;cursor:wait}.result-empty{color:var(--muted);font-size:14px;border:1px dashed #bdc9c1;padding:18px;border-radius:5px}.headline{font-weight:700;font-size:18px;line-height:1.55;margin:0 0 12px}.meta{display:flex;gap:7px;flex-wrap:wrap;margin:0 0 18px}.tag{font-size:12px;padding:4px 7px;border-radius:4px;background:#eaf0ef;color:#42535b}.tag.warn{background:#fff0d7;color:#875700}.tag.risk{background:#fbe8e9;color:#973239}.block{border-top:1px solid var(--line);padding:16px 0}.block:last-child{padding-bottom:0}.block h3{font-size:14px;margin:0 0 9px}.block p,.block li{font-size:14px;line-height:1.6}.block ul{margin:0;padding-left:20px}.market{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.metric{background:#f7faf8;border:1px solid #e0e7e2;border-radius:5px;padding:11px}.metric span{display:block;color:var(--muted);font-size:12px;margin-bottom:3px}.metric strong{font-size:15px}.history{grid-column:1/-1;padding:0;background:transparent;border:0}.history-list{list-style:none;padding:0;margin:0}.history-list li{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 0;border-bottom:1px solid var(--line);font-size:13px}.history-list a{color:var(--green);text-decoration:none;font-weight:700}.history-list small{color:var(--muted);display:block;margin-top:3px}.error{background:#fbe8e9;color:#872e34;border-left:4px solid var(--red);padding:12px;font-size:14px;margin:0 0 16px}@media(max-width:820px){main{grid-template-columns:1fr;padding:20px 14px;gap:14px}.panel{padding:18px}.choice{grid-template-columns:repeat(2,1fr)}header{padding:0 14px}.brand{font-size:16px}}
</style></head><body><header><div class="brand">Crypto Intelligence｜即時工作台</div><div class="status">本機資料工作階段</div></header><main>
<section class="panel"><h1>新情報研判</h1><p class="sub">每次研判會保留原始觀察、來源、即時快照與輸出結果。</p><form id="assessment-form"><div id="form-error"></div><div class="field"><label for="title">情境標題</label><input id="title" name="title" maxlength="160" required placeholder="例如：主要交易所出現提領異常傳聞"></div><div class="field"><label for="observation">你的觀察</label><textarea id="observation" name="observation" maxlength="2000" required placeholder="記錄你看到的現象、時間、可能受影響的標的與仍待確認的部分。"></textarea></div><div class="field"><label>你目前的市場方向判斷</label><div class="choice"><input id="bullish" type="radio" name="direction" value="bullish"><label for="bullish">偏利多</label><input id="bearish" type="radio" name="direction" value="bearish"><label for="bearish">偏利空</label><input id="neutral" type="radio" name="direction" value="neutral"><label for="neutral">中性</label><input id="mixed" type="radio" name="direction" value="mixed" checked><label for="mixed">待確認</label></div></div><div class="field"><label>緊急程度</label><div class="urgency"><input id="normal" type="radio" name="urgency" value="normal"><label for="normal">一般</label><input id="high" type="radio" name="urgency" value="high" checked><label for="high">提高關注</label><input id="critical" type="radio" name="urgency" value="critical"><label for="critical">黑天鵝</label></div></div><div class="field"><label for="sources">可驗證來源連結（選填，每行一個）</label><textarea id="sources" name="sources" placeholder="https://example.com/official-announcement" style="min-height:84px"></textarea></div><button id="submit-button" type="submit">開始即時研判</button></form></section>
<section class="panel"><h2>本次結果</h2><div id="result" class="result-empty">尚未進行研判。</div></section><section class="panel history"><h2>最近研判</h2><div id="history" class="result-empty">正在讀取紀錄。</div></section></main>
<script>
const result=document.getElementById('result'),form=document.getElementById('assessment-form'),errorBox=document.getElementById('form-error'),button=document.getElementById('submit-button');
function escapeHtml(value){return String(value??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function metric(label,value){return `<div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;}
function sourceLink(url,name){if(!/^https?:\/\//i.test(url))return escapeHtml(name);return `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(name)}</a>`;}
function render(data){const m=data.market||{},j=data.immediate_judgement||{},events=(data.related_events||[]).slice(0,5);const warnings=(data.warnings||[]).map(x=>`<li>${escapeHtml(x)}</li>`).join('')||'<li>目前無額外系統警示。</li>';result.className='';result.innerHTML=`<p class="headline">${escapeHtml(j.summary)}</p><div class="meta"><span class="tag">推論</span><span class="tag">信心 ${Number(j.confidence||0).toFixed(2)}</span><span class="tag ${data.manual_input.urgency==='critical'?'risk':'warn'}">${escapeHtml(data.manual_input.urgency)}</span></div><div class="block"><h3>市場快照</h3><div class="market">${metric('BTC/USD',m.btc_usd?`${Number(m.btc_usd.price).toLocaleString('en-US',{maximumFractionDigits:2})} USD`:'N/A')}${metric('USDT/USD',m.usdt_usd?`${Number(m.usdt_usd.price).toFixed(4)} USD`:'N/A')}${metric('BTC Dominance',m.btc_dominance==null?'N/A':`${Number(m.btc_dominance).toFixed(2)}%`)}${metric('USDT Depeg',m.usdt_depeg==null?'N/A':Number(m.usdt_depeg).toFixed(4))}</div></div><div class="block"><h3>不確定性</h3><p>${escapeHtml(j.uncertainty)}</p></div><div class="block"><h3>下一輪確認</h3><ul>${(j.follow_up||[]).map(x=>`<li>${escapeHtml(x)}</li>`).join('')}</ul></div><div class="block"><h3>關聯情報</h3><ul>${events.map(e=>`<li>${sourceLink(e.source_url,e.title)} <small>｜${escapeHtml(e.classification)}｜信心 ${Number(e.confidence).toFixed(2)}</small></li>`).join('')}</ul></div><div class="block"><h3>風險與資料限制</h3><ul>${warnings}</ul></div><div class="block"><a href="${escapeHtml(data.artifacts.html_url)}" target="_blank" rel="noopener noreferrer">開啟完整研判報告</a><p class="sub">${escapeHtml(data.disclaimer)}</p></div>`;loadHistory();}
async function loadHistory(){const target=document.getElementById('history');try{const r=await fetch('/api/recent');const d=await r.json();const items=d.items||[];target.className='';target.innerHTML=items.length?`<ul class="history-list">${items.map(i=>`<li><div><strong>${escapeHtml(i.title)}</strong><small>${escapeHtml(i.created_at)}｜${escapeHtml(i.urgency)}｜${escapeHtml(i.market_provider_status)}</small></div><a href="${escapeHtml(i.html_url)}" target="_blank" rel="noopener noreferrer">查看報告</a></li>`).join('')}</ul>`:'尚無研判紀錄。';}catch(_){target.textContent='無法讀取近期紀錄。';}}
form.addEventListener('submit',async event=>{event.preventDefault();errorBox.innerHTML='';button.disabled=true;button.textContent='正在取得資料與研判...';const data={title:form.title.value,observation:form.observation.value,stated_direction:form.direction.value,urgency:form.urgency.value,source_urls:form.sources.value.split('\n').map(x=>x.trim()).filter(Boolean)};try{const response=await fetch('/api/assess',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const output=await response.json();if(!response.ok)throw new Error(output.error||'研判未完成。');render(output);}catch(err){errorBox.innerHTML=`<div class="error">${escapeHtml(err.message)}</div>`;}finally{button.disabled=false;button.textContent='開始即時研判';}});loadHistory();
</script></body></html>'''
