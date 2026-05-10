from dataclasses import dataclass
from app.config import get_settings

@dataclass
class Chunk:
    text: str
    source_file: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict

class SemanticChunker:
    def __init__(self):
        self.settings = get_settings()

    def chunk_text(self, text: str, source_file: str, metadata: dict | None = None) -> list[Chunk]:
        chunk_size = self.settings.chunk_size
        overlap = self.settings.chunk_overlap
        metadata = metadata or {}
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text.strip()]
        chunks = []
        current_text = ""
        chunk_idx = 0
        char_offset = 0
        for para in paragraphs:
            if len(current_text) + len(para) > chunk_size and current_text:
                chunks.append(Chunk(
                    text=current_text.strip(), source_file=source_file,
                    chunk_index=chunk_idx, start_char=char_offset,
                    end_char=char_offset + len(current_text), metadata={**metadata},
                ))
                chunk_idx += 1
                char_offset += len(current_text) - overlap
                overlap_text = current_text[-overlap:] if overlap > 0 else ""
                current_text = overlap_text + "\n\n" + para
            else:
                current_text = (current_text + "\n\n" + para) if current_text else para
        if current_text.strip():
            chunks.append(Chunk(
                text=current_text.strip(), source_file=source_file,
                chunk_index=chunk_idx, start_char=char_offset,
                end_char=char_offset + len(current_text), metadata={**metadata},
            ))
        return chunks

    def chunk_file(self, filepath: str, source_file: str | None = None) -> list[Chunk]:
        from pathlib import Path
        path = Path(filepath)
        source = source_file or path.name
        text = path.read_text(encoding="utf-8", errors="replace")
        meta = {"file_size": path.stat().st_size, "file_type": path.suffix, "modified": path.stat().st_mtime}
        return self.chunk_text(text, source, meta)
