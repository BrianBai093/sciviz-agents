# Paper brief: Wu, Wang & Evans (2019)

L. Wu, D. Wang, J. A. Evans, "Large teams develop and small teams disrupt science and technology",
*Nature* 566, 378–382 (2019). https://doi.org/10.1038/s41586-019-0941-9

This brief is our own summary of the study, written from its public abstract, figure titles and extended-data
captions, for a team that will try to reproduce the findings on a different dataset. It does not copy the article.

## Question
Science and technology are produced by ever larger teams. Does the kind of work that large and small teams
produce differ? In particular, do small teams tend to *disrupt* (introduce ideas that make earlier work less
needed) while large teams tend to *develop* (build on and extend recent, popular work)?

## Original data
- About 24 million research articles (Web of Science, 1954–2014), about 2.5 million US patents and about
  27 thousand GitHub software projects; 65+ million works in total.
- Team size = the number of authors (inventors, contributors) of a work.
- Most analyses use works with at least one citation and team sizes 1–10; some extend to 100.

## Measure: disruption D
For a focal work f with reference list R, look at later works that cite f or cite anything in R:
- n_i = later works that cite f but none of the works in R;
- n_j = later works that cite f and also at least one work in R;
- n_k = later works that cite at least one work in R but not f.

D = (n_i − n_j) / (n_i + n_j + n_k), which lies in [−1, 1].
- D > 0: later work cites f *instead of* its sources (f disrupts).
- D < 0: later work cites f *together with* its sources (f develops / consolidates).
- D = 0 is the boundary between the two.

The study mostly reports D as a **percentile** (the rank of a work's D among all works, 0–100), and also the raw
D. It measures citations over the observation window available in the data, and shows the results are robust
to windows from 5 to 40 years. It also checks alternative versions of D:
- excluding self-citations;
- counting only popular references;
- a simplified ratio n_i / (n_i + n_j);
- counting citations instead of citing works.

## Claims (and where the study shows them)
1. **Main result (Fig. 2).** As team size grows from 1 to 10, the average D percentile falls steadily while
   citations (median) rise. This holds for papers, patents and software: small teams disrupt, large teams
   develop. Bootstrapped 95% confidence intervals are shown. Extended to team sizes up to 100, the same
   direction holds.
2. **Distributions (Extended Data).** The whole distribution of D shifts with team size, not only the mean;
   differences between team sizes are statistically significant (t-tests and Kolmogorov–Smirnov tests).
3. **Across impact levels (Fig. 3).** The decline of D with team size appears at every level of citation impact
   and is stronger for highly cited work. Highly cited small-team work tends to be very disruptive, and highly
   cited large-team work tends to be very developmental.
4. **Across fields (Fig. 3, Extended Data).** The decline holds across fields and subfields and within most
   journals.
5. **Search through past work (Fig. 4).** Larger teams cite more recent references and more popular (highly
   cited) references. Smaller teams reach further into the past and cite less popular work. The study models the
   reference age distribution as exponential (its decay rate grows with team size) and reference popularity as
   a power law (its exponent changes with team size).
6. **Timing of attention (Extended Data).** Work by large teams is cited soon after publication; work by small
   teams (and disruptive work) is recognised later, if at all ("sleeping beauty" patterns are more common).
7. **Not explained by topic or design (text, Extended Data).** Controlling for publication year, topic and the
   individual author (fixed effects; regression of D on team size), most of the team-size effect remains: it
   happens within the same people as they work in smaller or larger teams. Theory vs empirical papers and
   review vs non-review papers show the same pattern.
8. **Robustness.** The result is robust to the citation window and to the alternative versions of D.
9. **Trends and policy (Extended Data).** Average team size grew over 1954–2014; funded work and patents by
   large companies are also compared; Nobel-winning papers are unusually disruptive. (Context, not the core
   finding.)

## Notes for a reproduction
- Report sample sizes for every team size, and confidence intervals.
- Say clearly which claims can and cannot be tested on the available data, and why.
