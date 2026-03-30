import re
from datetime import datetime

# Pre-compile experience patterns so they aren't built on every single resume
EXP_PATTERNS = [
    re.compile(r'(\d+)(?:\+)?\s*(?:yrs|years?)(?:\s+of)?\s+experience'),
    re.compile(r'experience.*?(?:of)?\s*(\d+)(?:\+)?\s*(?:yrs|years?)'),
    re.compile(r'(\d+)(?:\+)?\s*(?:yrs|years?)')
]

DATE_RANGE_PATTERN = re.compile(
    r'\b(?P<start_month>january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|\d{1,2})[\s/\-]+'
    r'(?P<start_year>(?:19|20)\d{2})\s*'
    r'(?:-|to|till|until|–|—|—)\s*'
    r'(?P<end_month>january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|present|current|today|now|\d{1,2})?[\s/\-]*'
    r'(?P<end_year>(?:19|20)\d{2})?\b',
    re.IGNORECASE
)

def _parse_date(month_str, year_str):
    if not month_str or not year_str:
        return None
    month_str = month_str.lower()
    
    if month_str.isdigit():
        month_int = int(month_str)
        if 1 <= month_int <= 12:
            return datetime(int(year_str), month_int, 1)
        return None
        
    if month_str == 'sept':
        month_str = 'sep'
    month_str = month_str[:3]
    try:
        return datetime.strptime(f"{month_str} {year_str}", "%b %Y")
    except ValueError:
        return None

def extract_experience(resume_text):
    """
    Attempts to extract the years of experience from the resume text using common patterns
    and date ranges.
    """
    if not resume_text:
        return "Unknown"
        
    text_lower = resume_text.lower()
    
    # Check date ranges first as they represent accumulated duration
    intervals = []
    matches = DATE_RANGE_PATTERN.finditer(text_lower)
    for match in matches:
        start_m = match.group('start_month')
        start_y = match.group('start_year')
        end_m = match.group('end_month')
        end_y = match.group('end_year')
        
        start_date = _parse_date(start_m, start_y)
        if not start_date:
            continue
            
        if end_m and end_m.lower() in ['present', 'current', 'today', 'now']:
            end_date = datetime.now()
        elif end_m and end_y:
            end_date = _parse_date(end_m, end_y)
        else:
            continue
            
        if not end_date or end_date < start_date:
            continue
            
        start_months = start_date.year * 12 + start_date.month
        end_months = (end_date.year * 12 + end_date.month)
            
        intervals.append((start_months, end_months))
        
    total_months = 0
    if intervals:
        # Calculate total career span from the earliest start to the latest end
        min_start = min(start for start, end in intervals)
        max_end = max(end for start, end in intervals)
        
        total_months = max_end - min_start
        if total_months == 0:
            total_months = 1
        
    if total_months > 0:
        years = total_months // 12
        months = total_months % 12
        
        parts = []
        if years > 0:
            parts.append(f"{years} Year{'s' if years > 1 else ''}")
        if months > 0:
            parts.append(f"{months} Month{'s' if months > 1 else ''}")
            
        if parts:
            return " ".join(parts)
        
    # Check for direct mentions first
    for pattern in EXP_PATTERNS:
        match = pattern.search(text_lower)
        if match:
            val = match.group(1)
            # Sanity check: years shouldn't be massive like 100+
            if val.isdigit() and int(val) < 50:
                return f"{val} Years"
                
    return "Not Specified"

def create_keyword_pattern(keywords):
    """
    Creates a single, optimized regex pattern for all keywords.
    Properly handles word boundaries for keywords with special characters (like C++, .NET).
    """
    if not keywords:
        return None
        
    # Sort keywords by length descending so longer phrases match first (e.g. "React Native" before "React")
    sorted_kws = sorted(keywords, key=len, reverse=True)
    parts = []
    
    for kw in sorted_kws:
        escaped = re.escape(kw.lower())
        # If it starts with an alphanumeric character, use \b. Otherwise, use a negative lookbehind.
        start_bound = r'\b' if kw[0].isalnum() else r'(?<!\w)'
        # If it ends with an alphanumeric character, use \b. Otherwise, use a negative lookahead.
        end_bound = r'\b' if kw[-1].isalnum() else r'(?!\w)'
        
        parts.append(f'{start_bound}{escaped}{end_bound}')
        
    # Combine all parts with OR operator
    return re.compile(r'(' + '|'.join(parts) + r')', re.IGNORECASE)

def calculate_match_score(resume_text, keywords):
    """
    Calculates a simple matching score based on the presence of predefined keywords
    in the resume text.
    """
    if not resume_text or not keywords:
        return 0, [], "Unknown"

    text_lower = resume_text.lower()
    matched_keywords = []
    
    # Create the unified regex pattern
    pattern = create_keyword_pattern(keywords)
    
    if pattern:
        # Find all matches in the text
        all_matches = pattern.findall(text_lower)
        # Unique the matches, maintaining case from original keywords list
        # We map lowercased found matches back to the original casing
        kw_map = {k.lower(): k for k in keywords}
        matched_set = set(m.lower() for m in all_matches)
        
        for matched_lower in matched_set:
            if matched_lower in kw_map:
                matched_keywords.append(kw_map[matched_lower])
            
    # Calculate percentage
    score = (len(matched_keywords) / len(keywords)) * 100 if keywords else 0
    experience = extract_experience(resume_text)
    
    return round(score, 2), matched_keywords, experience
