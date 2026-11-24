Smaller teams generally produced work that ranked higher on disruption, while larger teams received more citations. Among works with **1–10 authors**, each doubling of team size was associated with a **3.66-point drop in mean disruption percentile** (95% CI: −4.34 to −2.99; \(n=6{,}264\)) [F1, T50]. The decline was not strictly monotonic, and the data did **not** show the stronger decline among highly cited works reported in the original study [F1, F3, T50, T52]. This is a descriptive result for recent Columbia-linked works, not evidence that adding authors makes a work less disruptive.

## Findings

Intervals below are 95%; \(n\) counts sampled works unless otherwise noted.

| Claim | Result |
|---|---|
| **C1 · Team size and citations** | Mean disruption percentiles were **62.85**, **47.44**, and **36.35** for solo, 10-author, and 51–100-author works; median citing-work counts were **4**, **15**, and **38**, respectively (\(n=626,\ 626,\ 481\)). The largest band ranked **11.09 points below** the 10-author group (CI: −12.87 to −9.32; \(n=1{,}107\)) [F1, T50]. |
| **C2 · Raw disruption** | Raw disruption was negative for **46.2%** of solo works (CI: 43.0% to 49.7%) versus **77.3%** of 10-author works (CI: 74.7% to 80.1%; \(n=626\) each). The median raw score for solo works was **zero**: ranking relatively high did not mean that the typical solo work had positive disruption [F2, T51]. |
| **C3 · Citation impact** | The team-size slope in the top citation decile was **2.83 percentile points less negative** per doubling than in the bottom half (CI: −1.42 to 5.66; \(n=3{,}761\)). The contrast was inconclusive and did not support stronger disruption differences at high impact [F3, T52]. |
| **C4 · Fields and journals** | Slopes were negative in **14 of 20 supported fields** (70%; CI: 60% to 85%; \(n=6{,}128\)) and **25 of 35 supported subfields** (71%; CI: 57% to 77%; \(n=3{,}693\)). Only **one journal** met the sample-support rule, so the claim about most journals could not be assessed [F4, T53, T54]. |
| **C5 · References** | Compared with solo works, 10-author works cited references **5.38 years newer** on average (CI: 4.69 to 6.13) and more highly cited today (**+0.40** on the log₂(1 + citations) scale; CI: 0.27 to 0.51; \(n=1{,}249\)). The fitted distributions showed appreciable discrepancies from the observed data; the results do not establish exponential or power-law behavior [F5, T58, T60, T65]. |
| **C6 · Timing of attention** | Among works cited in either of the first **two complete calendar years** after publication, the 51–100-author group received **5.24 percentage points more** of those citations in the earlier year than solo works (CI: 1.96 to 8.47; \(n=688\)). This supports earlier attention for large teams, not long-term delayed recognition for small teams [F6, T61]. |
| **C7 · Author, topic, and document type** | On the same **4,135 works**, the slope was **−1.80 points** per doubling before adjustment (CI: −3.07 to −0.53) and **−1.95** after year, topic, and author fixed effects (CI: −3.52 to −0.38). The review-only slope was inconclusive (\(n=390\)); theory versus empirical work could not be assessed [F7, T62–T64]. |
| **C8 · Robustness** | On the same **4,721 works** with 1–10 authors, slopes were **−3.85** in the main window and **−4.03** in the fixed window (paired difference: −0.19; CI: −0.62 to 0.23). The simplified focal-only citation ratio also declined with team size [F8, T55]. |
| **C9 · Funding acknowledgment** | The slope was **4.27 points less negative** where a funder acknowledgment was recorded than where none was recorded (CI: 2.91 to 5.63; \(n=6{,}264\)). No recorded acknowledgment does not mean no funding [F9, T56]. |

## Coverage, measurement, and cost

- **Sampling:** Of **55,371** snapshot works, **10,720** lacked a usable reference and another **4,110** lacked recorded citation evidence. The resulting proxy frame contained **40,541** works, from which **8,000** were drawn without replacement, with approximately equal allocation across team-size strata. The **51–100-author** stratum was taken in full (\(n=481\)); stratum counts and inclusion probabilities are saved in [T1, T2, T5].
- **Disruption and impact:** Disruption is the number of later works citing the focal work alone minus those citing both it and its references, divided by the number citing either. The main analysis used the current global OpenAlex graph, counting unique citing works published strictly after the focal work through **November 23, 2026**. Citation impact used the same window. Population estimates used inverse inclusion weights, with percentile ranks computed within publication year. Main disruption was defined for **7,997** works, including **64** with cited references but no focal citations; **3** had no citing works in the union. Requiring a positive focal citation count did not change the direction of the result [T32, T33, T49, T50, J11].
- **Fixed window and references:** Fixed follow-up ended on December 31 of the second calendar year after publication. The **1,988** works published in **2024** lacked complete follow-up and were excluded from that comparison, leaving **6,010** defined pairs across all sizes. Of **448,173** focal–reference links, **438,813** were usable for reference age and **440,876** for popularity. Popularity means current citations, not citations at the time the reference was cited [T33, T45, T55, T57, J11].
- **Cost:** Collection cost **$2.9126** of the **$3.50** cap, versus **$3.2299** projected before launch including reserve. Collection through the final audit took **31.6 minutes** wall time; the grouped-count and metadata jobs took **24.8 minutes**. Analysis incurred no additional API spend. Extending the collection to the entire eligible frame would cost about **$14.20 before reserve**, assuming a similar pagination burden; it was not launched [T16, T48, J9, J11].

## Approved figures and handoff

All figures below passed independent review and are saved as both PDF and PNG [J13].

| Figure | File stem |
|---|---|
| Team size, disruption percentile, and citations [P3] | `figures/fig2-team` |
| Raw disruption distributions [P1] | `figures/ext-raw-disruption` |
| Disruption by citation impact [P6] | `figures/fig3-impact` |
| Field and subfield comparisons [P10] | `figures/fig3-fields` |
| Empirical reference-age and popularity distributions [P12] | `figures/fig4-empirical` |

The evidence and code are ready for Stage 2 [J3, J5, J10, J12, F1–F9]. The paper report was **not** written in this stage. The recommended framing is a **partial reproduction**: the overall team-size relationship held in this cohort and survived the shorter window, but the high-impact result did not reproduce and the relationship was not uniform across fields. The historical team-size trend, long-term delayed recognition, patent and software comparisons, Nobel-paper effects, and uncollected disruption variants remain untested.