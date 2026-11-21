# Integration evidence

Status: **not yet fully verified**.

- Nebius model listing succeeded using the user's local API key: 24 model IDs returned.
- Selected available model: `Qwen/Qwen3-30B-A3B-Instruct-2507`.
- First real chat-completion attempt failed with HTTP 402 `credit_balance_exhausted`; no Nebius inference result exists yet.
- A repeat chat-completion attempt at 2026-11-21 05:10 UTC still failed with HTTP 402. No successful Nebius inference has occurred.
- Tavily search succeeded using the user's local API key. Query: `cold climate heat pumps performance field study`; 3 results returned with source URLs. This is a service smoke test, not a full agent run.
  - https://research-hub.nlr.gov/en/publications/field-validation-of-air-source-heat-pumps-for-cold-climates
  - https://www.aceee.org/wp-content/uploads/ssb2024/Rising%20up%20to%20the%20Challenge%20-%20Cold%20Climate%20Heat%20Pumps%20in%20the%20Field.pdf
  - https://heatpumpdata.energy.gov/data/studies/nrel-field-validation-air-source-heat-pumps-cold-climates-2021-2023
