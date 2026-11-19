"""Small offline Korean lettering check; not a production typography engine."""
import hashlib
import json
import struct
import tempfile
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from ..core import ROOT,safe,write_json
FONT=Path('/System/Library/Fonts/AppleSDGothicNeo.ttc')

def load_font(text):
    if not FONT.is_file(): raise ValueError('FONT_UNAVAILABLE')
    raw=FONT.read_bytes()
    def u16(o):return struct.unpack_from('>H',raw,o)[0]
    def u32(o):return struct.unpack_from('>I',raw,o)[0]
    try:
        offset=u32(12) if raw[:4]==b'ttcf' else 0
        tables={raw[o:o+4]:u32(o+8) for o in range(offset+12,offset+12+16*u16(offset+4),16)}
        cmap=tables[b'cmap']; subtables=[]
        for o in range(cmap+4,cmap+4+8*u16(cmap+2),8):
            platform,encoding=u16(o),u16(o+2)
            if platform==0 or (platform==3 and encoding in (1,10)):
                subtables.append(cmap+u32(o+4))
        def glyph(cp):
            for t in subtables:
                fmt=u16(t)
                if fmt==12:
                    for o in range(t+16,t+16+12*u32(t+12),12):
                        start,end,gid=u32(o),u32(o+4),u32(o+8)
                        if start<=cp<=end:return gid+cp-start
                elif fmt==4 and cp<=65535:
                    n=u16(t+6)//2; ends=t+14; starts=ends+2*n+2; deltas=starts+2*n; ranges=deltas+2*n
                    for i in range(n):
                        if u16(starts+2*i)<=cp<=u16(ends+2*i):
                            delta=u16(deltas+2*i); ro=u16(ranges+2*i)
                            if not ro:return (cp+delta)&65535
                            g=u16(ranges+2*i+ro+2*(cp-u16(starts+2*i)))
                            return ((g+delta)&65535) if g else 0
            return 0
        missing=sorted(set(c for c in text if not c.isspace() and not glyph(ord(c))))
        if missing:raise ValueError('MISSING_GLYPH:'+repr(missing))
        font=ImageFont.truetype(str(FONT),24,index=0)
    except (KeyError,struct.error,OSError) as exc:raise ValueError('FONT_SUPPORT_UNVERIFIED') from exc
    return font,hashlib.sha256(raw).hexdigest()

CLOSING='，。、,.!?？！:;)]}」』”’'
OPENING='([{「『“‘'
def wrap(text,font,width):
    if not text.strip():raise ValueError('EMPTY_TEXT')
    import re
    lines=[];errors=[]
    for para in text.split('\n'):
        if not para:
            lines.append('');continue
        line=''
        # Preserve all source characters; whitespace stays on the preceding line.
        for token in re.findall(r'\S+\s*|\s+',para):
            if font.getlength(token.rstrip())>width:
                errors.append('WORD_TOO_WIDE: widen balloon or explicitly edit text: '+token.rstrip())
            if line and font.getlength(line+token.rstrip())>width:
                lines.append(line);line=token
            else:line+=token
        lines.append(line)
    for line in lines:
        visible=line.strip()
        if visible and (visible[0] in CLOSING or visible[-1] in OPENING):errors.append('PUNCTUATION_BREAK')
    return lines,errors

def layout(items,size=(600,900)):
    font,digest=load_font(''.join(i['text'] for i in items)+'시험용 미리보기 최종본 아님')
    errors=[];records=[]
    for i,item in enumerate(items):
        x,y,w,h=item['box'];lines,issues=wrap(item['text'],font,w-32)
        errors += [str(i)+':'+e for e in issues]
        if x<0 or y<0 or x+w>size[0] or y+h>size[1]:errors.append(str(i)+':BALLOON_CLIPPED')
        if len(lines)*36+32>h:errors.append(str(i)+':TEXT_CLIPPED')
        for j,other in enumerate(items[:i]):
            a,b,c,d=other['box']
            if x<a+c and a<x+w and y<b+d and b<y+h:errors.append(str(j)+':'+str(i)+':BALLOON_OVERLAP')
        boxes=[font.getbbox(line) for line in lines]
        if any(b[2]-min(0,b[0])>w-32 or b[3]-b[1]>36 for b in boxes):errors.append(str(i)+':GLYPH_CLIPPED')
        records.append({'box':item['box'],'text':item['text'],'lines':lines,'glyph_bounds':boxes})
    return {'test_only':True,'final_allowed':False,'font_sha256':digest,'font_name':font.getname(),
            'size':size,'records':records,'errors':errors},font

def verify_archive(path):
    with zipfile.ZipFile(path) as z:
        if z.testzip():raise ValueError('ZIP_CRC_FAILED')
        manifest=json.loads(z.read('manifest.json'))
        if set(z.namelist()) != set(manifest['files'])|{'manifest.json'}:raise ValueError('ZIP_ENTRY_MISMATCH')
        if manifest.get('test_only') is not True or manifest.get('final_allowed') is not False:raise ValueError('NOT_TEST_ARCHIVE')
        for name,digest in manifest['files'].items():
            if hashlib.sha256(z.read(name)).hexdigest()!=digest:raise ValueError('ZIP_HASH_MISMATCH')
    return manifest

def demo():
    items=[{'text':'이것은 한글 말풍선 배치 시험입니다. 그림과 대사는 실제 작품이 아닙니다.','box':[50,120,500,220]},
           {'text':'잠시 멈추고, 다음 장면을 읽어 봅니다.\n이 파일은 최종본이 아닙니다.','box':[90,480,440,220]}]
    report,font=layout(items)
    if report['errors']:raise ValueError(str(report['errors']))
    base=safe(ROOT,'output/korean-layout-runs');base.mkdir(parents=True,exist_ok=True)
    run=Path(tempfile.mkdtemp(prefix='ko-',dir=base))
    im=Image.new('RGB',report['size'],'#efe9df');draw=ImageDraw.Draw(im)
    draw.text((30,30),'시험용 미리보기 · 최종본 아님',font=font,fill='#b00000')
    for record in report['records']:
        x,y,w,h=record['box'];draw.rounded_rectangle((x,y,x+w,y+h),radius=25,fill='white',outline='black',width=2)
        for i,line in enumerate(record['lines']):draw.text((x+16,y+16+i*36),line,font=font,fill='black',anchor='lt')
    with safe(run,'test-preview.png').open('xb') as f:im.save(f,format='PNG')
    write_json(run,'layout-report.json',report)
    manifest={'test_only':True,'final_allowed':False,'g4':'not_authenticated','files':{}}
    for name in ('test-preview.png','layout-report.json'):
        manifest['files'][name]=hashlib.sha256(safe(run,name).read_bytes()).hexdigest()
    write_json(run,'manifest.json',manifest)
    with zipfile.ZipFile(safe(run,'private-test-only.zip'),'x',zipfile.ZIP_DEFLATED) as z:
        for name in list(manifest['files'])+['manifest.json']:z.write(safe(run,name),name)
    verify_archive(safe(run,'private-test-only.zip'))
    return {'run':str(run),'errors':report['errors'],'test_only':True,'final_allowed':False,'zip_roundtrip':True}
