# cell 40 | agent: analyst | original run: ok | artifacts created: F1, F2, F3, F4, F5, F6, F7, F8, F9
scripts['findings']=r'''
import json

def found(text, items):
 data={key:json.loads(value.to_json(orient='records')) for key,value in items.items()}; print(record_finding(text,data))
found('C1. Sizes 1–10: −3.657 D percentile points per doubling [−4.344, −2.992], n=6,264. Solo/10/51–100 means 62.852/47.443/36.350 (n=626/626/481); median citing works 4 [3,4], 15 [13,16], 38 [38,38]. Not strictly monotone; 51–100 minus 10 is −11.093 [−12.865, −9.323], n=1,107. T50 gives all n and intervals.',{'all_C1':c1})
found('C2. Raw D <0: 46.17% [42.97,49.66] solo and 77.32% [74.65,80.05] at 10, n=626 each. KS distance 0.3115 [0.2683,0.3558], n=1,252. Median raw D 0 [0,0] vs −0.000416 [−0.000499,−0.000313].',{'distribution_headlines':c2[~c2.metric.eq('CDF')],'raw_sign':c1[c1.metric.str.contains('fraction')]})
found('C3. Low/middle/high size slopes −2.647 [−3.459,−1.884], −1.304 [−2.444,0.274], +0.179 [−4.049,2.838], n=3299/2503/462. High-minus-low +2.827 [−1.418,5.663], n=3,761. No stronger high-impact decline demonstrated.',{'all_C3':c3})
found('C4. Negative slopes in 14/20 supported fields (70% [60,85], n=6,128) and 25/35 supported subfields (71.43% [57.14,77.14], n=3,693). Only one of 2,607 observed journals supported (n=45; slope −2.042 [−10.725,6.793]); not a universality result.',{'support':c4s,'supported_groups':c4[c4.supported]})
found('C5. 10 minus solo (equal total weight per work): −5.384 reference years [−6.134,−4.692] and +0.398 log2(1+current citations) [0.273,0.509], n=1,249 works (57,162 and 57,394 edges). Weighted age/popularity coverage 97.87% [97.78,97.94]/98.36% [98.29,98.42] of available design-weighted edge denominators, n=8,000. 10-minus-solo geometric rate +0.03168 [0.02741,0.03572], n=1,249; power-law tail exponent +0.00798 [−0.00829,0.02373], n=1,230; imperfect fits.',{'means':c5,'coverage':c5cov,'fit_diagnostics':c5f,'fit_intervals':c5fi})
found('C6. 51–100 minus solo, mean work share of complete calendar years +1 and +2 citations in +1: +5.235 pp [1.955,8.467], n=688. Negative minus positive raw D: +1.851 pp [−0.011,3.672], n=5,369 for complete years and +2.141 pp [1.127,3.121], n=5,421 for the partially exposed publication-year share standardized by publication cohort and quarter.',{'timing':c6})
found('C7. Within comparable sample, unadjusted −1.801 [−3.069,−0.532], year+topic+author FE −1.950 [−3.521,−0.379], 4,135 works/1,892 Columbia-affiliated focal authors (two-way cluster intervals). Review minus article slope +3.340 [0.406,6.228], n=5,047; review slope −0.248 [−2.945,2.525], n=390.',{'models':c7m,'design_baseline':c7w,'type':c7d})
found('C8. Main vs true fixed on the same 1–10-author works (n=4,721): −3.846 [−4.666,−3.084] vs −4.034 [−4.850,−3.229], paired difference −0.188 [−0.617,0.234]. Simplified ratio −4.285 pp [−5.087,−3.496] per doubling, n=6,210.',{'robustness':c8})
found('C9. Acknowledgment-recorded slope +0.402 [−0.534,1.367], n=4,022 vs −3.867 [−4.869,−2.879], n=2,242 for no record. Difference +4.269 [2.909,5.628], n=6,264. Not a contrast of true funding status.',{'funding_records':c9})
'''
exec(scripts['findings'])
