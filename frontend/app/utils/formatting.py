 def format_sources(sources: list) -> str:
    """Format source citations"""
    if not sources:
        return ""
    
    formatted = "Sources:\n"
    for source in sources:
        formatted += f"- {source['doc_name']}, Page {source['page']}\n"
    return formatted