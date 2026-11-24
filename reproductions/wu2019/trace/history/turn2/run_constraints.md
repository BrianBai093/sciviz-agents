FULL RUN, STAGE 2 OF 2: two corrections, then the report. Stage 1 (evidence and figures) is finished; its
findings, figures and data are in this workspace and stay as they are unless a correction below changes them.

The user reviewed the stage-1 report and figures and decided:

1. Main analysis population. Follow the study: the main analysis uses works with at least one citing work in the
   window (in each window separately). Re-estimate the findings and figures that change. Keep the stage-1 version
   (every work for which the measure is defined) as a robustness check, shown next to the main estimates in a
   table.
2. Uncertainty. The stratum that was sampled in full gets intervals near zero, because a design-based variance
   with a finite-population correction treats those works as the whole population. Intervals in the report should
   describe uncertainty about the pattern, not only about this finite set of works: treat every stratum as a
   sample from a larger population (no finite-population correction), for example a bootstrap that resamples
   works within each stratum, the fully sampled one included. State the method in the methods section and in the
   figure captions.
3. For the claim on the age and popularity of cited work, use figure P12; P9 is superseded.

Every redrawn figure goes through the figure gate again. Findings and figures from stage 1 that do not change
can be reused as they are.

Then write the report (PDF) and pass it through the report gate:
- Reader: a researcher who knows the study. About 8 to 12 pages including figures and tables.
- Sections: summary (question, data, answer); data and methods (the snapshot, the eligibility rules and
  exclusions with counts, the sample design and weights, how the measure was computed from the API, the two
  windows, the interval method); results, one subsection per claim, each with its figure or table; a comparison
  table with one row per claim of the study (status: reproduced / partly / not reproduced / not testable, the
  study's result from the brief, our result, and the reason); deviations from the study's method and why;
  limitations; how to reproduce the run.
- The exported run includes the scripts, the frozen API responses for offline replay, and a run record (time,
  spend, API requests, gate rounds) that the harness adds at export. Describe the replay in the reproduction
  section; do not estimate times or costs.
- Every number cites the artifact it comes from; facts about the original study cite [brief]. Describe the
  study in your own words, without quoting it.
- Report what did not reproduce as plainly as what did.

External API: the stage-1 responses are cached and free to read again; new requests should not be needed.

Stop when the report gate has released the report. Report to the user: the PDF path, the gate outcome, what
changed in the corrections, and anything left open.
