1. quick prototype, analyze output, then use that to drive development

|                                 | Evaluate with code (objective) | Evaluate with LLM (subjective) |
| :------------------------------ | :----------------------------- | :----------------------------- |
| **Per example ground truth**    | ✅                             | ✅                             |
| **No per example ground truth** | ❌                             | ✅                             |

Tips:

1. quick and dirty evals is ok to start. Then, iterate.
2. Find places twhere evals fail to capture human judgement. That is an opportunity! iterate.
3. Look for plqces where performance is worse than humans.

Error analysis:
