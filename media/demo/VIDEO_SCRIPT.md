# EvidenceTrail demo narration

English narration used by `scripts/render_video.py`. Visuals must come from the genuine live run.

| Time | Narration | Visual |
| --- | --- | --- |
| 0:00–0:18 | A useful research answer needs more than confident writing. It needs a path back to the original evidence. EvidenceTrail is an AI research agent designed to make that path visible, from the first question to every cited source and every uncertainty in the final report. | Title and problem |
| 0:18–0:42 | We start with a practical question: what do recent studies say about heat pumps in cold climates? The question is entered in the real EvidenceTrail interface. Nebius Token Factory turns it into two focused searches, so the agent can examine different parts of the problem instead of relying on one broad query. | Actual Streamlit question entry |
| 0:42–1:12 | Tavily runs those queries against the live web. The research trace shows each search and how many usable results came back. For every result, the agent keeps the original URL and extracted content. It merges repeated URLs without losing their query history. Nebius then checks whether a material evidence gap calls for one more search. If it does, Tavily searches again. | Actual Tavily search trace |
| 1:12–1:42 | Now the source material goes to Nebius for synthesis. The model receives only the retrieved titles, URLs, and snippets, with source IDs assigned by EvidenceTrail. Retrieved pages are treated as untrusted data. The model is asked to separate supported facts from inference, describe conflicting findings, and state what remains uncertain. This report comes from this live run, not a stored answer. | Actual Nebius report |
| 1:42–1:56 | The report uses short citation IDs, such as S one. Each ID resolves to an original source URL you can open and inspect. Here we expand a real result and compare it with the passage Tavily returned. | Actual source detail |
| 1:56–2:10 | This is the original public page behind the citation. EvidenceTrail rejects unknown IDs and unverified links before displaying a report. Downloadable JSON preserves the question, sources, model, and timestamped trace. | Actual original source page |
| 2:10–2:30 | Behind the interface, the flow is explicit. The user asks a question. Nebius plans focused searches. Tavily retrieves evidence. EvidenceTrail deduplicates and checks for gaps. Nebius writes the synthesis. Citation validation runs before the answer reaches the user. Each step is visible in the trace. | Animated architecture |
| 2:30–2:40 | EvidenceTrail. Research you can trace. The public repository includes the code, setup, tests, and honest limitations. | Outro and public GitHub URL |

Target duration: 160 seconds. Pronunciation cues for local TTS: Nebius → “Neh bee us”; Tavily → “Tah villy”.
