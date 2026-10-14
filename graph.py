"""Safe self-contained interactive vis-network graph inside a Streamlit iframe."""
import html
import json
import math
from collections import Counter, defaultdict


def _json(value):
    # Prevent Reddit-provided text from breaking out of the script element.
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def build_graph(posts, topics, dark=True):
    group = defaultdict(list)
    for p in posts:
        group[p["subreddit"]].append(p)
    sub_names = sorted(group, key=lambda x: sum(p["heat"] for p in group[x]), reverse=True)[:22]
    nodes, edges, details = [], [], {}
    for ix, sub in enumerate(sub_names):
        entries = sorted(group[sub], key=lambda x: x["heat"], reverse=True)
        sid = "s:" + sub.lower()
        nodes.append({"id": sid, "label": "r/" + sub, "group": "sub", "value": min(28, 9+5*math.log1p(len(entries))), "title": f"{len(entries)} sampled posts in r/{html.escape(sub)}"})
        details[sid] = {"name": "r/" + sub, "type": "Subreddit", "description": f"{len(entries)} relevant posts in this sample", "links": [
            {"title": p["title"], "url": p["url"], "subreddit": p["subreddit"], "heat": p["heat"]} for p in entries[:10]]}
    for ix, t in enumerate(topics[:18]):
        tid = "t:" + t["term"]
        nodes.append({"id": tid, "label": t["term"].title(), "group": "topic", "value": min(35, 13 + 5*math.log1p(t["posts"])), "title": f"{t['posts']} mentions in {t['communities']} communities"})
        details[tid] = {"name": t["term"].title(), "type": "Discussion topic", "description": f"{t['posts']} posts · {t['communities']} communities", "links": t["links"]}
        for name, n in t["subreddits"].items():
            if name in sub_names:
                edges.append({"from": tid, "to": "s:" + name.lower(), "value": n, "title": f"{n} posts", "width": min(5, 1+math.sqrt(n))})
    colors = {"bg": "#111821", "panel": "#192433", "text": "#eef3fb", "muted": "#9aacc5", "edge": "#496077", "line": "#2b3c51"} if dark else {"bg": "#ffffff", "panel": "#f7f9fd", "text": "#152338", "muted": "#63748a", "edge": "#c4ccda", "line": "#e3e7f0"}
    return r"""<!doctype html><html><head><meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
    <style>*{box-sizing:border-box}body{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif;background:VAR_BG;color:VAR_TEXT}
    .wrap{display:grid;grid-template-columns:minmax(0,1fr) 305px;height:600px;border:1px solid VAR_LINE;border-radius:12px;overflow:hidden}
    #mynetwork{height:100%;min-width:0;background:VAR_BG}.detail{background:VAR_PANEL;border-left:1px solid VAR_LINE;overflow-y:auto;padding:20px}
    h3{font-size:17px;line-height:1.3;margin:0 0 7px}p{font-size:13px;color:VAR_MUTED;line-height:1.55}
    .label{font-size:11px;font-weight:750;color:#55b5fa;letter-spacing:1px;text-transform:uppercase;margin-bottom:10px}
    .entry{padding:12px 0;border-bottom:1px solid VAR_LINE}.entry a{color:VAR_TEXT;font-size:13px;line-height:1.45;display:block;text-decoration:none;font-weight:550}
    .entry a:hover{color:#74b7ff}.meta{font-size:11px;color:VAR_MUTED;padding-top:6px}
    .legend{position:absolute;top:12px;left:14px;padding:7px 10px;background:VAR_PANEL;border:1px solid VAR_LINE;border-radius:8px;font-size:11px;pointer-events:none;z-index:1}
    .dot{display:inline-block;height:9px;width:9px;border-radius:50%;margin-right:4px}.canvas{position:relative;min-width:0}
    @media(max-width:680px){.wrap{height:720px;grid-template-columns:1fr;grid-template-rows:390px 330px}.detail{border-left:none;border-top:1px solid VAR_LINE}}
    </style></head><body><div class="wrap"><div class="canvas"><div class="legend"><span class="dot" style="background:#4c91f3"></span> Subreddit&nbsp;&nbsp;&nbsp; <span class="dot" style="background:#ec6b9c"></span> Topic</div><div id="mynetwork"></div></div>
    <aside class="detail" id="detail"><div class="label">Interactive network</div><h3>Explore the discussion</h3><p>Click a topic or subreddit to view its relevant posts. Scroll to zoom and drag to move around the network.</p></aside></div>
    <script>
    const nodes = new vis.DataSet(NODES);
    const edges = new vis.DataSet(EDGES);
    const details = DETAILS;
    const network = new vis.Network(document.getElementById('mynetwork'), {nodes,edges}, {
     autoResize:true,
     nodes:{shape:'dot',font:{face:'Inter,system-ui,sans-serif',size:13,color:'VAR_TEXT',strokeWidth:3,strokeColor:'VAR_BG'},borderWidth:1.5,scaling:{min:12,max:30}},
     groups:{sub:{color:{background:'#367dd8',border:'#74b7ff',highlight:{background:'#4d9cf0',border:'#b7dfff'}}},topic:{color:{background:'#e2558d',border:'#ffa5c4',highlight:{background:'#f87cae',border:'#ffe1ec'}}}},
     edges:{color:{color:'VAR_EDGE',highlight:'#85bfff'},smooth:{type:'dynamic'},selectionWidth:2},
     physics:{solver:'forceAtlas2Based',forceAtlas2Based:{gravitationalConstant:-44,centralGravity:0.012,springLength:145,springConstant:0.065,damping:0.75},stabilization:{iterations:180,fit:true}},
     interaction:{hover:true,tooltipDelay:130,navigationButtons:true,keyboard:true,zoomView:true},
     layout:{improvedLayout:true}
    });
    const panel=document.getElementById('detail');
    function render(id){const d=details[id];if(!d)return;panel.replaceChildren();
      const label=document.createElement('div');label.className='label';label.textContent=d.type;panel.appendChild(label);
      const h=document.createElement('h3');h.textContent=d.name;panel.appendChild(h);
      const p=document.createElement('p');p.textContent=d.description;panel.appendChild(p);
      d.links.forEach(item=>{const row=document.createElement('div');row.className='entry';
        const a=document.createElement('a');a.textContent=item.title;
        if(item.url && /^https:\/\/www\.reddit\.com\/r\//.test(item.url)){a.href=item.url;a.target='_blank';a.rel='noopener noreferrer nofollow';}
        row.appendChild(a);
        const m=document.createElement('div');m.className='meta';m.textContent='r/'+item.subreddit+' · Attention '+Math.round(item.heat);row.appendChild(m);panel.appendChild(row);
      });
    }
    network.on('click',params=>{if(params.nodes.length) render(params.nodes[0]);});
    if(nodes.length) render(nodes.getIds()[0]);
    </script></body></html>""".replace("NODES", _json(nodes)).replace("EDGES", _json(edges)).replace("DETAILS", _json(details)) \
        .replace("VAR_BG", colors["bg"]).replace("VAR_PANEL", colors["panel"]).replace("VAR_TEXT", colors["text"]) \
        .replace("VAR_MUTED", colors["muted"]).replace("VAR_EDGE", colors["edge"]).replace("VAR_LINE", colors["line"])
