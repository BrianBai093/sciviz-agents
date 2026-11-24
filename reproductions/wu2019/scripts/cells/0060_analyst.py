# cell 60 | agent: analyst | original run: failed | artifacts created: none
script = '''# Figure-only wording update. Run with the harness load() helper from the workspace.
# Uses the released plotting routines and saved estimates; never runs the analysis.
from pathlib import Path
import io, json, re, hashlib, shutil, subprocess, tempfile
from matplotlib.text import Text
from PIL import Image
import numpy as np

parents = {'fig2-team-stage2':'P15', 'fig3-fields-stage2':'P16', 'fig4-empirical-stage2':'P17',
           'fig3-impact-stage2':'P18', 'ext-raw-disruption-stage2':'P19'}
slugs = {'P15':'team-size-and-disruption', 'P16':'disruption-by-field', 'P17':'references-by-team-size',
         'P18':'disruption-by-citation-rank', 'P19':'disruption-score-distributions'}
original_paths = {f['id']: f['immutable_gate_files'] for f in load('J14')['figures']}
words = {
'P15': {'Mean D percentile (0–100)':'Average disruption percentile (0–100)',
        'Median citing works (count)':'Median number of citing works',
        'A  Disruption rank':'A  Disruption rank by team size', 'B  Citation count':'B  Citations by team size',
        'Team size (authors; sample n below each size band)':'Team size (authors), with number of works below'},
'P16': {'Change in mean D percentile per doubling of authors (points)':'Change in disruption rank per doubling of team size (percentile points)',
        '20 supported OpenAlex fields • teams of 1–10 authors':'Disruption by team size in 20 fields (1–10 authors)',
        'Grouping':'Group type', 'Supported /\\nobserved':'Met requirements /\\nobserved',
        'Negative\\nslopes':'Lower rank with\\nlarger teams', '95% bootstrap\\ninterval':'95% confidence\\ninterval'},
'P17': {'A  Reference age':'A  Age of cited references', 'B  Reference popularity':'B  Citations to those references',
        'Current reference citations (count; symlog)':'Current citations per reference (count)',
        'Weighted share of edges above threshold':'References above threshold (%)'},
'P18': {'Mean D percentile (0–100)':'Average disruption percentile (0–100)',
        'Within-year citation impact (unweighted n)':'Citation rank within publication year',
        'Bottom 50% (n=3,768)':'Lowest half (3,768 works)',
        '50th–<90th (n=3,278)':'50th to below 90th (3,278 works)',
        '90th–100th (n=887)':'90th to 100th (887 works)'},
'P19': {'Raw disruption score D (symmetric log scale)':'Disruption score (negative: development; positive: disruption)',
        'Works at or below D (%)':'Works at or below score (%)'},
}

def new_word(parent, text):
    if text in words[parent]: return words[parent][text]
    if parent == 'P16': return re.sub(r' \\(n=([0-9,]+)\\)$', r' (\\1)', text)
    if parent == 'P19': return re.sub(r' \\(n=([0-9,]+)\\)$', r' (\\1 works)', text)
    return text

def pixels(raw):
    return np.asarray(Image.open(io.BytesIO(raw)).convert('RGB'))

def render_pdf(raw):
    with tempfile.TemporaryDirectory() as folder:
        p = Path(folder)/'panel.pdf'; p.write_bytes(raw)
        return subprocess.run(['pdftoppm','-singlefile','-r','150','-png',str(p)],capture_output=True,check=True).stdout

def sha(raw): return hashlib.sha256(raw).hexdigest()

parity = {}
def write_words(fig, original_slug):
    parent=parents[original_slug]; slug=slugs[parent]; evidence={}
    for ext, original_file in zip(('pdf','png'),original_paths[parent]):
        get_bbox=fig.get_tightbbox
        def render(mode):
            positions=[]; edits=[]; outside=[]; undo=[]
            def crop(renderer, *args, **kwargs):
                # This runs after the original layout pass. Use the original crop and do not rerun layout.
                bbox=get_bbox(renderer,*args,**kwargs)
                positions.extend([list(ax.get_position().bounds) for ax in fig.axes])
                positions.append(list(bbox.bounds))
                if mode == 'words':
                    for artist in fig.findobj(Text):
                        old=artist.get_text(); new=new_word(parent,old)
                        if new==old: continue
                        edits.append([old,new]); undo.append((artist,old)); anchor=artist.get_position()
                        artist.set_text(new); assert artist.get_position()==anchor
                        box=artist.get_window_extent(renderer).transformed(fig.dpi_scale_trans.inverted())
                        if box.x0 < bbox.x0-.099 or box.x1 > bbox.x1+.099 or box.y0 < bbox.y0-.099 or box.y1 > bbox.y1+.099:
                            outside.append((new,list(box.bounds)))
                return bbox
            fig.get_tightbbox=crop
            try:
                b=io.BytesIO(); fig.savefig(b,format=ext,dpi=250,bbox_inches='tight',facecolor='white'); raw=b.getvalue()
            finally:
                del fig.get_tightbbox
                for artist,old in undo: artist.set_text(old)
            return raw,positions,edits,outside
        baseline, oldpos, _, _=render('original'); updated, newpos, edits, outside=render('words')
        orig=Path(original_file).read_bytes()
        # Original and amended renders use exactly the same axes and crop to floating-point precision.
        assert np.allclose(oldpos,newpos,rtol=0,atol=1e-10),parent
        if ext=='png': reference, reproduced, final=map(pixels,(orig,baseline,updated))
        elif shutil.which('pdftoppm'): reference, reproduced, final=(pixels(render_pdf(x)) for x in (orig,baseline,updated))
        else: reference=reproduced=final=None
        if reference is not None:
            assert reference.shape == reproduced.shape == final.shape, (parent,ext,reference.shape,reproduced.shape,final.shape)
            baseline_equal=bool(np.array_equal(reference,reproduced))
            assert baseline_equal, (parent,ext,int(np.count_nonzero(np.any(reference!=reproduced,axis=2))))
            changed_pixels=int(np.count_nonzero(np.any(reference!=final,axis=2)))
        else: baseline_equal=changed_pixels=None
        assert not outside, (parent,ext,outside)
        Path(f'figures/{slug}.{ext}').write_bytes(updated)
        evidence[ext]=dict(original_file=original_file,original_sha256=sha(orig),output_sha256=sha(updated),
            original_rerender_pixel_exact=baseline_equal,changed_pixels=changed_pixels,axis_and_crop_bounds=newpos,
            changed_text=edits,changed_labels_outside_page=outside)
    parity[parent]=evidence

def render_relabels():
    ns={'load':load,'STAGE2_RUN':False}
    exec(load('J15')['scripts']['analysis_stage2.py'],ns)
    code=ns['figcode']; start=code.index('def save('); end=code.index('def err(',start)
    ns['figcode']=code[:start]+"def save(fig,slug):\\n write_words(fig,slug)\\n plt.close(fig)\\n"+code[end:]
    ns['render_saved_stage2'].__globals__['write_words']=write_words
    ns['render_saved_stage2']()
    return parity

if __name__ == '__main__':
    print(json.dumps(render_relabels(),ensure_ascii=False,indent=2))
'''
Path('relabel_figures.py').write_text(script); rel={'load':load,'__name__':'relabel_figures'}; exec(script,rel); rel['render_relabels'](); print([(p,{e:(a['original_rerender_pixel_exact'],a['changed_pixels']) for e,a in v.items()}) for p,v in rel['parity'].items()]);
