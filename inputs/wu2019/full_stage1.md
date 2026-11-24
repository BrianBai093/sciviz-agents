FULL RUN, STAGE 1 OF 2: evidence and figures. The report is written in stage 2 (a later message in this session).

Decisions already made by the user:
1. Population and sample. Use the works for which the study's measure is defined and computable (the pilot's
   eligibility rules are in pilot_report.md). Draw a sample of about 8,000 works stratified by team size, with
   strata 1, 2, ..., 10, 11-20, 21-50 and 51-100 authors, allocated as equally as possible across strata
   (take every work in a stratum that is smaller than its share), seed 42. Keep the inclusion probabilities and
   use sampling weights wherever a population-level quantity is estimated (for example percentiles over all
   works, or overall means); state when an estimate is unweighted.
2. Measure windows. Main analysis: citing works published after the focal work up to the snapshot day
   (2026-11-23). Robustness check: a fixed window of citing works published no later than the end of the second
   calendar year after the focal work's publication year. Percentiles are taken within publication year.
3. Data for the analyses of past work cited (claim about reference age and popularity): publication year and
   current citation count of the works the sampled works cite.
4. External API budget for this run: $3.50 in total. Plan the collection so that all of the above fits, and
   check the projected cost on a small batch before the bulk collection. The pilot's design, API facts and
   costs are in pilot_report.md and pilot_decisions.md; reuse them and skip preflight work that the pilot
   already did.
5. Produce evidence (findings with estimates, uncertainty and sample sizes) for every claim marked "yes" or
   "partly" in the claim plan, and figures that a reader can compare with the study's main figures. Every
   figure must pass the figure gate.

Stop when the evidence and figures are complete, with a report to the user that lists the findings, the figures
and anything that could not be done. Do not write the paper report in this stage.
