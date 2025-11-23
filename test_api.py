from semanticscholar import SemanticScholar
sch = SemanticScholar()
print("Searching...")
try:
    results = sch.search_paper("Artificial Intelligence Education", limit=1)
    print(f"Found: {results[0].title}")
except Exception as e:
    print(f"Error: {e}")
