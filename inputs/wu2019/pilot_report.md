# Pilot run report (100 works, 2026-11-23)

The pilot computed raw disruption scores for all **100 randomly sampled Columbia works** [T2, T10]. Independent counts matched on **all 3 validation works** [T11]. Total external spend was **$0.0825** [T13, J3], below the pilot cap. This validates the collection method on the checked cases; it does not establish how team size relates to disruption.

### Eligibility and measurement

The local snapshot contained **55,371 works** [T1]. The eligibility screen excluded **10,720** without a usable recorded reference and another **4,110** without recorded citation evidence, leaving **40,541 proxy-eligible works** [T1, J2]. Citation evidence meant a positive snapshot lifetime citation count, a positive later-calendar-year citation count, or a strictly later local inbound citation edge. The pilot imposed no team-size or work-type restriction. It sampled without replacement from sorted OpenAlex work IDs using NumPy PCG64 with **seed 42** [T2, J4].

For each focal work, the local snapshot supplied its publication date and deduplicated reference list. The external API supplied counts of **unique citing works** published strictly after the focal work and through **November 23, 2026** [J1, T3]. If \(F\) is the set citing the focal work and \(R\) is the set citing at least one of its references, then:

- \(n_i=|F\setminus R|\): cites the focal work only.
- \(n_j=|F\cap R|\): cites both the focal work and at least one reference.
- \(n_k=|R\setminus F|\): cites at least one reference but not the focal work.

The score is \(D=(n_i-n_j)/(n_i+n_j+n_k)\). Collection used exact API counts where possible and deduplicated citing-work IDs where query limits required pagination. It never summed overlapping chunk counts. The pilot computed raw \(D\), not percentiles. The cutoff limits citing works by **publication date**; it does not make the live OpenAlex graph a historical snapshot or give each cohort equal follow-up [J1, T3–T6, T9, T10].

### Validation and coverage

All **100 draws** returned complete counts and passed the count identities and score bounds [T10]. **99** met the study’s positive-inbound-citation restriction within the observed window [T10]. The remaining work had a defined \(D=0\) because later works cited its references but not the focal work; it was flagged and retained without replacement [T10, J2]. The exact full-dataset count under the stricter global, date-filtered citation rule is therefore **not known**.

The independent check paginated citing records and classified them directly from their outgoing edges. It reproduced every count and score for all **3 validation works** [T5, T6, T11]. All **100 focal records** matched the local publication dates, reference lists, and registered lifetime citation totals, but live date-filtered inbound counts were below the snapshot’s later-year counts for **19 works** [T7, J2]. Those counts are not interchangeable, and the validation checks counting within OpenAlex, not the completeness of its citation graph.

### API cost and full-run projections

The pilot logged **840 submissions** [T13]: **829 backend requests**, including **4 uncharged errors**, plus **11 cache hits** and no explicit retries [T13]. Production averaged **6.19 submissions and $0.000610 per work** [T13]. Including preflight, validation, and the metadata audit, the cost was **$0.000825 per work** [T2, T13]. Timed API batches took **173.1 seconds** after preflight, plus **5.5 seconds** of timed preflight; the initial probe was not timed, so this is not end-to-end elapsed time [J1, J3].

The observed charge was **$0.0001 per uncached successful list request**; the harness reported a **$1/day** key budget and did not report a request-rate quota [J1, J2, J3]. The full baseline has a locally determined footprint of **126,219 count calls plus 459 cursor streams** [T12, T14]. The number of pages per stream drives the uncertainty.

| Workload | Projected requests | Projected cost | Active API time |
|---|---:|---:|---:|
| Full baseline, light-to-heavy paging | 130,404–188,769 | $13.04–$18.88 | 4.0–8.6 hours [T14] |
| Full baseline, pilot-like paging | 147,837 | $14.78 | 5.4 hours [T14] |
| Reference age and current citation totals, using local metadata first | 13,957 | $1.40 | 0.41 hours [T14] |
| Fixed-window reruns, per window from one to five years | 39,199–147,837 | $3.92–$14.78 | 1.6–5.4 hours [T14] |
| Excluding focal-author self-citations, **if** the required API filter works | 147,837 | $14.78 | 5.4 hours [T14] |
| Popular-reference \(D\), one threshold, after metadata collection and assuming no paging | 121,623 | $12.16 | 3.6 hours [T14] |
| Citation-edge variant, illustrative counting method | 4,449,461 | $444.95 | 130.2 hours [T14] |

The full baseline would consume roughly **14–19 daily budget allocations** [T14, J3], so elapsed completion time would be much longer than active API time. Add-on rows are separate, not cumulative. Current citation totals are not reference popularity at the time the focal work was published; historical reconstruction was not priced. The simplified disruption ratio, field and impact comparisons, and fixed-effects analyses can reuse baseline outputs and local data [T14].

### Claim plan and recommended next step

The saved claim plan distinguishes what the recent Columbia cohort can test from what needs a different population or longer follow-up:

| Testability | Study claims |
|---|---|
| **Testable within Columbia** | Distributional differences in disruption by team size. |
| **Partly testable** | The main team-size and citation gradients; differences by impact, field, and journal; reference age and popularity; early citation timing; fixed-effects and document-type comparisons; disruption variants; and comparisons by recorded funding acknowledgment. |
| **Not testable here** | The historical team-size trend, patents by large companies, and exceptional disruption among Nobel-winning papers. The Columbia snapshot also cannot reproduce the original cross-population comparison of papers, patents, and software. |

Before committing to the full run, the next step is to resolve the comparability of local and live inbound counts and refine the paging-cost estimate for works with long reference lists. The reproducible script is saved in [J4], the raw per-work results in [T9], the computed scores and coverage flags in [T10], and the validation evidence in [T5, T6, T11]. The run stopped at the pilot: no team-size effects were estimated and no figures were made.