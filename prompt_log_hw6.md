# 15-113 HW6 - Prompt Log
## Tools Used
Claude Sonnet 5.5 on High was used for the majority of the exploring of ChromaDB, coding, and refactoring. All work was done in the Kiro IDE app.
## Development Process
- First, I explored the arXiv API to make sure this idea was possible, getting an idea of what the returned data looked like.
  - I then built the core paper & abstract bulk retrieval loop, eventually building in concurrency into it (running concurrent with embedding)
- Next, I built the main embedding / retrieval functionality, where I tested the two prompts I had.
  - I then added the functions to add new papers (individually, and by topic)
- I switched to a larger model (bge-base-en-v1.5) after doing more research about the input limits (abstracts are at most ~350 words long).
- Lastly, I wrapped a text user interface around the code and refactored it to be neater.
  - Made small adjustments like displaying an article's arXiv id instead of its year
  - Made it display all valid arXiv categories when prompted.

## Selected Prompts

### Initial Exploration of arXiv API
I want to get titles, abstracts, authors, years, and links of papers from ArXiV's API, in bulk (~1000 papers total). Explain the main endpoints and workflow for doing this, and write some sample code to retrieve some data.

### Adding Concurrency to fetching + Reformatting code
Change the code to handle concurrently fetching arxiv and embedding, since it takes a lot of time.

Can you also make your code more modular?

Also refactor the code to follow good coding practices (e.g. KISS)

### Preparing for the "Create" of CRUD - allowing the user to search for a paper by id
Also create a arxiv_client function that searches the API for a single paper by id and returns that paper.

### Categorizing articles by arXiv categories
Allow for a system to retrieve & embed different categories on arxiv, and detect if different categories were already embedded/retrieved.

### Creating the TUI
Wrap a text user interface around this tool, which should be called by main. This can just be a menu loop. If too many things are happening, you can split this into multiple files.  
  
The interface should:  
  
- Allow the user to query papers by searching in natural language. This should only return name and year.  
  - Allow the user to tweak how many entries they see at once.  
- For any paper, allow the user to:  
  - View it - display all metadata on it that we have, in a nice format.  
  - "Save/pin" papers. If this command is used without a label, it refers to the most recently viewed paper. Also label/number returned queries to make pinning easier.  
- Adding to the database:  
  - Given a arXiv paper id, search it up and add it to the database.  
  - Given an arXiv category, retrieve k recent papers (allow specification) in that category and add it.


### Final reformatting
move all py files into src (except for main), but keep data where it is now in /chroma_store.

Update all references.