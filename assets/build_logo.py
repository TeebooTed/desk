import subprocess,re,os
from PIL import Image
O=os.path.join(os.path.dirname(os.path.abspath(__file__)),'')
ACC={'light':'#2f6fed','dark':'#6a9bff'};FG={'light':'#14171c','dark':'#e9ecf1'}
def arrows(c,sw=20,h=48,m=16):
    a,b=m,100-m
    return (f'<path fill="{c}" d="M{b} {a}V{a+h}L{b-h} {a}Z M{a} {b}V{b-h}L{a+h} {b}Z"/>'
            f'<line x1="{a+h*0.4}" y1="{b-h*0.4}" x2="{b-h*0.4}" y2="{a+h*0.4}" stroke="{c}" stroke-width="{sw}"/>')
def svg(inner,vb="0 0 100 100"): return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">{inner}</svg>'
def save(n,s): open(O+n,'w').write(s)
def shot(html,out,w,h,bg='00000000'):
    open('/tmp/v3.html','w').write(html)
    subprocess.run(['google-chrome','--headless=new','--no-sandbox','--hide-scrollbars','--allow-file-access-from-files',f'--default-background-color={bg}',f'--window-size={w},{h}',f'--screenshot={out}','/tmp/v3.html'],capture_output=True)
def png(n,w,h): shot(f'<body style="margin:0"><img src="{O}{n}.svg" style="width:{w}px;height:{h}px;display:block">',O+n+'.png',w,h)
for m in ('light','dark'):
    v2=open(O+f'desk-logo-{m}-v2.svg').read()
    vb=[float(x) for x in re.search(r'viewBox="([^"]+)"',v2).group(1).split()]
    W,H=vb[2],vb[3]
    body=v2.split('>',1)[1].rsplit('</svg>',1)[0]; word=re.split(r'<g transform="translate\([\d.]+ [\d.]+\) scale\(1.5\)">',body)[0]
    iy=re.search(r'translate\([\d.]+ ([\d.]+)\) scale\(1.5\)',v2).group(1)
    s=svg(word+f'<g transform="translate({(W-160)/2:.1f} {float(iy)-6:.1f}) scale(1.6)">{arrows(ACC[m])}</g>',f"0 0 {W:.0f} {H:.0f}")
    save(f'desk-logo-{m}.svg',s); png(f'desk-logo-{m}',int(W*1.5),int(H*1.5))
    save(f'desk-icon-{m}.svg',svg(arrows(ACC[m])));png(f'desk-icon-{m}',512,512)
TILE=lambda r: f'<rect width="100" height="100" rx="{r}" fill="#2f6fed"/>'+arrows('#fff')
save('desk-icon-tile.svg',svg(TILE(22)));png('desk-icon-tile',512,512)
save('favicon.svg',svg(f'<rect width="100" height="100" rx="22" fill="#2f6fed"/>'+arrows('#fff')));png('favicon',512,512)
Image.open(O+'favicon.png').convert('RGBA').save(O+'favicon.ico',sizes=[(16,16),(32,32),(48,48)]);os.remove(O+'favicon.png')
save('_a.svg',svg(f'<rect width="100" height="100" fill="#2f6fed"/>'+arrows('#fff')));png('_a',180,180)
Image.open(O+'_a.png').convert('RGB').save(O+'apple-touch-icon.png');os.remove(O+'_a.png');os.remove(O+'_a.svg')
ico=Image.open(O+'favicon.ico')
for s in (16,32,48):
    ico.size=(s,s);ico.load();ico.convert('RGBA').save(f'/tmp/g{s}.png')
tab=lambda fg,tb:''.join(f'<div style="display:flex;align-items:center;gap:8px;background:{tb};color:{fg};padding:8px 14px;border-radius:10px 10px 0 0;width:200px;margin-right:8px"><img src="/tmp/g{s}.png" style="width:{s}px;height:{s}px;image-rendering:pixelated">Desk · {s}px</div>' for s in (16,32))
cell=lambda f,bg,lab,lc:f'<div style="flex:1;background:{bg};padding:30px;text-align:center"><img src="{O}{f}" style="height:280px"><p style="color:{lc}">{lab}</p></div>'
shot(f'''<body style="margin:0;width:1600px;background:#f3f4f7;font:14px system-ui"><div style="display:flex">
{cell("../logo/apple-touch-icon-v3.png","#fff","REFERENCE: apple-touch v3","#677180")}{cell("desk-logo-light.svg","#fff","v4 lockup light","#677180")}{cell("desk-logo-dark.svg","#0c0e12","v4 lockup dark","#8c95a3")}</div>
<div style="display:flex;gap:36px;padding:30px 40px;align-items:flex-end">
<div><img src="{O}apple-touch-icon-v3.png" style="width:130px;border-radius:28px"><p>ref v3</p></div><div><img src="{O}desk-icon-light.svg" style="width:130px;background:#fff;border-radius:14px"><p>icon light v4</p></div>
<div><img src="{O}desk-icon-dark.svg" style="width:130px;background:#0c0e12;border-radius:14px"><p>icon dark v4</p></div>
<div><img src="{O}desk-icon-tile.svg" style="width:130px"><p>tile</p></div>
<div><img src="{O}apple-touch-icon.png" style="width:180px;border-radius:40px"><p>apple-touch v4 180</p></div>
<div><img src="/tmp/g48.png"> <img src="/tmp/g32.png"> <img src="/tmp/g16.png"><p>ICO 48/32/16 (1:1)</p></div>
<div><img src="{O}desk-logo-light.svg" style="height:60px;background:#fff"> <img src="{O}desk-logo-dark.svg" style="height:36px;background:#0c0e12"><p>small lockups</p></div></div>
<div style="padding:0 40px 30px"><div style="background:#dee1e6;padding:8px 8px 0;display:flex">{tab('#14171c','#fff')}</div>
<div style="background:#202124;padding:8px 8px 0;display:flex;margin-top:12px">{tab('#e9ecf1','#35363a')}</div></div></body>''',O+'desk-logo-preview.png',1600,900,'f3f4f7ff')
