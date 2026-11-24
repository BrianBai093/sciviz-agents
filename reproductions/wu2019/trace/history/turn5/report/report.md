# How later research cites work by smaller and larger teams

## Summary

Larger teams generally drew more citations in recent Columbia-linked research. A larger share of their works scored below zero. That means more later publications cited each work alongside at least one of its references than cited it without any of them. Wu, Wang and Evans call this pattern development and the opposite balance disruption. This does not show that adding authors makes work less original. [brief] [F11, F12, T83]

The distribution of disruption scores differed by team size, as in the original study. Larger teams generally ranked lower against works from the same year, but not at every size or in every field. They cited newer and generally more cited sources. Among works cited in either of the first two full calendar years after publication, works with 51 to 100 authors received a larger share of those citations in the first year, on average, than solo works did. Larger teams still showed less disruption when we compared works by the same authors, counted citations over a shorter period, or used a simpler score. [brief] [F11, F12, F14, F15, F16, F17, F18]

The decline in disruption rank was clear in the least-cited half. We did not establish the original claim of a steeper decline among the most cited. Reviews and the model of highly cited references gave inconclusive results. We could not test recognition years later, team growth over decades, company patents or Nobel-winning work. [brief] [T1, F13, F15, F16, F17, F19]

## What the original study asked

Wu, Wang and Evans asked whether small teams tend to disrupt and large teams tend to develop earlier work. They examined research articles, US patents and GitHub software projects. Team size meant the number of authors, inventors or contributors listed on a work. [brief]

## What we measured

We sampled 8,000 works published from 2021 through 2024 in OpenAlex, a research index. They included articles, reviews and book chapters. Each had an author listing Columbia University or an institution OpenAlex groups under Columbia. We counted all author entries, even if the person was not identified. The source excluded teams above 100 authors. We drew separately at each size from one to ten and for groups of 11 to 20, 21 to 50 and 51 to 100. A work counted for more if we drew a smaller fraction of its group. This is its sampling weight. [T1, T2, T5, T82, P25]

To enter the sampling list, a work needed a recorded reference other than itself. It also needed any one of three citation records in our copy of OpenAlex: a positive total citation count, a citation in a later calendar year through 2026, or a recorded citing work published after it. [T1, T3, T33, T82, T83, J5]

Across all of OpenAlex, not just the Columbia sample, we counted citing works published after the sampled work. The main window ended on 23 November 2026. The shorter window ended on 31 December of the second calendar year after publication. Works from 2024 were excluded from the shorter analysis because their window had not ended. For each window, the main disruption analysis required a citation to the work itself during that window. [T32, T33, T82, T84]

To score disruption, count distinct later works that cite the paper without any of its references. Subtract the count citing it alongside at least one reference. Divide by the count citing the paper, any of its references, or both. Count each later work only once. With no citations to the paper or its references, the score is undefined. [brief] [T32, T33]

Suppose six later works cite a paper without any of its references, two cite both, and eight cite only the references. Subtract two from six and divide four by sixteen: the score is positive one quarter. A negative score means citing the paper alongside a reference was more common than citing it without its references. If those counts tie, the score is zero. [brief]

The original study mostly reported ranks rather than raw scores. We ranked each score against other sampled works from the same year that qualified for the analysis. On the scale from 0 to 100, add the percentage with lower scores to half the percentage tied, using sampling weights for both. If weights total 100, with 40 below and 20 tied, the rank is 50. A high rank need not mean a positive score. [brief] [T66, T67, T84, P25]

For most intervals we repeatedly drew from the original sample within each team-size group, allowing repeats. This is called a bootstrap. The middle 95% of the recalculated values gives the confidence interval for one estimate. We did not narrow intervals to reflect how much of each group had already been sampled, even for the largest group, where we drew every work. [T5, T66, T68, P25]

## Larger teams ranked lower on disruption and drew more citations

Larger teams generally ranked lower on disruption and drew more citations. The original study found steadily falling ranks and rising typical citation counts, with the disruption pattern extending to teams of up to 100. [brief] [F11, P25]

For works with one to ten authors, we fitted a trend that estimates the same change in disruption rank for each doubling of team size. It showed a decline of 3.48 rank points per doubling, with a 95% interval of 2.70 to 4.27 points of decline among 6,210 works. [T66, F11, P25]

Figure 1 shows average ranks in panel A and median citation counts in panel B. The median is the middle count when works are ordered by citations. For 600 solo works it was 4, with a 95% interval of 3 to 4. For 624 ten-author works it was 15, with an interval of 13 to 17. For 477 works with 51 to 100 authors it was 39, with an interval of 31 to 46. [T66, F11, P25]

{{figure:P25}}

**Partly reproduced.** The measures sometimes levelled off or reversed between neighbouring groups. The largest group shows a result for the range, not each size in it. [brief] [F11, P25]

## The distribution changed, not just the average

Larger teams more often scored below zero. The original study likewise found that the distribution differed by team size. In Figure 2 each curve shows the share at or below each score. Look just left of zero to exclude exact zeros. [brief] [T67, F12, P30]

The share below zero was 77.6% for ten-author works and 48.2% for solo works. The difference was 29.4 percentage points, with a 95% interval of 24.0 to 34.5 points among 1,224 works. Most scores were close to zero. Solo works tended to rank higher, but only 44.3% scored above zero, with an interval of 40.3% to 48.0% among 600 works. [T66, T67, F12, P30]

{{figure:P30}}

**Reproduced in this sample.** We found a difference in distributions without repeating the original tests. [brief] [T67, F12]

## The decline was clearest among less-cited works

The decline in disruption rank was clear in the least-cited half. The original study reported declines at all citation levels, especially among the most cited. [brief] [T68, F13]

Figure 3 groups works by their citation percentiles, which rank counts of distinct citing works within each publication year. The least-cited group is below the 50th percentile. The middle group begins there and the top group begins at the 90th percentile. Ties share a rank. Weights determine the groups, so the lowest group need not contain half the sampled works. The fitted changes use works with one to ten authors. [T68, T84, P44]

The least-cited group fell by 2.50 rank points per doubling, with a 95% interval of 1.64 to 3.39 points of decline among 3,277 works. The middle result was inconclusive. The top estimate was a rise of 0.23 points; its interval ran from a decline of 4.33 to a rise of 3.37 points among 457 works. [T68, F13, P44]

{{figure:P44}}

**Partly reproduced.** For each doubling of team size, the estimated change in rank was 2.73 points higher in the top tenth than in the least-cited half. The 95% interval ranged from 1.89 points lower to 6.00 points higher, based on 3,734 works. We could not tell which group had the steeper decline. [T68, F13]

## The decline was common across fields, but not universal

Most fields and subfields with enough data had downward estimates. The original study found declines across fields and subfields and within most journals. We used the broad and narrow subjects in OpenAlex’s main classification for each work. [brief] [T69, T70, P35]

Figure 4 plots the change per doubling for each field. To qualify, a field, subfield or journal needed at least 30 works with one to ten authors, at least four distinct sizes, and at least five works in each of two ranges: one or two authors, and five to ten. [T69, T70, P35]

The estimated trend was downward in 14 of 20 fields, or 70%, with a 95% interval of 55% to 80%. All 20 fields contained 6,074 works. For subfields, 24 of 34 had downward estimates, or 71%, with an interval of 53% to 76%. All qualifying subfields contained 3,601 works. Many individual intervals allowed no change or a rise. [T69, T70, F14, P35]

{{figure:P35}}

**Partly reproduced for fields and subfields; not testable for most journals.** Only *Proceedings of the National Academy of Sciences* qualified. For its 45 works the estimate was a decline of 2.11 points per doubling, with a 95% interval from a decline of 12.2 to a rise of 7.73. [T69, T70, F14]

## Larger teams drew on newer and more cited references

Larger teams in Figure 5 cited newer and generally more highly cited sources than solo authors did, as in the original study. We measured popularity using cumulative citation totals from our copy of OpenAlex or from the live index, not totals as of the publication date of the work listing each reference. [brief] [T10, T11, T45, T74, T75, F15, P45]

Each plotted reference gets the weight of the work listing it, so longer lists contribute more. We also compared each work’s average reference age using sampling weights. Among works themselves cited in the main window, references in ten-author works were 5.20 years newer than in solo works, with a 95% interval of 4.41 to 6.05 years newer among 1,221 works. Without this extra citation filter, the difference was 5.38 years, with an interval of 4.58 to 6.24 years among 1,249 works. [T74, T75, F15, P45]

{{figure:P45}}

**Partly reproduced.** The curves show observed lists, not models. The age model assumes that raising the age cutoff by one year reduces the share of older references by the same fraction each time. The fitted share fell faster for ten-author than solo works. The citation model assumes that doubling a citation count reduces the predicted share with exactly that count by the same fraction each time. Among references with at least 50 citations, we could not tell whether that fraction differed by team size. Neither model fit closely. [brief] [T76, T77, F15]

## The largest teams drew more of their early attention in the first full year

The largest teams drew early attention, as in the original study. It also found later recognition for small teams and disruptive work. [brief] [T32, T78, F16]

We used works from 2021 through 2023. For each work cited in either of the two full calendar years after publication, we calculated the share arriving in the first. The weighted average share was 5.23 percentage points higher for teams of 51 to 100 than for solo works. The 95% interval was 0.94 to 9.38 points higher, based on 688 works. The ten-author comparison was inconclusive. [T32, T78, F16]

We also calculated each work’s share arriving in the publication year, counting citations through the second full calendar year. We compared works with negative and positive scores as if both groups had the same mix of publication years and quarters. The average publication-year share was 2.14 percentage points larger for negative scores, with a 95% interval of 1.04 to 3.19 points among 5,421 works. The first-full-year measure did not establish a difference by score. Some citations enter both scores and timing measures. [T32, T78, F16]

**Partly reproduced.** The largest teams had a higher average first-year share. Neither measure tests recognition after years of little attention. [F16]

## The link remained when comparing works by the same authors

Larger teams still ranked lower when we compared works by the same authors. The original study found that the link mostly remained after accounting for year, topic and author, and appeared across types of work. [brief] [T79, F17]

We used teams of one to ten. Authors qualified if they had a recorded Columbia affiliation on eligible works with different team sizes. We counted each work under every author who qualified, splitting its sampling weight among them. For each author, we compared disruption ranks for their works on larger and smaller teams, adjusting for publication year and main OpenAlex topic without matching on either. Among 4,107 works, each doubling was associated with a rank 1.85 points lower, with a 95% interval of 0.27 to 3.43 points of decline. Without those adjustments on the same works, the decline was 1.73 points, with an interval of 0.46 to 3.01 points of decline. These intervals account for works sharing an author and works counted under several authors, without resampling. [T79, T80, F17, J12]

**Partly reproduced.** The decline held within authors. In a separate comparison by type, ranks fell among works OpenAlex classified as articles. For reviews the estimate was unclear, and the comparison did not establish that the trends differed. [T79, T81, F17]

## The association held with a shorter window and a simpler score

The original study found the link held across several windows and scoring rules. We ranked the same 4,405 works with one to ten authors and a citation in both windows, separately for each window. The decline per doubling was 3.01 points in the main window, with a 95% interval of 2.01 to 3.93 points of decline. It was 2.82 points in the shorter window, with an interval of 1.78 to 3.85. The direct comparison did not establish a difference. [brief] [T71, T82, T84, F18]

**Partly reproduced.** The simpler score counts the share of later works citing the sampled work that cite none of its references. It fell by 4.29 percentage points per doubling, with a 95% interval of 3.40 to 5.21 points of decline among 6,210 works. Other scores and long windows were not tested. [brief] [T33, T71, F18]

Including works that scored zero because only their references were cited in the relevant window barely changed the main team-size result, though the appendix shows differences for the shorter window and for reviews compared with articles. [F11, F17, F18, T87]

## Funding records offer a narrower comparison

The rank trend differed between works with and without a funding acknowledgment in OpenAlex. The original study also compared company patents and Nobel-winning work and tracked team sizes over decades. [brief] [T72, F19]

Per doubling, rank fell by an estimated 3.75 points without a recorded acknowledgment and rose by an estimated 0.52 points with one; only the decline was clear. The change was 4.26 points higher with an acknowledgment, with a 95% interval of 2.68 to 5.83 points higher among 6,210 works. [T72, F19]

**Partly testable.** We could compare recorded acknowledgments, not verified funding status. Team growth over decades, company patents and Nobel-winning work were not testable here. [brief] [T1, F19]

## Where the findings agree and where they do not

| Finding | Original result | Result in this sample |
|---|---|---|
| Team size | Disruption rank fell and typical citations rose steadily, with the disruption pattern extending to larger teams. [brief] | **Partly reproduced.** Both directions held overall, with exceptions between neighbouring sizes. [F11, P25] |
| Distribution of scores | The distribution changed, not just the average. [brief] | **Reproduced in this sample.** Larger teams more often scored below zero. [F12, T67, P30] |
| Citation levels | Disruption fell with team size at all citation levels, most sharply among highly cited works. [brief] | **Partly reproduced.** The decline was clear in the least-cited half but not established at other citation levels. [F13, P44] |
| Fields and journals | The decline appeared across fields and subfields and in most journals. [brief] | **Partly reproduced.** The decline was common but not universal. Only one journal qualified. [F14, P35] |
| References | Larger teams cited newer and more popular work. How quickly older and highly cited references became rarer differed by team size. [brief] | **Partly reproduced.** References were newer and generally more cited. The fitted age difference agreed in direction; the citation model comparison was inconclusive. [F15, T76, T77, P45] |
| Timing | Large teams drew earlier attention; small teams and disruptive works gained recognition later. [brief] | **Partly reproduced.** The largest teams had a higher average first-full-year citation share than solo authors. Long-delayed recognition could not be tested. [F16, T78] |
| Author, year, topic and type | The link remained after accounting for author, year and topic, and appeared across research types. [brief] | **Partly reproduced.** The decline held within authors. Reviews were inconclusive. [F17, T79, T81] |
| Other windows and scores | The link held across windows and scoring rules. [brief] | **Partly reproduced.** The direction held with a shorter window and a simpler score. [F18, T71] |
| Historical and policy context | Team sizes grew over decades; the study also compared funding, company patents and Nobel-winning work. [brief] | **Partly testable.** We compared recorded acknowledgments, not verified funding. The other comparisons were not testable. [T1, T72, F19] |

## What we could not test

The short follow-up cannot reveal recognition years later or show whether team sizes grew over decades. We did not test long citation windows or score variants that exclude self-citations, use only popular references or count individual citation links instead of citing works. [brief] [T1, T32, T33, T71, T78, F18, F19]

One university’s research cannot stand in for the original collections of articles, patents and software. We lacked data on company patents and Nobel-winning work. Most journals had too few works across the required range of team sizes. We could not reliably distinguish work about theories from work based on observations or experiments, or verify funding. [brief] [T1, T69, T70, T72, T81, F17, F19]

## How far to take the findings

Disruption measures citations, not whether researchers abandoned an idea. Even within authors, different projects may attract different numbers of collaborators. The results do not show what would happen if a team added an author. [brief] [T32, T33, T79]

The results do not describe all Columbia output. Even within a publication year, earlier works had more time to be cited. OpenAlex’s subjects may differ from the original study’s. [brief] [T1, T33, T69, T82, T83, T84]

The cutoff sets which publication dates count; it does not reconstruct the index on that date. Our counts matched separate counts in the cases checked, but that does not mean OpenAlex recorded every citation. The intervals do not account for index errors or for one later work contributing to several scores. [T15, T24, T25, T32, T33, T66, T79]

## Appendix: sampling and checks

**Sampling.** Of 55,371 Columbia-linked works, 10,720 had no usable reference and a recorded count of zero. None had a positive reference count without a usable link. Another 4,110 lacked citation evidence, leaving 40,541. Of those excluded for references, 3,507 had a positive citation total, 3,188 a later-year count, and 482 a dated later citing work; groups overlap. [T1, T83, F20, J5]

We sorted OpenAlex record numbers and drew randomly without replacement within groups, using PCG64 with seed 42. The weight is the number listed divided by the number drawn. Works kept those weights after screening. [T2, T5, T82, J5]

| Authors | Listed | Drawn | Work cited: main | Work cited: short | Weight |
|---|---:|---:|---:|---:|---:|
| 1 | 2,681 | 627 | 600 | 350 | 4.28 |
| 2 | 4,202 | 627 | 618 | 428 | 6.70 |
| 3 | 4,702 | 627 | 623 | 428 | 7.50 |
| 4 | 4,364 | 627 | 623 | 452 | 6.96 |
| 5 | 3,781 | 627 | 624 | 465 | 6.03 |
| 6 | 3,194 | 627 | 625 | 450 | 5.09 |
| 7 | 2,663 | 627 | 625 | 463 | 4.25 |
| 8 | 2,212 | 626 | 623 | 452 | 3.53 |
| 9 | 1,920 | 626 | 625 | 448 | 3.07 |
| 10 | 1,622 | 626 | 624 | 469 | 2.59 |
| 11–20 | 6,370 | 626 | 623 | 474 | 10.18 |
| 21–50 | 2,349 | 626 | 623 | 437 | 3.75 |
| 51–100 | 481 | 481 | 477 | 355 | 1.00 |
| All | 40,541 | 8,000 | 7,933 | 5,671 | — |

Counts are unweighted. [T5, T82, F20]

**Windows.** In the main window, 64 works had only their references cited and three had no citations to either. The shorter window ended for 6,012 works, excluding 1,988 from 2024. In that window, 339 had only references cited and two had neither the work nor its references cited. Of 5,966 cited in the main window with time for both, 5,671 were cited in both. Admitting references-only cases brings the totals to 7,997 for the main window and 6,010 for the shorter window and direct comparison. [T33, T82, T84, F20]

**Count checks.** We searched throughout OpenAlex. A citing work counted in the first matching batch of references. All 62 grouped-count checks, including main and short totals, matched independent counts or classifications from citing works’ reference lists. Reversing batch order left counts unchanged in seven checks. All 122 checked works in one later batch cited a reference from that batch and none from earlier ones. All 79 retrieved lists matched separate OpenAlex totals after deduplication. For lists citing the sampled work itself, we checked which works also listed a reference. [T15, T24, T25, T26, T27, T29, T32, T33]

**Uncertainty.** In 1,000 repeat draws (seed 20261123) we kept group sizes and weights, reapplied eligibility and recalculated ranks. This included the largest group, even though all 481 listed works were sampled. For the author models, 1,885 authors and 4,107 works made 6,838 author–work records. Their intervals hold ranks fixed and allow records sharing an author or work to be related, called two-way clustering. [T5, T66, T68, T79, T80, J12, J15]

**References.** Among works themselves cited in the main window, 373,977 distinct sources appeared 446,323 times. Age excluded 7,547 appearances without a year and 1,742 dated later than the listing work; it kept 10,732 same-year appearances. Citation totals were missing for 7,230 and never zero where known. [T73, T85, F20]

The logarithmic citation scale counts doublings from one after adding one to the total: three citations become four, or two doublings. The age model uses the negative natural logarithm of the fraction remaining each year. The citation model uses a power-law exponent: doubling the count halves the predicted frequency at exponent one and quarters it at exponent two. Larger values mean faster drops. Fit gaps describe mismatch, not formal tests. [T74, T76, T77, J12]

## Appendix: estimates

Each cell gives the estimate, 95% bounds in parentheses, and unweighted work count after the semicolon. The first results column requires a citation to the work itself. The second also accepts citations to its references alone. Results use the main window unless noted. Trends are rank points per doubling for one to ten authors unless stated. Differences subtract the second group from the first. [T66, T68, T71, T87]

### Team size and score distributions

| Estimate | Work itself cited | Also if only references cited |
|---|---|---|
| Rank trend [T66, F11] | −3.48 (−4.27,−2.70); 6,210 | −3.66 (−4.43,−2.91); 6,264 |
| Mean rank: solo [T66, F11] | 62.46 (59.99,64.78); 600 | 62.85 (60.46,65.14); 626 |
| Mean rank: 10 authors [T66, F11] | 47.57 (45.29,49.77); 624 | 47.44 (45.20,49.67); 626 |
| Mean rank: 51–100 authors [T66, F11] | 36.23 (33.97,38.54); 477 | 36.35 (34.09,38.65); 481 |
| Rank difference: 51–100 vs 10 [T66, F11] | −11.34 (−14.47,−8.12); 1,101 | −11.09 (−14.27,−8.00); 1,107 |
| Median citations: solo [T66, F11] | 4 (3,4); 600 | 4 (3,4); 626 |
| Median citations: 10 authors [T66, F11] | 15 (13,17); 624 | 15 (13,17); 626 |
| Median citations: 51–100 authors [T66, F11] | 39 (31,46); 477 | 38 (31,44); 481 |
| Median score: solo [T67, F12] | 0 (−0.0000555,0); 600 | 0 (−0.0000107,0); 626 |
| Median score: 10 authors [T67, F12] | −0.000420 (−0.000523,−0.000289); 624 | −0.000416 (−0.000521,−0.000289); 626 |
| Median score: 51–100 authors [T67, F12] | −0.00116 (−0.00138,−0.000982); 477 | −0.00112 (−0.00134,−0.000880); 481 |
| Below zero: solo (%) [T66, F12] | 48.2 (44.3,52.3); 600 | 46.2 (42.4,50.2); 626 |
| Above zero: solo (%) [T66, F12] | 44.3 (40.3,48.0); 600 | 42.5 (38.6,46.1); 626 |
| Below zero: 10 authors (%) [T66, F12] | 77.6 (74.1,81.0); 624 | 77.3 (73.8,80.8); 626 |
| Above zero: 10 authors (%) [T66, F12] | 17.9 (14.9,21.0); 624 | 17.9 (14.9,20.9); 626 |
| Below zero: 51–100 authors (%) [T66, F12] | 88.1 (85.0,90.8); 477 | 87.3 (84.2,90.0); 481 |
| Above zero: 51–100 authors (%) [T66, F12] | 9.22 (6.77,11.9); 477 | 9.15 (6.65,11.9); 481 |
| Below-zero gap: 10 vs solo (percentage points) [T67, F12] | 29.4 (24.0,34.5); 1,224 | 31.2 (26.0,36.0); 1,252 |
| Largest curve gap: 10 vs solo (share) [T67, F12] | 0.294 (0.247,0.348); 1,224 | 0.312 (0.261,0.364); 1,252 |

The curve gap compares shares at or below each score, whichever curve is higher. [T67, F12]

### Citation levels and subjects

| Estimate | Work itself cited | Also if only references cited |
|---|---|---|
| Trend: least-cited half [T68, F13] | −2.50 (−3.39,−1.64); 3,277 | −2.65 (−3.54,−1.79); 3,299 |
| Trend: middle group [T68, F13] | −1.22 (−2.54,0.48); 2,476 | −1.30 (−2.62,0.46); 2,503 |
| Trend: most-cited tenth [T68, F13] | 0.23 (−4.33,3.37); 457 | 0.18 (−4.55,3.29); 462 |
| Trend difference: top vs bottom [T68, F13] | 2.73 (−1.89,6.00); 3,734 | 2.83 (−1.75,6.00); 3,761 |
| Fields with estimated declines (%) [T70, F14] | 14/20: 70 (55,80); 6,074 | 14/20: 70 (55,80); 6,128 |
| Subfields with estimated declines (%) [T70, F14] | 24/34: 71 (53,76); 3,601 | 25/35: 71 (57,77); 3,693 |
| Journals with estimated declines (%) [T70, F14] | 1/1: 100 (0,100); 45 | 1/1: 100 (0,100); 45 |
| Trend: only qualifying journal [T69, F14] | −2.11 (−12.22,7.73); 45 | −2.04 (−12.09,7.76); 45 |

### References

Differences compare ten authors with solo works. Citation averages use the logarithmic scale. All draws passed the initial screen. [T74, T77, T83, F15]

| Estimate | Work itself cited | Also if only references cited | All draws (no additional citation filter) |
|---|---|---|---|
| Age gap: each listed reference (years) [T74, F15] | −4.95 (−5.95,−3.97); 1,221 | −5.04 (−6.02,−4.09); 1,248 | −5.04 (−6.03,−4.09); 1,249 |
| Age gap: averages per work (years) [T74, F15] | −5.20 (−6.05,−4.41); 1,221 | −5.30 (−6.08,−4.51); 1,248 | −5.38 (−6.24,−4.58); 1,249 |
| Citation gap: each listed reference [T74, F15] | 0.362 (0.234,0.481); 1,221 | 0.366 (0.237,0.486); 1,248 | 0.367 (0.237,0.487); 1,249 |
| Citation gap: averages per work [T74, F15] | 0.391 (0.245,0.530); 1,221 | 0.392 (0.248,0.526); 1,248 | 0.398 (0.254,0.535); 1,249 |
| Difference in fitted age decline [T77, F15] | 0.0313 (0.0259,0.0363); 1,221 | 0.0317 (0.0265,0.0366); 1,248 | 0.0317 (0.0266,0.0366); 1,249 |
| Difference in fitted citation exponent [T77, F15] | 0.00723 (−0.0117,0.0261); 1,204 | 0.00798 (−0.0110,0.0268); 1,230 | 0.00798 (−0.0110,0.0268); 1,230 |
| References with usable age (%) [T73, F15] | 97.87 (97.78,97.96); 7,933 | 97.87 (97.78,97.95); 7,997 | 97.87 (97.78,97.95); 8,000 |
| References with known count (%) [T73, F15] | 98.37 (98.29,98.44); 7,933 | 98.36 (98.29,98.43); 7,997 | 98.36 (98.29,98.43); 8,000 |

### Timing, authors and research types

Timing rows compare average shares in percentage points. Both columns require a citation to the work itself for these rows. [T78, F16]

| Estimate | Work itself cited | Also if only references cited |
|---|---|---|
| First full year: 51–100 vs solo [T78, F16] | 5.23 (0.94,9.38); 688 | 5.23 (0.94,9.38); 688 |
| Publication year: 51–100 vs solo [T78, F16] | 3.31 (0.45,6.10); 705 | 3.31 (0.45,6.10); 705 |
| First full year: 10 vs solo [T78, F16] | 2.82 (−1.76,7.21); 804 | 2.82 (−1.76,7.21); 804 |
| Publication year: 10 vs solo [T78, F16] | −1.24 (−4.01,1.13); 819 | −1.24 (−4.01,1.13); 819 |
| First full year: negative vs positive scores [T78, F16] | 1.85 (−0.20,3.85); 5,369 | 1.85 (−0.20,3.85); 5,369 |
| Publication year: negative vs positive scores [T78, F16] | 2.14 (1.04,3.19); 5,421 | 2.14 (1.04,3.19); 5,421 |
| Before accounting for year, topic and author [T79, F17] | −1.73 (−3.01,−0.46); 4,107 | −1.80 (−3.07,−0.53); 4,135 |
| Same trend, bootstrap bounds [T80] | −1.73 (−2.80,−0.55); 4,107 | −1.80 (−2.82,−0.63); 4,135 |
| Accounting for year, topic and author [T79, F17] | −1.85 (−3.43,−0.27); 4,107 | −1.95 (−3.52,−0.38); 4,135 |
| Trend: articles [T81, F17] | −3.45 (−4.34,−2.50); 4,628 | −3.59 (−4.47,−2.66); 4,657 |
| Trend: reviews [T81, F17] | −0.24 (−3.26,2.88); 390 | −0.25 (−3.27,2.87); 390 |
| Trend difference: reviews vs articles [T81, F17] | 3.21 (−0.08,6.52); 5,018 | 3.34 (0.07,6.64); 5,047 |

### Windows, scores and funding records

The simpler score requires a citation to the work itself in both columns. Even under the broader rule, the direct comparison between windows was inconclusive. [F18, T71]

| Estimate | Work itself cited | Also if only references cited |
|---|---|---|
| Main trend: all years [T71, F18] | −3.48 (−4.27,−2.70); 6,210 | −3.66 (−4.43,−2.91); 6,264 |
| Main trend: years with both windows [T71, F18] | −3.65 (−4.53,−2.75); 4,685 | −3.85 (−4.73,−3.00); 4,721 |
| Main trend: same works eligible in both windows [T71, F18] | −3.01 (−3.93,−2.01); 4,405 | −3.85 (−4.73,−3.00); 4,721 |
| Short trend: same works eligible in both windows [T71, F18] | −2.82 (−3.85,−1.78); 4,405 | −4.03 (−4.94,−3.15); 4,721 |
| Short trend: all qualifying works [T71, F18] | −2.82 (−3.85,−1.78); 4,405 | −4.03 (−4.94,−3.15); 4,721 |
| Short vs main trend: same works [T71, F18] | 0.19 (−0.27,0.65); 4,405 | −0.19 (−0.68,0.29); 4,721 |
| Simpler score trend (percentage points) [T71, F18] | −4.29 (−5.21,−3.40); 6,210 | −4.29 (−5.21,−3.40); 6,210 |
| Trend: no acknowledgment recorded [T72, F19] | −3.75 (−4.92,−2.65); 2,200 | −3.87 (−5.03,−2.77); 2,242 |
| Trend: acknowledgment recorded [T72, F19] | 0.52 (−0.53,1.60); 4,010 | 0.40 (−0.62,1.49); 4,022 |
| Trend difference: acknowledgment vs none [T72, F19] | 4.26 (2.68,5.83); 6,210 | 4.27 (2.72,5.82); 6,264 |

**Original study:** Wu, L., Wang, D. & Evans, J. A. *Nature* 566, 378–382 (2019). DOI: 10.1038/s41586-019-0941-9. [brief]

## Open review issues

The independent review still raised these points after 4 rounds:

- The sentence “We ranked the same 4,405 works with one to ten authors and a citation in both windows, separately for each window” confuses the rank reference set with the slope sample. T71, T82, T84 and J15 show that the ranks were computed among all 5,671 paired eligible works, within publication year, before fitting the slope on 4,405 works. The earlier phrase “against other sampled works” also incorrectly suggests that the focal work was excluded from its own weighted midrank.
- “For reviews the estimate was unclear, and the comparison did not establish that the trends differed” does not specify the eligibility rule. The review slope was inconclusive under both rules, but the review–article contrast narrowly excluded zero when references-only cases were admitted (F17, T81). The appendix gives both results, but the main claim assessment does not distinguish them.
- “A citing work counted in the first matching batch of references” misdescribes the union count. J5 shows that the ordered batches included the focal work ID as well as its reference IDs; a work citing only the focal work still entered the union.
- “We counted all author entries, even if the person was not identified. The source excluded teams above 100 authors.” The cited evidence shows that the analysis used the snapshot’s stored author count and that its observed range was 1–100. It does not establish how unidentified entries were counted or whether the source applied an upstream exclusion.
