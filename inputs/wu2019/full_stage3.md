FULL RUN, STAGE 3: the report, rewritten for people. The analysis is final: do not run new analyses, do not
change any number, and make no external API requests.

The user read the released report and decided it must be rewritten. It reads like a technical appendix: it uses
the team's working labels (for example "strict domain", "comparator", "proxy frame", "Stage 1" and "Stage 2",
"F>0", "U>0", "focal-only share", "standalone" and "paired" estimates, "supported" fields), symbols in running
text, and long sentences packed with qualifications. Its how-to-reproduce section pointed to internal artifacts and
code. The figure titles and captions have the same problems ("Fig. 2 analogue", "(Stage 2)", "inverse-inclusion
weights", "no finite-population correction").

The user's instruction: write it for people, in plain English from start to finish, with no terms the team made
up. Check it against what the task asks for: a PDF report that describes the reproduced findings of the study,
the analysis and the figures (the main findings, including the written analysis and figures), with the scripts,
intermediate data and reproduction instructions provided alongside it.

1. Figures. Have the analyst redraw the five figures the report uses (P15, P16, P17, P18, P19) from their saved
   data, changing only the words: a plain title that says what the figure shows; plain axis labels and legends;
   a plain caption that says what is plotted, for which papers, what the error bars or bands mean and what to look
   at, and which figure of the original study it corresponds to. Same data, same marks, no new analysis. Each
   redrawn figure goes through the figure gate again.
2. Report. Have the writer rewrite the report from scratch with the redrawn figures. Use the current report
   (report/report.md) and the evidence as the source of facts and citations, not of wording. Remove sections that
   no longer fit.
   - Reader: a researcher from a neighbouring field who has not read the study. The main text should take about
     20 minutes to read; technical details go to an appendix.
   - Start with a summary: the question, the answer in a few sentences, and which of the study's findings were
     reproduced, partly reproduced, not reproduced or could not be tested here.
   - Then: the original study in a few sentences; the data and method in plain words, with a small worked example
     of how the disruption score is computed; one section per main finding of the study (what the study found,
     what we found, the figure, the verdict); the comparison table; what could not be tested and why;
     limitations; an appendix with the technical details (sample and weights, how the citation counts were
     checked, the full table of estimates with 95% intervals).
   - The main analysis covers the papers cited at least once. The version that also includes the papers that
     were never cited (whose score is zero) is a robustness check: say in one sentence that it gives nearly the
     same results, and keep its numbers in the appendix table.
   - Describe the final analysis only, not the history of the run (stages, corrections, earlier versions).
   - No how-to-reproduce section and no account of the agents' workflow: the harness adds both when it exports
     the package. Do not estimate times or costs.
   - Every number cites the artifact it comes from; facts about the original study cite [brief]. Describe the
     study in your own words, without quoting it. Report what did not reproduce as plainly as what did.

Stop when the report gate has released the report. Report to the user: the PDF path, the gate outcome, and
anything left open.
