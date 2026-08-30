import logging
from pathlib import Path
from . import parser, storage

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def ingest(documents_path: str) -> int:
    """Load, parse, embed and store corpus documents.

    Returns the number of chunks stored.

    Raises:
        ValueError: If document count is not exactly 20
    """
    doc_dir = Path(documents_path)
    md_files = sorted(doc_dir.glob('*.md'))

    if len(md_files) != 20:
        raise ValueError(
            f"Expected 20 documents, found {len(md_files)} in {documents_path}"
        )

    ids = []
    documents = []
    metadatas = []

    for filepath in md_files:
        filename = filepath.name
        print(f"Loading: {filename}")

        text = filepath.read_text()
        lines = text.split('\n')
        header_line = lines[3]

        doc_id = parser.extract_doc_id(filename)
        title = parser.extract_title(text)
        effective_date = parser.extract_effective_date(header_line, filename)
        authority_tier = parser.derive_authority_tier(doc_id)
        form = parser.derive_form(header_line)

        clean_text = parser.strip_html_comment(text)

        ids.append(doc_id)
        documents.append(clean_text)
        metadatas.append({
            'doc_id': doc_id,
            'title': title,
            'effective_date': effective_date,
            'authority_tier': authority_tier,
            'form': form
        })

    client = storage.get_chroma_client()
    collection = storage.reset_collection(client, "acme_auto_corpus")

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    count = collection.count()
    logging.info(f"Ingestion complete: {count} chunks stored")

    return count
