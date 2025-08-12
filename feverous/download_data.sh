mkdir -p data
wget -O data/dev.jsonl https://fever.ai/download/feverous/feverous_dev_challenges.jsonl
wget -O data/feverous-wiki-pages-db.zip https://fever.ai/download/feverous/feverous-wiki-pages-db.zip
unzip data/feverous-wiki-pages-db.zip -j data/feverous_wikiv1.db
