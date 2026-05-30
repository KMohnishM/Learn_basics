"""
MODULE 5 - SCRIPT 1: Document Loading and Chunking.

This script demonstrates how to load text documents and slice them into semantic 
chunks using RecursiveCharacterTextSplitter.
"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Create a sample document containing detailed guidelines
document_content = (
    "# Zenith Tech Support Guide\n\n"
    "## 1. Network Issues\n"
    "If your Zenith router shows a blinking amber light, it indicates a loss of WAN connection. "
    "To resolve this, power cycle the modem by unplugging its power cord for 30 seconds. "
    "Reconnect the power cord and wait 2 minutes for full reboot sync.\n\n"
    "## 2. Password Resets\n"
    "To perform a hard factory reset on the security portal, locate the recessed pinhole button "
    "on the back of the device. Using a paperclip, press and hold the button for 15 seconds. "
    "The default credentials will revert to Admin / Password123.\n\n"
    "## 3. Contact Support\n"
    "For issues not resolved by this guide, contact the helpdesk at support@zenithtech.internal "
    "or dial extension 4900 between 9 AM and 5 PM EST."
)

# Wrap in a generic LangChain Document object
doc = Document(
    page_content=document_content,
    metadata={"source": "zenith_guide.md", "category": "internal_procedures"}
)

print("=== ORIGINAL DOCUMENT ===")
print(f"Characters count: {len(doc.page_content)}")
print("Source metadata: ", doc.metadata)
print("=========================\n")


# 1. Initialize the RecursiveCharacterTextSplitter
# We choose a small chunk size of 150 characters to clearly see the splits,
# with a chunk overlap of 30 characters.
splitter = RecursiveCharacterTextSplitter(
    chunk_size=150,
    chunk_overlap=30,
    add_start_index=True # Keeps track of where the chunk started in the original document
)

# 2. Perform the splitting operation
chunks = splitter.split_documents([doc])

print(f"=== SPLITTING RESULTS (Total Chunks: {len(chunks)}) ===")
for idx, chunk in enumerate(chunks):
    print(f"\n[Chunk #{idx}]")
    print(f"Length: {len(chunk.page_content)} characters | Start Index: {chunk.metadata.get('start_index')}")
    print("Content preview:")
    # Print double-quoted block to see exact whitespace structures
    print(f'"{chunk.page_content}"')
    print("-" * 50)
