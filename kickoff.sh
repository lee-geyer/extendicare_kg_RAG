#!/bin/bash

# Use current directory as project root
PROJECT_ROOT=$(pwd)
DOC_PATH="/Users/leegeyer/Library/CloudStorage/OneDrive-Extendicare(Canada)Inc/INTEGRATION FILES TARGETED"

echo "📁 Initializing Extendicare KG RAG project in: $PROJECT_ROOT"

# Step 1: Create folder structure
mkdir -p data/{raw,parsed,metadata} scripts models configs

# Step 2: Copy agents.md if available one directory above
if [ -f "../agents.md" ]; then
  cp ../agents.md .
  echo "✅ Copied agents.md"
else
  echo "⚠️  agents.md not found one level above — skipping copy"
fi

# Step 3: Create symbolic link to Extendicare Knowledge Base
ln -s "$DOC_PATH" data/raw/extendicare_kb 2>/dev/null || echo "🔁 Symlink already exists or failed"

# Step 4: Initialize Git repo
git init
echo -e "# Extendicare Knowledge Graph RAG\n\nThis repo supports document parsing, indexing, and hybrid RAG over Extendicare policies." > README.md

# Step 5: Create .gitignore
cat <<EOL > .gitignore
__pycache__/
.env
*.pyc
*.pkl
*.sqlite
*.log
.vscode/
.ipynb_checkpoints/
data/raw/*
!data/raw/extendicare_kb
EOL

# Step 6: Create requirements.txt
cat <<EOL > requirements.txt
llama-cloud-services
openai
qdrant-client
neo4j
pydantic
sentence-transformers
fastapi
uvicorn
python-dotenv
EOL

# Step 7: Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 8: Create FastAPI app starter
cat <<EOL > scripts/api.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Extendicare Knowledge Graph RAG API"}
EOL

# Step 9: GitHub setup (optional)
echo ""
read -p "Would you like to create a GitHub repo and push the initial commit? (y/n): " CONFIRM
if [[ "\$CONFIRM" == "y" ]]; then
  read -p "GitHub repo name (e.g., extendicare_kg_RAG): " REPO_NAME
  read -p "GitHub username: " GH_USER
  git remote add origin git@github.com:\$GH_USER/\$REPO_NAME.git
  git add .
  git commit -m "Initial scaffold"
  git branch -M main
  git push -u origin main
fi

echo ""
echo "✅ Project scaffold complete!"
echo "📂 Folder: $PROJECT_ROOT"
echo "🚀 To activate your environment: source .venv/bin/activate"
echo "▶️  To run FastAPI app: uvicorn scripts.api:app --reload"