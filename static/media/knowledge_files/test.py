from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader

# Set up the parser
parser = LlamaParse(
    api_key="llx-3pchZiHONc25URdAcljgWpToR5aykmaBtGjEP8vzTkw6qUI3",
    result_type="markdown"  # "markdown" and "text" are available
)
#print(parser.load_data("Projects_ideas__ttuLBHI.pdf"))

# Use SimpleDirectoryReader to parse our file
file_extractor = {".pdf": parser}

# Ensure the file path is correct
input_files = ["canada.pdf"]
#print(parser.parse_file("Projects_ideas_.pdf").load_data())
# Check if the file exists
import os
for file in input_files:
    if not os.path.exists(file):
        raise FileNotFoundError(f"The file '{file}' does not exist. Please check the file path.")

# Load the data
print(documents)
