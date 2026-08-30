import re
import logging


def strip_html_comment(text: str) -> str:
    """Remove HTML comment from line 1, return clean text from line 2 onward."""
    lines = text.split('\n')
    return '\n'.join(lines[1:])


def extract_doc_id(filename: str) -> str:
    """Extract doc_id from filename (without .md extension)."""
    return filename.replace('.md', '')


def extract_title(text: str) -> str:
    """Extract H1 title from line 3, strip '# ' prefix."""
    lines = text.split('\n')
    title_line = lines[2]
    return title_line.lstrip('# ').strip()


def extract_effective_date(header_line: str, filename: str) -> str | None:
    """Parse effective date from header, handling 4 label variants.

    CRITICAL: Check longest label first to avoid D4 trap.
    D4 has: **Issued:** 2026-04-15 | **Effective for losses on or after:** 2026-05-01
    Must extract 2026-05-01, not 2026-04-15.
    """
    patterns = [
        r'\*\*Effective for losses on or after:\*\* (\d{4}-\d{2}-\d{2})',
        r'\*\*Effective:\*\* (\d{4}-\d{2}-\d{2})',
        r'\*\*Last reviewed:\*\* (\d{4}-\d{2}-\d{2})',
        r'\*\*Date:\*\* (\d{4}-\d{2}-\d{2})'
    ]

    for pattern in patterns:
        match = re.search(pattern, header_line)
        if match:
            return match.group(1)

    logging.warning(f"{filename}: No date label found in '{header_line}'")
    return None


def derive_authority_tier(doc_id: str) -> str:
    """Map filename prefix to authority tier."""
    prefix = doc_id[0].upper()
    mapping = {
        'A': 'policy',
        'B': 'procedure',
        'C': 'reference',
        'D': 'comms'
    }
    return mapping[prefix]


def derive_form(header_line: str) -> str:
    """Derive form type from form codes in header.

    ACME-PA-2025 only → 'personal'
    ACME-CF-2025 only → 'fleet'
    Both or neither → 'both'
    """
    has_personal = 'ACME-PA-2025' in header_line
    has_fleet = 'ACME-CF-2025' in header_line

    if has_personal and not has_fleet:
        return 'personal'
    elif has_fleet and not has_personal:
        return 'fleet'
    else:
        return 'both'
