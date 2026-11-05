# ShipReady complete repository context

This ZIP is a normalized context store for later analysis or API automation.

- `chunks.jsonl` contains each source-code section exactly once.
- `connections.jsonl` contains verified cross-file links.
- `selections.jsonl` maps each source file to precomputed narrow, optimal and wider connected contexts.
- Join a selection's `chunk_ids` to `chunks.jsonl` before sending one context to an LLM.

Do not send this entire ZIP as one LLM request. Process one selected context at a time and cite the original file and line fields.
