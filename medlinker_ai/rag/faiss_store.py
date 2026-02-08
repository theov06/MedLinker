"""FAISS-based RAG retrieval for MedLinker AI.

This module provides optional FAISS-based retrieval to improve Q&A performance.
Falls back to TF-IDF if FAISS is not available.
"""

import os
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

from medlinker_ai.models import FacilityAnalysisOutput, RegionSummary


# Try to import FAISS (optional)
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

# Always available: sklearn for TF-IDF fallback
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def is_rag_available() -> bool:
    """Check if RAG is enabled via environment variable.
    
    Returns:
        True if RAG_ENABLED=1 is set
    """
    return os.environ.get("RAG_ENABLED", "0") == "1"


def build_facility_text(facility: FacilityAnalysisOutput) -> str:
    """Build searchable text from facility output.
    
    Args:
        facility: Facility analysis output
        
    Returns:
        Concatenated searchable text
    """
    caps = facility.extracted_capabilities
    parts = [
        facility.facility_id,
        facility.status,
        " ".join(caps.services),
        " ".join(caps.equipment),
        " ".join(caps.staffing),
        " ".join(facility.reasons)
    ]
    return " ".join(parts)


def build_region_text(region: RegionSummary) -> str:
    """Build searchable text from region summary.
    
    Args:
        region: Region summary
        
    Returns:
        Concatenated searchable text
    """
    parts = [
        region.country,
        region.region,
        f"desert_score_{region.desert_score}",
        " ".join(region.missing_critical),
        " ".join(region.coverage.get("services", {}).keys()),
        " ".join(region.coverage.get("equipment", {}).keys()),
        " ".join(region.coverage.get("staffing", {}).keys())
    ]
    return " ".join(parts)


def build_indexes(
    facilities: List[FacilityAnalysisOutput],
    regions: List[RegionSummary],
    out_dir: str = "outputs/faiss"
) -> None:
    """Build FAISS indexes for facilities and regions.
    
    Args:
        facilities: List of facility outputs
        regions: List of region summaries
        out_dir: Output directory for indexes
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Build facility texts and metadata
    facility_texts = [build_facility_text(f) for f in facilities]
    facility_ids = [f.facility_id for f in facilities]
    
    # Build region texts and metadata
    region_texts = [build_region_text(r) for r in regions]
    region_keys = [f"{r.country}-{r.region}" for r in regions]
    
    # Use TF-IDF vectorizer (lightweight, always available)
    vectorizer = TfidfVectorizer(max_features=512, stop_words='english')
    
    # Fit and transform facility texts
    if facility_texts:
        facility_vectors = vectorizer.fit_transform(facility_texts).toarray().astype('float32')
        
        # Save vectorizer vocabulary for later use
        vocab_path = out_path / "vocab.json"
        # Convert vocabulary dict values to regular Python ints
        vocab_dict = {k: int(v) for k, v in vectorizer.vocabulary_.items()}
        with open(vocab_path, 'w') as f:
            json.dump({
                "vocabulary": vocab_dict,
                "idf": vectorizer.idf_.tolist()
            }, f)
        
        if FAISS_AVAILABLE:
            # Use FAISS if available
            dimension = facility_vectors.shape[1]
            facility_index = faiss.IndexFlatL2(dimension)
            facility_index.add(facility_vectors)
            faiss.write_index(facility_index, str(out_path / "facilities.index"))
        else:
            # Save vectors as numpy array (fallback)
            np.save(out_path / "facilities_vectors.npy", facility_vectors)
        
        # Save facility metadata
        with open(out_path / "facilities_meta.json", 'w') as f:
            json.dump(facility_ids, f)
    
    # Transform region texts using same vectorizer
    if region_texts:
        region_vectors = vectorizer.transform(region_texts).toarray().astype('float32')
        
        if FAISS_AVAILABLE:
            dimension = region_vectors.shape[1]
            region_index = faiss.IndexFlatL2(dimension)
            region_index.add(region_vectors)
            faiss.write_index(region_index, str(out_path / "regions.index"))
        else:
            np.save(out_path / "regions_vectors.npy", region_vectors)
        
        # Save region metadata
        with open(out_path / "regions_meta.json", 'w') as f:
            json.dump(region_keys, f)
    
    print(f"Built RAG indexes in {out_dir}")
    print(f"  Facilities: {len(facility_ids)}")
    print(f"  Regions: {len(region_keys)}")
    print(f"  Using: {'FAISS' if FAISS_AVAILABLE else 'TF-IDF fallback'}")


def load_indexes(out_dir: str = "outputs/faiss") -> Optional[Dict[str, Any]]:
    """Load FAISS indexes and metadata.
    
    Args:
        out_dir: Directory containing indexes
        
    Returns:
        Dictionary with indexes and metadata, or None if not found
    """
    out_path = Path(out_dir)
    
    # Check if indexes exist
    vocab_path = out_path / "vocab.json"
    fac_meta_path = out_path / "facilities_meta.json"
    reg_meta_path = out_path / "regions_meta.json"
    
    if not vocab_path.exists() or not fac_meta_path.exists():
        return None
    
    # Load vocabulary
    with open(vocab_path) as f:
        vocab_data = json.load(f)
    
    # Reconstruct vectorizer
    vectorizer = TfidfVectorizer(max_features=512, stop_words='english')
    vectorizer.vocabulary_ = vocab_data["vocabulary"]
    vectorizer.idf_ = np.array(vocab_data["idf"])
    
    # Load facility metadata
    with open(fac_meta_path) as f:
        facility_ids = json.load(f)
    
    # Load facility index
    if FAISS_AVAILABLE and (out_path / "facilities.index").exists():
        facility_index = faiss.read_index(str(out_path / "facilities.index"))
        facility_vectors = None
    else:
        facility_index = None
        vec_path = out_path / "facilities_vectors.npy"
        facility_vectors = np.load(vec_path) if vec_path.exists() else None
    
    # Load region metadata and index
    region_keys = None
    region_index = None
    region_vectors = None
    
    if reg_meta_path.exists():
        with open(reg_meta_path) as f:
            region_keys = json.load(f)
        
        if FAISS_AVAILABLE and (out_path / "regions.index").exists():
            region_index = faiss.read_index(str(out_path / "regions.index"))
        else:
            vec_path = out_path / "regions_vectors.npy"
            region_vectors = np.load(vec_path) if vec_path.exists() else None
    
    return {
        "vectorizer": vectorizer,
        "facility_index": facility_index,
        "facility_vectors": facility_vectors,
        "facility_ids": facility_ids,
        "region_index": region_index,
        "region_vectors": region_vectors,
        "region_keys": region_keys
    }


def retrieve(
    question: str,
    k_fac: int = 8,
    k_reg: int = 5,
    index_dir: str = "outputs/faiss"
) -> Optional[Tuple[List[str], List[str]]]:
    """Retrieve relevant facility IDs and region keys using RAG.
    
    Args:
        question: User question
        k_fac: Number of facilities to retrieve
        k_reg: Number of regions to retrieve
        index_dir: Directory containing indexes
        
    Returns:
        Tuple of (facility_ids, region_keys) or None if indexes not available
    """
    # Load indexes
    indexes = load_indexes(index_dir)
    if indexes is None:
        return None
    
    vectorizer = indexes["vectorizer"]
    
    # Vectorize question
    question_vec = vectorizer.transform([question]).toarray().astype('float32')
    
    # Retrieve facilities
    facility_ids = []
    if indexes["facility_index"] is not None:
        # Use FAISS
        distances, indices = indexes["facility_index"].search(question_vec, k_fac)
        facility_ids = [indexes["facility_ids"][i] for i in indices[0] if i < len(indexes["facility_ids"])]
    elif indexes["facility_vectors"] is not None:
        # Use cosine similarity fallback
        similarities = cosine_similarity(question_vec, indexes["facility_vectors"])[0]
        top_indices = np.argsort(similarities)[::-1][:k_fac]
        facility_ids = [indexes["facility_ids"][i] for i in top_indices if i < len(indexes["facility_ids"])]
    
    # Retrieve regions
    region_keys = []
    if indexes["region_keys"]:
        if indexes["region_index"] is not None:
            # Use FAISS
            distances, indices = indexes["region_index"].search(question_vec, k_reg)
            region_keys = [indexes["region_keys"][i] for i in indices[0] if i < len(indexes["region_keys"])]
        elif indexes["region_vectors"] is not None:
            # Use cosine similarity fallback
            similarities = cosine_similarity(question_vec, indexes["region_vectors"])[0]
            top_indices = np.argsort(similarities)[::-1][:k_reg]
            region_keys = [indexes["region_keys"][i] for i in top_indices if i < len(indexes["region_keys"])]
    
    return facility_ids, region_keys
