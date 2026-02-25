import plistlib
import base64
import re
from bs4 import BeautifulSoup, NavigableString, Doctype


def parse_webarchive(file_bytes: bytes) -> str:
    """Parse .webarchive file and extract plain text."""
    try:
        plist_data = plistlib.loads(file_bytes)
    except Exception:
        raise ValueError("Invalid .webarchive format")
    
    # Handle both MainResource and WebMainResource keys
    main_resource = plist_data.get("MainResource") or plist_data.get("WebMainResource")
    if not main_resource:
        raise ValueError("Webarchive missing main content")
    
    web_resource_data = main_resource.get("WebResourceData")
    if not web_resource_data:
        raise ValueError("Webarchive missing main content")
    
    # plistlib already decodes base64, data is raw bytes
    html_bytes = web_resource_data
    
    # Determine encoding
    encoding = main_resource.get("WebResourceTextEncodingName", "UTF-8")
    
    # Decode with error handling
    try:
        html_content = html_bytes.decode(encoding, errors='strict')
    except UnicodeDecodeError:
        html_content = html_bytes.decode(encoding, errors='replace')
    
    # Extract text from HTML
    text = html_to_text(html_content)
    
    return text


def html_to_text(html: str) -> str:
    """Convert HTML to clean plain text."""
    soup = BeautifulSoup(html, 'lxml')
    
    # Remove unwanted elements
    for tag in soup.find_all(['script', 'style', 'noscript', 'nav', 'header', 'footer']):
        tag.decompose()
    
    # Remove elements with navigation/ad classes
    for tag in soup.find_all(class_=re.compile(r'(nav|menu|sidebar|ad|advertisement)', re.I)):
        tag.decompose()
    for tag in soup.find_all(id=re.compile(r'(nav|menu|sidebar|ad|advertisement)', re.I)):
        tag.decompose()
    
    # Extract text with structure
    text = _extract_text(soup)
    
    # Clean text
    text = clean_text(text)
    
    return text


def _extract_text(element, depth=0) -> str:
    """Recursively extract text with formatting."""
    # Skip DOCTYPE declarations
    if isinstance(element, Doctype):
        return ''
    
    if isinstance(element, NavigableString):
        return str(element)
    
    result = []
    tag_name = element.name if element.name else ''
    
    # Skip document root and structural containers
    if tag_name in ['[document]', 'html', 'body', 'head']:
        for child in element.children:
            result.append(_extract_text(child, depth))
        return ''.join(result)
    
    # Handle lists
    if tag_name == 'ul':
        for i, li in enumerate(element.find_all('li', recursive=False)):
            indent = '  ' * depth
            result.append(f"{indent}• {_extract_text(li, depth+1).strip()}\n")
        return ''.join(result)
    
    if tag_name == 'ol':
        for i, li in enumerate(element.find_all('li', recursive=False), 1):
            indent = '  ' * depth
            result.append(f"{indent}{i}. {_extract_text(li, depth+1).strip()}\n")
        return ''.join(result)
    
    # Handle tables
    if tag_name == 'table':
        for row in element.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if cells:
                row_text = ' | '.join(_extract_text(cell, depth).strip() for cell in cells)
                result.append(row_text + '\n')
        return ''.join(result) + '\n'
    
    # Handle preformatted text
    if tag_name in ['pre', 'code']:
        return element.get_text()
    
    # Process children
    for child in element.children:
        if isinstance(child, NavigableString):
            result.append(str(child))
        else:
            result.append(_extract_text(child, depth))
    
    text = ''.join(result)
    
    # Add spacing for block elements
    if tag_name in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'section', 'article']:
        text += '\n\n'
    elif tag_name == 'br':
        text += '\n'
    
    return text


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove zero-width characters
    text = text.replace('\u200b', '').replace('\ufeff', '')
    
    # Normalize unicode whitespace to ASCII space
    text = re.sub(r'[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]', ' ', text)
    
    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split('\n')]
    
    # Collapse multiple spaces within lines
    lines = [re.sub(r' +', ' ', line) for line in lines]
    
    # Collapse multiple blank lines to max 1 blank line
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        if not line.strip():
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append(line)
        else:
            blank_count = 0
            cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Ensure file ends with single newline
    text = text.rstrip() + '\n'
    
    return text
