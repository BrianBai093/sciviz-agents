PILOT RUN. The goal is to test the data-collection design and measure its cost, not to answer the question yet.

1. Write the claim plan for the whole study (all claims, with testability on this dataset).
2. Design how to obtain every quantity the study's main measure needs for one work, using the local dataset
   where possible and the external API for the rest.
3. Draw a random sample of 100 works (fixed seed 42) from the works for which the measure is defined and
   computable; state the eligibility rules and how many works in the whole dataset meet them.
4. Collect the data for these 100 works, save the raw per-work results, and compute the measure for each.
5. Validate the counting on at least 3 of the works with an independent method, and check coverage.
6. Report the external requests and cost per work, and project requests, cost and wall-clock time for all
   eligible works and for the other planned analyses (for example, metadata of cited works), under the API
   limits the harness reports.

Stop after step 6. Do not run the full analysis, make figures or write the paper report.
External API spend for this pilot must stay under $0.20.
