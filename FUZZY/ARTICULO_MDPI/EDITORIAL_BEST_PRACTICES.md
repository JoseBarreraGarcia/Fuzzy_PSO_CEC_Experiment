# Editorial Best Practices for Scientific Manuscripts

**Purpose.** This is the single active editorial and scientific-writing guide for manuscripts developed in this project. It consolidates the project’s guidance on academic prose, captions, evidence, structure, consistency, and submission checks. Apply journal-specific requirements when they are stricter. Keep project decisions and task histories in their own records; do not treat them as general writing rules.

## 1. Editorial Principles

- Make the scientific question, contribution, evidence, and limits identifiable to the intended journal’s readership.
- Prefer precise, economical prose over rhetorical emphasis, formulaic transitions, or repeated summaries.
- Preserve the authors’ terminology and voice while improving clarity and consistency.
- Distinguish observed results, statistical inference, interpretation, and speculation.
- Never invent data, methods, citations, references, novelty claims, or author contributions. Verify that every citation supports the statement attached to it.
- Do not edit text to evade AI detectors or imitate a presumed “human” style. Do not insert errors, unusual synonyms, or random variation. Tool classifications are not evidence of authorship.
- Keep internal notes, file paths, script names, audit histories, and agent instructions out of reader-facing text. Cite reproducibility resources only when they are actually available and in the appropriate availability statement.
- Use earlier manuscripts or conference papers only as internal organizational references unless a genuine scholarly citation is warranted. Do not copy their prose or describe the article as their extension without an approved scholarly and bibliographic basis. Rebuild figures and tables from the current study's data.

## 2. Build Claims from Evidence

Before drafting or revising a claim, identify its source, population, outcome, analysis unit, and uncertainty. Check that the strength of the wording matches the study design.

- Report the actual experimental unit, sample size, replication structure, exclusions, randomization or seed procedure, and any nesting or matching relevant to inference.
- State how outcomes were calculated and aggregated. Distinguish run-level values, per-instance summaries, per-function summaries, and class/subset aggregates.
- Keep estimands distinct: dispersion of ranks, dispersion of normalized gaps, and fitness differences are not interchangeable. A change in rank does not quantify the magnitude of an objective-value improvement.
- Distinguish descriptive summaries from inferential tests. Do not call an exploratory or descriptive pattern a confirmed effect or interaction.
- Report effect size as well as statistical significance where relevant. Define the direction of the effect, test sidedness, alpha, and multiplicity family/correction.
- A non-significant test is not evidence of equivalence, independence, absence of an effect, or a tie in outcomes. Use “non-significant” for tests; reserve “tie” for an explicitly defined equal-rank or equal-value result.
- Avoid causal language unless the design identifies a causal effect. Avoid generalizing beyond the sampled systems, benchmarks, conditions, or population.
- Do not interpret an instance-specific oracle selection as an implementable policy. Do not present a post hoc threshold as prespecified.
- If methods, data, or procedures change, check every dependent statistic, table, figure, and claim. Do not patch one number in isolation.

## 3. Article Structure and Argument

Use each section for its scientific function:

- **Title and abstract:** identify the topic and contribution; summarize the design, principal verified findings, and scope without claiming more than the evidence supports.
- **Introduction:** define the problem, explain the specific gap, state the research question and contribution, and cite verified sources. Avoid broad claims of importance or novelty without support.
- **Methods:** describe what was done in sufficient detail to reproduce the analysis. Use past tense for completed procedures; define notation, units, benchmarks, sample structure, tests, and corrections.
- **Results:** report observations and estimates, with enough context to understand denominators and comparisons. Do not turn the Results section into a list of unexplained p-values or repeat the full method in every paragraph.
- **Discussion:** interpret why the observations matter, relate them to the study question, and distinguish plausible explanations from tested mechanisms. Do not simply restate tables.
- **Limitations:** identify design constraints and their inferential consequences. Preserve author-approved limitations text unless an inconsistency is found; request approval before a substantive change.
- **Conclusions and future work:** state what the evaluated evidence supports and its scope. Future work should describe genuine extensions, not unfinished analyses required to complete the current paper.

Completed studies must read as completed work. Remove planning language such as “will report,” “planned analysis,” “to be completed,” or “preliminary results not shown,” except when future work genuinely concerns a new study or extension.

Describe the adopted method and its inferential scope where readers need them. Consolidate repeated qualifications without strengthening the claims; retain discarded analyses and their chronology in research records rather than narrating them throughout Results, Discussion, and Conclusions.

## 4. Natural Academic English

- Replace vague openings and claims with the actual problem, object, conditions, and evidence.
- Use verbs that describe the work or observation: compared, estimated, increased, remained, differed, or was associated with.
- Remove redundant paraphrases, repeated transitions, decorative intensifiers, and long strings of abstract nouns.
- Vary sentence structure only to improve clarity; do not vary wording mechanically.
- Use active or passive voice according to emphasis and journal convention, not as a fixed rule.
- Separate statistical significance from practical importance. Use “significant” unambiguously and define its statistical meaning.
- Avoid categorical terms such as “proved,” “guarantees,” “universal,” or “optimal” unless the mathematical result and scope warrant them.
- Do not use detector-oriented word lists as editing rules. Revise for accuracy, readability, and authorial intent.

## 5. Tables, Figures, and Captions

Every table and figure must be generated from the current validated results and must agree with the surrounding text.

### Captions

A caption should identify what is shown and provide the minimum information needed to interpret the visual: population or instances, variables, units, aggregation, transformations, symbols, and essential test details. It should not duplicate the Results paragraph or carry the full interpretation.

- Put abbreviations, symbols, exceptions, thresholds, and detailed statistical conventions in a concise note when that reads more clearly.
- In the main text, explain why the item is included and the result the reader should notice; in the Discussion, interpret its implications.
- Keep captions concise but complete. Suggested word ranges are editorial heuristics, not journal limits; never remove information required for correct interpretation merely to shorten a caption.
- As a practical starting point, use roughly 15--30 words for a simple item, 25--50 for a multipanel figure or complex table, and up to about 35--65 for a statistically complex figure. Add separate notes when they improve readability; these ranges are not requirements.
- For multipanel figures, identify panels and explain shared or differing scales. Explain colours and markers if they are not self-evident.

### Tables and figures

- Before adding a table, identify its question, source, estimand, aggregation order, denominator, weighting, and information not already accessible in existing displays. Prefer adapting an existing table when it answers the same question; justify the additional space and interpretive risk of a new one.
- Give each item a descriptive title/caption, units, sample sizes or denominators, and notes for abbreviations and corrections.
- Make columns and groups easy to scan. Use consistent number precision and label uncertainty/statistical outcome categories explicitly.
- Check that captions, legends, notes, axes, panel labels, and text agree. Do not label non-significant tests as ties.
- Keep the body focused on the items needed to support the argument; place exhaustive matrices, per-instance details, and extended outputs in a clearly identified supplement.
- For a factorial benchmark paper, a useful body sequence is the overall ranking, class/function-level evidence, key factor contrasts, and representative dynamics. Full configuration matrices, all per-instance outcomes, complete trajectories, and extended tests generally belong in appendices or supplementary files, subject to the journal's structure and space limits.
- Inspect the rendered PDF, not only the source. Check that captions remain above/below their tables, notes do not float beside table bodies, equations do not spill into adjacent columns, and labels remain legible.
- Do not remove a table or figure based only on visual redundancy; verify that no text, equation, or appendix depends on it.

## 6. Mathematical and Statistical Presentation

- Define symbols before or at first use and use one notation consistently.
- State assumptions and the scope of propositions/theorems. A proof establishes only the property under those assumptions; do not extend it to empirical performance.
- Separate mathematical properties of a model from numerical verification and benchmark observations.
- State the test, independent/paired structure, sample sizes, sidedness, correction family, and effect-size direction accurately.
- Use consistent labels for wins, non-significant outcomes, losses, and rank ties; define them in tables and methods.
- When multiple functions, dimensions, configurations, or runs are nested or related, explain the aggregation and do not assume independence without justification.
- Treat descriptive dispersion as descriptive. Do not add a formal interaction claim or inferential test unless its estimand, design, and calibration are defensible and approved.

## 7. Terminology and Consistency

For this project’s Fuzzy-PSO manuscript, use the following terms consistently:

- Configuration names: `FCS-n-Rk` (for example, FCS-3-R1); define `n` and the rule-base pattern once.
- Use “rule-base pattern,” “fixed-dimensional multimodal,” and “normalized gap” consistently.
- Define `S1` as F1–F13 and `S2` as F14–F23 once, and use those labels consistently.
- Keep landscape classes distinct from dimensional subsets; do not attribute differences to modality or dimensionality alone when the groups are confounded.
- Use RQ1–RQ5 when presenting the current research questions. Do not rename historical data keys or scripts solely to match manuscript labels.
- For the current benchmark article, RQ3 is descriptive; no formal granularity-by-rule interaction is estimated. Run identifiers do not establish common-seed pairing across configurations.
- For the current benchmark article, RQ4 uses independent two-sided Mann–Whitney tests with Bonferroni adjustment across 1,984 comparisons; Table 11 is a separate 1,984-test family using independent two-sided Mann–Whitney tests with Holm adjustment. State these families separately.

These study-specific conventions describe the current article. Reassess them for a future study rather than applying them automatically to a different design.

## 8. Reproducibility and Availability Statements

- Verify that reported counts, seeds, configuration labels, test outputs, and figures correspond to the final analysis inputs.
- Preserve sufficient numerical precision in distributed data to reproduce ties, effect sizes, tests, and adjusted decisions; verify calculations from the exported file itself, not only from an internal data format.
- Distinguish recalculating statistics from supplied outcomes from reexecuting the optimizer with versioned code, benchmark definitions, configurations, seeds, and dependencies. Claim only the level supported by the delivered resources.
- Distinguish public deposits from materials supplied only as journal supplementary files or retained privately. Never claim a public repository, DOI, script, or raw-data deposit that does not exist.
- A reproducibility statement should identify the actual resources and access route at the time of submission, subject to author approval and journal policy.
- Keep reader-facing availability text concise; put the detailed data dictionary and file organization in the supplement README, not in the article body.

## 9. Revision and Submission Checklist

Before finalizing a manuscript:

1. Confirm the research questions, claims, methods, tables, figures, and conclusions describe the same analysis.
2. Check every number against its source table: sample sizes, run totals, ranks, effect sizes, p-values, confidence intervals, units, and denominators.
3. Confirm the analysis unit, pairing/independence, nesting, seed handling, and multiplicity correction are correctly stated.
4. Search for obsolete tests, outdated figures/tables, duplicate assets, placeholders, internal paths, agent notes, and planning language.
5. Check citations and bibliography keys; verify that each cited source supports the claim.
6. Compile the complete manuscript and any separate supplementary PDF with the intended build workflow. Resolve missing files, undefined references, and unintended layout overflow.
7. Inspect the rendered pages, including equations, table captions/notes, figure labels, appendices, and supplementary cross-references.
8. Preserve user-approved text and scientific conclusions. Seek author approval for changes to protected sections or changes in interpretation.
9. Report any unresolved discrepancy or build warning clearly; do not conceal it by deleting evidence or weakening a valid limitation.
