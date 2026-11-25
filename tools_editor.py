# -*- coding: utf-8 -*-
"""手心皮肤可视化参数编辑器 v2：所有几何、字号、颜色都能调，实时预览，一键生成 .sxi。

运行：双击 启动编辑器.bat（或 python editor2.py），浏览器打开 http://127.0.0.1:8778
"""
import json
import os
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_SXI = r"D:\DSH\temp\palm.sxi"
WORK_JSON = r"D:\DSH\temp\palm\skin.json"
OUT_DIR = os.path.join(ROOT, "shouxin_out")
OUT_SXI = os.path.join(OUT_DIR, "乱序17_24键.sxi")

LEFT = [
    [("HP", "h"), ("Sh", "s"), ("Zh", "z")],
    [("L", "l"), ("D", "d"), ("Y", "y")],
    [("Ch", "c"), ("Q~", "q"), ("G", "g")],
]
RIGHT = [
    [("B", "b"), ("X", "x"), ("MS", "m")],
    [("WZ", "w"), ("JK", "j"), ("NR", "n")],
    [("CF", "f"), ("T", "t"), (None, None)],
]
STROKES = ["一", "丨", "丿", "丶", "乛"]
LEFT_UP = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]
RIGHT_UP = [["@", "$", "#"], ["0", "%", "&"], ["！", "？"]]

DEFAULTS = {
    "margin": 8,
    "side": 96,
    "mid": 58,
    "gap": 8,
    "extra": 22,
    "gap_l": 0,
    "gap_r": 0,
    "bar_fill_light": "FF4A4A4E",
    "bar_fill_dark": "FF3C3C40",
    "row_top": 10,
    "row_h": 88,
    "rowgap": 10,
    "bottom_h": 78,
    "bw": 62,
    "enter_w": 96,
    "size_main": 40,
    "size_sub": 18,
    "size_small": 26,
    "weight_main": 300,
    "weight_small": 300,
    "light_main": "FF1A1A1A",
    "light_sub": "FF7A7A7A",
    "dark_main": "FFF2F2F2",
    "dark_sub": "FFA8A8A8",
}


def build_skin(p):
    skin = json.load(open(WORK_JSON, encoding="utf-8"))
    P = dict(DEFAULTS)
    P.update({k: v for k, v in p.items() if k in DEFAULTS})
    for key in ("margin", "side", "mid", "gap", "extra", "gap_l", "gap_r", "row_top", "row_h"):
        P[key] = float(P[key])
    for key in ("rowgap", "bottom_h", "bw", "enter_w", "size_main", "size_sub", "size_small", "weight_main", "weight_small"):
        P[key] = float(P[key])

    for theme_name, main_col, sub_col in (
        ("default", P["light_main"], P["light_sub"]),
        ("night", P["dark_main"], P["dark_sub"]),
    ):
        theme = skin[theme_name]
        for layout_key, w, h in (("port_layout", 720, 392), ("land_layout", 1280, 280)):
            board = theme[layout_key].get("b", {}).get("full26Pinyin")
            if not board:
                continue
            scale = 1.0 if w < 1000 else 1.75
            m = P["margin"] * (1 if w < 1000 else 1.5)
            side = P["side"] * scale
            mid = P["mid"] * scale
            gap = P["gap"] * (1 if w < 1000 else 1.5)
            extra = P["extra"] * scale
            gap_l = P["gap_l"] * (1 if w < 1000 else 1.5)
            gap_r = P["gap_r"] * (1 if w < 1000 else 1.5)
            bar_fill = P["bar_fill_light"] if theme_name == "default" else P["bar_fill_dark"]
            row_h = P["row_h"] * (1 if w < 1000 else (h - 30) / 3.0 / 88.0)
            row_top = P["row_top"] * (1 if w < 1000 else 0.8)
            rowgap = P["rowgap"] * (1 if w < 1000 else 1.2)
            bw = P["bw"] * (1 if w < 1000 else 1.5)
            enter_w = P["enter_w"] * (1 if w < 1000 else 1.5)
            bottom_h = P["bottom_h"] * (1 if w < 1000 else 0.55)
            size_main = P["size_main"] * scale
            size_sub = P["size_sub"] * scale
            size_small = P["size_small"] * scale

            rows = []
            y = row_top
            for _ in range(3):
                rows.append((y, row_h))
                y += row_h + rowgap
            bottom_y = rows[-1][0] + rows[-1][1] + rowgap

            base = next((k for k in board["keys"] if isinstance(k.get("b"), dict) and k["b"].get("base_b") is not None), board["keys"][0])
            ss = theme["s_info"]["ss_1"]
            keys = []
            state = {"id": 1}

            def style(text, fs, col, weight):
                sid = max(int(k) for k in ss) + 1
                ss[str(sid)] = {"f": 0, "id": "STYLE%d" % sid,
                                "s_1": {"c_hl": col, "c_normal": col, "f_s": fs, "f_w": weight,
                                        "for_back": False, "text": text}}
                return sid

            def add(cx, cy, cw, ch, text, values, fs=None, sym=None, col=None, weight=None):
                sid = style(text, fs or size_main, col or main_col, weight if weight is not None else P["weight_main"])
                fores = [sid]
                offs = [2]
                if sym:
                    sid2 = style(sym, size_sub, sub_col, P["weight_small"])
                    fores.append(sid2)
                    offs.append(6)
                keys.append({"b": {"base_b": base["b"]["base_b"], "base_f": fores, "base_o": offs},
                             "hit_rect": [[cx, cy], [cw, ch]], "id": str(state["id"]),
                             "rect": [[cx, cy], [cw, ch]], "values": values})
                state["id"] += 1

            def lx(c):
                return m + c * (side + gap)

            def mx():
                return m + 3 * side + 2 * gap + gap_l

            def rx(c):
                return mx() + mid + gap_r + c * (side + gap)

            fill_sid = max(int(k) for k in ss) + 1
            ss[str(fill_sid)] = {"f": 0, "id": "STYLE%d" % fill_sid,
                                 "s_1": {"c_normal": bar_fill, "c_hl": bar_fill, "for_back": True}}

            for r, (yy, hh) in enumerate(rows):
                for c, (label, code) in enumerate(LEFT[r]):
                    up = LEFT_UP[r][c]
                    add(lx(c), yy, side, hh, label, [0, up, 4, code], sym=up)
                for c, (label, code) in enumerate(RIGHT[r]):
                    if code is None:
                        add(rx(c), yy, side, hh, "删除", [4, "backspace"], size_small, col=main_col, weight=P["weight_small"])
                    else:
                        up = RIGHT_UP[r][c]
                        add(rx(c), yy, side, hh, label, [0, up, 4, code], sym=up)

            top = rows[0][0]
            bottom = rows[-1][0] + rows[-1][1]
            step = (bottom - top) / 5.0
            for i, glyph in enumerate(STROKES):
                add(mx(), top + i * step, mid, step, glyph, [4, glyph], size_main + 2)
                keys[-1]["b"]["base_b"] = fill_sid

            bh = bottom_h
            bx = m
            add(bx, bottom_y, bw, bh, "123", [4, "numberBoard"], size_small, col=main_col, weight=P["weight_small"])
            bx += bw + gap
            add(bx, bottom_y, bw, bh, "～", [4, "symbolBoard"], size_main)
            bx += bw + gap
            add(bx, bottom_y, bw, bh, "EN", [4, "switchToEnglish"], size_small, col=main_col, weight=P["weight_small"])
            bx += bw + gap
            en_x = w - m - enter_w - gap - bw
            add(bx, bottom_y, en_x - bx - gap, bh, "空格", [4, "space"], size_small, col=main_col, weight=P["weight_small"])
            add(en_x, bottom_y, bw, bh, "，", [0, "。", 4, "，"], size_main, sym="。")
            add(en_x + bw + gap, bottom_y, enter_w, bh, "回车", [4, "enter"], size_small, col=main_col, weight=P["weight_small"])
            board["keys"] = keys

            for ekey in ("full26EnglishLower", "full26EnglishUpper"):
                eng = theme[layout_key].get("b", {}).get(ekey)
                if not eng:
                    continue
                for k in eng.get("keys", []):
                    v = k.get("values")
                    if v == [0, ".", 4, ","]:
                        k["values"] = [4, "switchToChinese"]
                        sid = style("CN", size_small, main_col, P["weight_small"])
                        k["b"]["base_f"] = [sid]
                        k["b"]["base_o"] = [2]
                    elif v == [4, "."]:
                        k["values"] = [0, ".", 4, ","]
                        s1 = style(",", size_main, main_col, P["weight_main"])
                        s2 = style(".", size_sub, sub_col, P["weight_small"])
                        k["b"]["base_f"] = [s1, s2]
                        k["b"]["base_o"] = [2, 6]
                    elif v == [4, "switchToChinese", 6, "switchToChinese"]:
                        k["__drop"] = True
                enter_x = None
                for k in eng.get("keys", []):
                    if k.get("values") in ([4, "enter", 6, "newLine"], [4, "enter"]):
                        enter_x = k["rect"][0][0]
                eng["keys"] = [k for k in eng.get("keys", []) if not k.pop("__drop", False)]
                if enter_x is not None:
                    for k in eng["keys"]:
                        if k.get("values") == [0, ".", 4, ","]:
                            (x, y), (_, hh2) = k["rect"]
                            k["rect"] = [[x, y], [enter_x - gap - x, hh2]]
                            k["hit_rect"] = k["rect"]

    skin["info"]["name"] = "乱序17 24键"
    skin["info"]["author"] = "dsh"
    skin["info"]["description"] = "24键拼音，参数可视化调整"
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = os.path.join(OUT_DIR, "skin.json")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(skin, fh, ensure_ascii=False, separators=(",", ":"))
    if os.path.exists(OUT_SXI):
        os.remove(OUT_SXI)
    with zipfile.ZipFile(TEMPLATE_SXI) as zin, zipfile.ZipFile(OUT_SXI, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "skin.json":
                zout.write(tmp, "skin.json")
            else:
                zout.writestr(item, zin.read(item.filename))
    return OUT_SXI


PAGE = r"""<!doctype html><html lang="zh"><meta charset="utf-8"><title>手心皮肤参数</title>
<style>
body{background:#161618;color:#eee;font:13px/1.5 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:0;display:flex;height:100vh;overflow:hidden}
#left{width:330px;padding:14px;overflow:auto;border-right:1px solid #2c2c30}
#right{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px}
#board{position:relative;border-radius:12px;box-shadow:0 10px 34px #000a}
.key{position:absolute;display:flex;align-items:center;justify-content:center;border-radius:9px;background:#5a5a5f}
.key .lb{line-height:1}
.key .sym{position:absolute;top:3px;left:0;right:0;text-align:center}
.grp{margin:14px 0 6px;color:#6ea8fe;font-weight:600;border-bottom:1px solid #2c2c30;padding-bottom:4px}
label{display:flex;justify-content:space-between;margin:8px 0 2px;color:#9a9aa0}
input[type=range]{width:100%}
input[type=color]{width:100%;height:26px;border:0;background:none}
button{width:100%;padding:11px;margin-top:14px;border:0;border-radius:9px;background:#0a84ff;color:#fff;font-size:15px}
#msg{margin-top:8px;color:#7fd67f;font-size:12px;min-height:18px;word-break:break-all}
</style>
<div id="left">
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px">
    <b style="font-size:15px">布局参数</b>
    <label style="margin:0;gap:6px"><input type="checkbox" id="dark" checked>深色预览</label>
  </div>
  <div id="controls"></div>
  <button onclick="build()">生成皮肤文件</button>
  <div id="msg"></div>
</div>
<div id="right"><div id="board"></div><div style="color:#777" id="hint"></div></div>
<script>
const P={margin:8,side:96,mid:58,gap:8,extra:22,gap_l:0,gap_r:0,row_top:10,row_h:88,rowgap:10,bottom_h:78,bw:62,enter_w:96,
 size_main:40,size_sub:18,size_small:26,weight_main:300,weight_small:300,
 light_main:"#1a1a1a",light_sub:"#7a7a7a",dark_main:"#f2f2f2",dark_sub:"#a8a8a8",
 bar_fill_light:"#4a4a4e",bar_fill_dark:"#3c3c40"};
const LEFT=[[["HP","h"],["Sh","s"],["Zh","z"]],[["L","l"],["D","d"],["Y","y"]],[["Ch","c"],["Q~","q"],["G","g"]]];
const RIGHT=[[["B","b"],["X","x"],["MS","m"]],[["WZ","w"],["JK","j"],["NR","n"]],[["CF","f"],["T","t"],[null,null]]];
const STROKES=["一","丨","丿","丶","乛"];
const LU=[["1","2","3"],["4","5","6"],["7","8","9"]];
const RU=[["@","$","#"],["0","%","&"],["！","？"]];
const SPEC=[
 ["margin",0,40,1],["side",40,140,1],["mid",30,130,1],["gap",0,24,1],["extra",0,80,1],
 ["row_top",0,40,1],["row_h",50,110,1],["rowgap",0,30,1],["bottom_h",40,110,1],["bw",36,120,1],["enter_w",60,220,1],
 ["gap_l",0,40,1],["gap_r",0,40,1],["size_main",20,64,1],["size_sub",10,34,1],["size_small",14,44,1],
 ["weight_main",100,700,50],["weight_small",100,700,50]];
const GROUPS={"几何":["margin","side","mid","gap","extra","gap_l","gap_r"],"行":["row_top","row_h","rowgap","bottom_h"],"底排":["bw","enter_w"],"字号":["size_main","size_sub","size_small"],"字重":["weight_main","weight_small"]};
const COLORS=[["light_main","浅色主字"],["light_sub","浅色副字"],["dark_main","深色主字"],["dark_sub","深色副字"],["bar_fill_light","浅色笔画条"],["bar_fill_dark","深色笔画条"]];
const box=document.getElementById('board');
const S=0.62;
const dark=()=>document.getElementById('dark').checked;
function draw(){
  const d=dark();
  box.style.width=(720*S)+'px';box.style.height=(392*S)+'px';
  box.style.background=d?'#2b2b2e':'#d9d9dd';
  box.innerHTML='';
  const m=P.margin,g=P.gap,side=P.side,mid=P.mid,extra=P.extra,rg=P.rowgap,rh=P.row_h;
  const rows=[P.row_top,P.row_top+rh+rg,P.row_top+2*(rh+rg)];
  const bottomY=rows[2]+rh+rg;
  const lx=c=>m+c*(side+g);
  const mx=()=>m+3*side+2*g+P.gap_l;
  const rx=c=>mx()+mid+P.gap_r+c*(side+g);
  const main=d?P.dark_main:P.light_main, sub=d?P.dark_sub:P.light_sub;
  function key(x,y,w,h,label,sym,fs,col){
    const e=document.createElement('div');e.className='key';
    e.style.left=(x*S)+'px';e.style.top=(y*S)+'px';e.style.width=(w*S)+'px';e.style.height=(h*S)+'px';
    e.style.background=d?'#5a5a5f':'#fbfbfd';
    const t=document.createElement('span');t.className='lb';t.textContent=label||'';
    t.style.fontSize=((fs||P.size_main)*S)+'px';t.style.color=col||main;t.style.fontWeight=P.weight_main;
    e.appendChild(t);
    if(sym){const s=document.createElement('span');s.className='sym';s.textContent=sym;
      s.style.fontSize=(P.size_sub*S)+'px';s.style.color=sub;s.style.fontWeight=P.weight_small;e.appendChild(s);}
    box.appendChild(e);
  }
  for(let r=0;r<3;r++){
    for(let c=0;c<3;c++) key(lx(c),rows[r],side,rh,LEFT[r][c][0],LU[r][c],P.size_main,main);
    for(let c=0;c<3;c++){const it=RIGHT[r][c];
      if(it[0]) key(rx(c),rows[r],side,rh,it[0],RU[r][c],P.size_main,main);
      else key(rx(c),rows[r],side,rh,"删除",null,P.size_small,main);}
  }
  const top=rows[0],bottom=rows[2]+rh,step=(bottom-top)/5;
  const barcol=d?P.bar_fill_dark:P.bar_fill_light;
  for(let i=0;i<5;i++){
    const e=document.createElement('div');e.className='key';
    e.style.left=(mx()*S)+'px';e.style.top=((top+i*step)*S)+'px';
    e.style.width=(mid*S)+'px';e.style.height=(step*S)+'px';
    e.style.background=barcol;e.style.borderRadius='0';
    const t=document.createElement('span');t.className='lb';t.textContent=STROKES[i];
    t.style.fontSize=((P.size_main+2)*S)+'px';t.style.color=main;t.style.fontWeight=P.weight_main;
    e.appendChild(t);box.appendChild(e);
  }
  const bh=P.bottom_h,bw=P.bw;
  let bx=m;
  key(bx,bottomY,bw,bh,"123",null,P.size_small,main);bx+=bw+g;
  key(bx,bottomY,bw,bh,"～",null,P.size_main,main);bx+=bw+g;
  key(bx,bottomY,bw,bh,"EN",null,P.size_small,main);bx+=bw+g;
  const enx=720-m-P.enter_w-g-bw;
  key(bx,bottomY,enx-bx-g,bh,"空格",null,P.size_small,main);
  key(enx,bottomY,bw,bh,"，","。",P.size_main,main);
  key(enx+bw+g,bottomY,P.enter_w,bh,"回车",null,P.size_small,main);
  document.getElementById('hint').textContent='预览缩放 '+S+'，实际 720×392';
}
const ctr=document.getElementById('controls');
for(const [gname,keys] of Object.entries(GROUPS)){
  const h=document.createElement('div');h.className='grp';h.textContent=gname;ctr.appendChild(h);
  keys.forEach(k=>{
    const def=SPEC.find(s=>s[0]===k);if(!def)return;
    const l=document.createElement('label');l.textContent=k;l.id='lb_'+k;
    const i=document.createElement('input');i.type='range';i.min=def[1];i.max=def[2];i.step=def[3];i.value=P[k];
    const sync=()=>{l.textContent=k+'：'+P[k];};
    i.oninput=()=>{P[k]=+i.value;sync();draw();};sync();
    ctr.appendChild(l);ctr.appendChild(i);
  });
}
const hc=document.createElement('div');hc.className='grp';hc.textContent='颜色';ctr.appendChild(hc);
COLORS.forEach(([k,name])=>{
  const l=document.createElement('label');l.textContent=name;
  const i=document.createElement('input');i.type='color';i.value=P[k];
  i.oninput=()=>{P[k]=i.value;draw();};
  ctr.appendChild(l);ctr.appendChild(i);
});
document.getElementById('dark').onchange=draw;
draw();
function hex(s){ // #rrggbb -> FFrrggbb
  const v=s.replace('#','').toUpperCase();
  return 'FF'+v;
}
async function build(){
  const msg=document.getElementById('msg');msg.textContent='生成中…';
  const out={};
  for(const k in P){out[k]=P[k];}
  out.light_main=hex(P.light_main);out.light_sub=hex(P.light_sub);
  out.dark_main=hex(P.dark_main);out.dark_sub=hex(P.dark_sub);
  try{
    const r=await fetch('/build',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(out)});
    const j=await r.json();
    msg.textContent=j.ok?('已生成：'+j.path):('失败：'+j.error);
  }catch(e){msg.textContent='失败：'+e;}
}
</script></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        body = PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            params = json.loads(self.rfile.read(n).decode("utf-8"))
            path = build_skin(params)
            out = json.dumps({"ok": True, "path": path}, ensure_ascii=False).encode("utf-8")
        except Exception as exc:  # noqa: BLE001
            out = json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    build_skin(DEFAULTS)
    print("编辑器： http://127.0.0.1:8778")
    HTTPServer(("127.0.0.1", 8778), Handler).serve_forever()
