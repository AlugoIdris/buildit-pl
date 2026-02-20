# Deploying BuildIt PL to Streamlit Cloud (Free)

## Prerequisites
- GitHub account
- OpenAI API key
- Streamlit Community Cloud account (free at share.streamlit.io)

## Steps

### 1. Create GitHub repo
```bash
cd buildit-pl
git init
git add .
git commit -m "feat: initial BuildIt PL MVP"
git remote add origin https://github.com/YOUR_USERNAME/buildit-pl.git
git push -u origin main
```

### 2. Seed knowledge base (run locally first)
```bash
python knowledge_base/seed_kb.py   # downloads PDFs
python ingestion/loader.py          # builds chroma_store/
git add knowledge_base/*.pdf chroma_store/
git commit -m "feat: add knowledge base"
git push
```

### 3. Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect your GitHub repo: `YOUR_USERNAME/buildit-pl`
4. Main file path: `streamlit_app.py`
5. Click "Advanced settings" → Add secrets:
   ```
   OPENAI_API_KEY = "sk-..."
   ```
6. Click "Deploy" — live in ~2 minutes ✅

### 4. Share the URL
Streamlit Cloud gives you a free URL:
`https://YOUR_USERNAME-buildit-pl-streamlit-app-XXXX.streamlit.app`

Share this in expat Facebook groups, Reddit r/poland, Warsaw expat Slack!
