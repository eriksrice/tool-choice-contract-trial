# Project Rename

The public project was renamed from **Tool Choice Contract Trial** to **Tool Choice Contract Evaluator**, and the canonical GitHub repository moved from `eriksrice/tool-choice-contract-trial` to `eriksrice/tool-choice-contract-evaluator`.

The naming migration is prospective rather than retroactive. The Python import package remains `tool_choice_contract_trial`, and the Python distribution metadata remains `tool-choice-contract-trial` to avoid an unrelated package migration. The supported module command therefore remains:

```bash
python -m tool_choice_contract_trial
```

Git history and hash-bound evidence were not rewritten. Historical Markdown reports, review materials, compatibility renderers, and provenance identifiers may retain the earlier title or slug when changing them would alter frozen or committed evidence. Those occurrences describe or reproduce artifacts created under the earlier name; they are not current project or repository references.

GitHub redirects the former repository URL to the renamed repository. The local checkout uses the renamed repository as its `origin` after the migration.
