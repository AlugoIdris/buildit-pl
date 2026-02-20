# BuildIt PL
AI-powered construction and renovation assistant for expats in Poland.

## Quick Start
```bash
pip install -r requirements.txt
cp .env.example .env
python knowledge_base/seed_kb.py
python ingestion/loader.py
streamlit run app/streamlit_app.py
```

## Model Strategy
| Query type | Model | Cost/1M tokens |
|---|---|---|
| General | gpt-4o-mini | $0.15 in / $0.60 out |
| Legal/permit | gpt-4o | $2.50 in / $10.00 out |
| Embeddings | text-embedding-3-small | $0.02 in |

Est. cost per query: ~$0.0001 to $0.001

## Roadmap
- [x] V1: RAG Q&A on Polish construction law
- [ ] V2: Document upload and contract analysis
- [ ] V3: Contractor trust scoring
- [ ] V4: Budget estimator with regional pricing
