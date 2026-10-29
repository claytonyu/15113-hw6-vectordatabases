# 15-113 HW6 - Vector Databases
My app is a arXiv searching command-line tool. Users can add individual arXiv papers, or add the latest articles from any category. Additionally, users can pin articles for later (this is retained across calls.)

## Database Entries
I store arXiv articles in the database, using the free arXiv API. Each entry holds one article's title and abstract, concatenated together. Since an abstract is small enough and is semantically very interconnected, I decided not to chunk the text. See Models Used for the limit of the feature (input) space.
I loaded 500 of the latest papers (250 from Computation and Language, 25 from Cell Behavior).
Metadata: title, authors, year published, url to arXiv, url to PDF, the article's primary category, as well as a list of all its categories.

## Two Queries
1. Query "extending in direction that follows least resistance"
  - Returns "Cognition as least action: the Physarum Lagrangian" (id: 2511.08531)
2. Query "how to make sure people follow through on their promises"
  - Returns "Words or Deeds? How LLMs Predict Users' Decisions in Human-Agent Dialogue" (id 2610.36813)
A keyword search searches for exact matches, so these two queries wouldn't match their corrresponding items in that case. However, in a query database, they may work. It was actually very difficult to get the exact paper the first time -- it always appeared in the top five results, but I needed to tweak the prompts to retrieve the correct paper at the first position.

## Data Collection
Data collection is automatically run by the script, collected from the arXiv website directly. Depending on machine and connection, it should 2-3 minutes to fully download and embed all 500 initial entries.

## Models Used
I'm using the ChromeDB mentioned in class, but using a different embedding model called BAAI/bge-base-en-v1.5. This one is found on SentenceTransformers, was used because its token count (512) was large enough to fit an entire abstract in one item. This was important because I believe chunking would not have been a good solution for my problem.
The model itself (~440 MB) downloads on the first run, taking about a minute. 

## How to run the app
This app should be run in the terminal, and requires dependencies found in requirements.txt.
Tested with Python 3.14.8

1. Setting up a venv:
```shell
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```
1. Or with uv (tested on my machine):
```shell
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

2. Start the tool (around ~3 min of setup on first load):
```shell
python main.py    # Just run the main file
```