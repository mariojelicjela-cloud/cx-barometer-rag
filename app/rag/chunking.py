from dataclasses import dataclass
from typing import Dict, Any, List
from langchain_text_splitters import RecursiveCharacterTextSplitter

@dataclass
class DocItem:
    text: str
    metadata: Dict[str, Any]

def split_unstructured(text: str, metadata: Dict[str, Any]) -> List[DocItem]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )

    chunks = splitter.split_text(text)

    return [
        DocItem(text=c, metadata=metadata)
        for c in chunks
    ]