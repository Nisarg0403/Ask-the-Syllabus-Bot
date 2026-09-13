import re
from typing import List, Dict, Tuple, Optional

PRONOUN_REFERENCE_PATTERNS = [
    re.compile(r'\b(it|its|this|that|these|those|they|them|the topic|this topic|that topic|this section|that section|the previous point|the previous topic)\b', re.IGNORECASE)
]

TECHNICAL_IDENTIFIER_PATTERN = re.compile(r'\b(topic\s+\d+|unit\s+\d+|chapter\s+\d+|cs\d+|lab\s+\d+|assignment\s+\d+)\b', re.IGNORECASE)

def normalize_query(query: str) -> str:
    """
    Safely normalizes raw query text:
    - Strips leading/trailing whitespace
    - Collapses internal whitespace
    - Preserves letters, numbers, casing, technical terms, and punctuation
    """
    if not query:
        return ""
    cleaned = query.strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned

def is_follow_up_query(query: str) -> bool:
    """
    Determines if query contains reference pronouns or is dependent on conversational history.
    """
    normalized = normalize_query(query)
    for pattern in PRONOUN_REFERENCE_PATTERNS:
        if pattern.search(normalized):
            return True
    return False

def extract_topic_or_subject(history: List[Dict[str, str]]) -> Optional[str]:
    """
    Extracts key topic, subject, or technical identifier from recent dialogue turns (max 4 turns).
    """
    for turn in reversed(history[-4:]):
        content = turn.get("content", "") or turn.get("message", "") or turn.get("text", "")
        if not content:
            continue
        
        # Check for explicit technical identifiers (e.g. Topic 162)
        match = TECHNICAL_IDENTIFIER_PATTERN.search(content)
        if match:
            return match.group(0).strip()
            
        # Check for bold or subject phrases
        bold_match = re.search(r'\*\*([^*]+)\*\*', content)
        if bold_match and len(bold_match.group(1).strip()) < 40:
            return bold_match.group(1).strip()
            
        # Look for "discussing X" or "about X"
        disc_match = re.search(r'\b(?:discussing|about|regarding)\s+([A-Za-z0-9\s]{3,30})\b', content, re.IGNORECASE)
        if disc_match:
            return disc_match.group(1).strip()

    return None

def rewrite_query(
    query: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    llm=None
) -> Tuple[str, str]:
    """
    Query Transformation & Multi-Turn Context Transformation Engine:
    
    Returns:
        - original_query: Exact query string supplied by user
        - rewritten_query: Cleaned / contextualized query for retrieval engine
    """
    original_query = query
    normalized = normalize_query(query)

    # 1. No chat history or standalone query without reference pronouns -> Return normalized query
    if not chat_history or not is_follow_up_query(normalized):
        return original_query, normalized

    # 2. Extract recent topic/subject context from dialogue history (max 4 turns)
    topic_context = extract_topic_or_subject(chat_history)

    if not topic_context:
        # Unable to reliably extract subject from context -> Prefer original normalized query to avoid hallucination
        return original_query, normalized

    # 3. Perform safe reference resolution
    rewritten = normalized
    # Replace possessive pronouns
    rewritten = re.sub(r'\b(its|it\'s)\b', f"{topic_context}'s", rewritten, flags=re.IGNORECASE)
    # Replace direct pronouns and references
    rewritten = re.sub(r'\b(it|this|that|the topic|this topic|that topic|this section|that section)\b', topic_context, rewritten, flags=re.IGNORECASE)

    rewritten = normalize_query(rewritten)
    
    # 4. Verification Guardrail: Never let rewritten query lose original question intent
    if not rewritten or len(rewritten) < len(normalized):
        return original_query, normalized

    return original_query, rewritten
