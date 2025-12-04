"""
CSV/XLSX data processing, size normalization, and product lookup
Supports both SSActivewear and Sanmar vendors
ENHANCED: Handles duplicates, tall sizes, spelled-out sizes, and XLSX files
"""
import csv
import re
import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Any, Optional, Callable, Union, Tuple
from collections import defaultdict

import config

try:
    import openpyxl
    XLSX_SUPPORT = True
except ImportError:
    XLSX_SUPPORT = False

# Global cache for SSActivewear catalog
_ssactivewear_cache = None
_ssactivewear_cache_attempted = False

# Global cache for Sanmar products (style_number -> product_data)
_sanmar_cache: Dict[str, Dict[str, Any]] = {}
_sanmar_client = None  # Will be initialized on first use


# ============================================================================
# SIZE MAPPING AND NORMALIZATION
# ============================================================================

# Expanded size mapping with spelled-out sizes
SIZE_MAP_NORMALIZE = {
    # Spelled-out sizes (case-insensitive)
    "SMALL": "S",
    "MEDIUM": "M",
    "LARGE": "L",
    "EXTRA LARGE": "XL",
    "EXTRALARGE": "XL",

    # Youth sizes
    "YXS": "YXS", "Y-XS": "YXS",
    "YS": "YS", "Y-S": "YS",
    "YM": "YM", "Y-M": "YM",
    "YL": "YL", "Y-L": "YL",
    "YXL": "YXL", "Y-XL": "YXL",

    # Adult sizes
    "XS": "XS",
    "S": "S",
    "M": "M",
    "L": "L",
    "XL": "XL",
    "2XL": "2XL", "XXL": "2XL",
    "3XL": "3XL", "XXXL": "3XL",
    "4XL": "4XL",
    "5XL": "5XL",
    "6XL": "6XL",

    # Baby/Toddler sizes
    "6M": "6M",
    "12M": "12M",
    "18M": "18M",
    "24M": "24M",
    "2T": "2T",
    "3T": "3T",
    "4T": "4T",
    "5T": "5T",
}

# Printavo API enum mapping
SIZE_MAP_ENUM = {
    "YXS": "size_yxs",
    "YS": "size_ys",
    "YM": "size_ym",
    "YL": "size_yl",
    "YXL": "size_yxl",
    "XS": "size_xs",
    "S": "size_s",
    "M": "size_m",
    "L": "size_l",
    "XL": "size_xl",
    "2XL": "size_2xl",
    "3XL": "size_3xl",
    "4XL": "size_4xl",
    "5XL": "size_5xl",
    "6XL": "size_6xl",
    "6M": "size_6m",
    "12M": "size_12m",
    "18M": "size_18m",
    "24M": "size_24m",
    "2T": "size_2t",
    "3T": "size_3t",
    "4T": "size_4t",
    "5T": "size_5t",
}


def parse_size_field(size_str: str) -> str:
    """
    Parse size field, handling:
    - Spelled-out sizes (Small, Medium, Large)
    - Extra data after size (e.g., "2XL ($3.50)")
    - Whitespace and case variations

    Returns the normalized size code (e.g., "M", "2XL", "LT")
    """
    if not size_str:
        return ""

    # Extract first unbroken string (ignore anything after whitespace/parentheses)
    size_clean = re.split(r'[\s\(]', size_str.strip())[0].upper()

    # Check if it's a spelled-out size
    if size_clean in SIZE_MAP_NORMALIZE:
        return SIZE_MAP_NORMALIZE[size_clean]

    # Otherwise return as-is (will handle Tall sizes separately)
    return size_clean


def is_tall_size(size: str) -> bool:
    """Check if size ends with 'T' and is a tall size (not toddler)"""
    if not size or len(size) < 2:
        return False

    # Toddler sizes don't count as tall
    if size in ["2T", "3T", "4T", "5T"]:
        return False

    return size.endswith("T")


def get_base_size(tall_size: str) -> str:
    """Convert tall size to base size (LT -> L, XLT -> XL)"""
    if is_tall_size(tall_size):
        return tall_size[:-1]  # Remove trailing 'T'
    return tall_size


def normalize_size(size_str: str) -> str:
    """
    Convert human-readable sizes to Printavo's enum format.
    e.g., "L" -> "size_l", "XL" -> "size_xl", "2XL" -> "size_2xl"
    """
    size_upper = size_str.strip().upper()

    # First normalize the size
    if size_upper in SIZE_MAP_NORMALIZE:
        size_upper = SIZE_MAP_NORMALIZE[size_upper]

    # Then convert to enum
    return SIZE_MAP_ENUM.get(size_upper, "size_other")


# ============================================================================
# FILE READING
# ============================================================================

def read_file_raw(filepath: str) -> Tuple[List[str], List[List[str]]]:
    """
    Read CSV or XLSX file and return raw headers and rows.
    Returns: (headers, rows) where rows are lists of cell values
    """
    if filepath.lower().endswith('.xlsx'):
        if not XLSX_SUPPORT:
            raise RuntimeError("XLSX support requires openpyxl. Install: pip install openpyxl")

        # Read XLSX
        wb = openpyxl.load_workbook(filepath, data_only=True)
        ws = wb.active

        rows_iter = ws.iter_rows(values_only=True)
        headers = [str(h).strip() if h else "" for h in next(rows_iter)]
        rows = []
        for row in rows_iter:
            rows.append([str(cell).strip() if cell is not None else "" for cell in row])

        return headers, rows

    else:
        # Read CSV
        with open(filepath, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = [h.strip() for h in next(reader)]
            rows = [[cell.strip() for cell in row] for row in reader]

        return headers, rows


# ============================================================================
# DATA PARSING AND VALIDATION
# ============================================================================

def detect_columns(headers: List[str]) -> Dict[str, Optional[int]]:
    """
    Auto-detect which columns contain qty, size, item_num, color.
    Returns dict mapping field names to column indices (or None if not found).
    """
    headers_lower = [h.lower() for h in headers]

    def find_col(*names):
        for name in names:
            if name.lower() in headers_lower:
                return headers_lower.index(name.lower())
        return None

    return {
        "qty": find_col("qty", "quantity", "count"),
        "size": find_col("size"),
        "item_num": find_col("item num", "item_num", "itemnumber", "item number", "item", "style", "style number"),
        "color": find_col("color", "colour"),
    }


def parse_rows_to_items(headers: List[str], rows: List[List[str]],
                       column_map: Dict[str, Optional[int]],
                       log_callback: Optional[Callable] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Parse raw rows into item dictionaries using column mapping.
    Handles size parsing and validation.

    Returns: (items, warnings)
    """
    items = []
    warnings = []

    qty_idx = column_map.get("qty")
    size_idx = column_map.get("size")
    item_idx = column_map.get("item_num")
    color_idx = column_map.get("color")

    if qty_idx is None or item_idx is None:
        raise ValueError("Required columns not found: qty and item_num are mandatory")

    for row_num, row in enumerate(rows, start=2):  # Start at 2 (1 is header)
        if not row or all(cell == "" for cell in row):
            continue  # Skip empty rows

        # Parse quantity
        try:
            qty_str = row[qty_idx] if qty_idx < len(row) else ""
            if not qty_str:
                quantity = 0
            else:
                # Handle both int and float (XLSX often returns floats like "1.0")
                quantity = int(float(qty_str))
        except (ValueError, TypeError):
            warnings.append(f"Row {row_num}: Invalid quantity '{row[qty_idx]}' - skipped")
            continue

        if quantity <= 0:
            warnings.append(f"Row {row_num}: Zero/negative quantity - skipped")
            continue

        # Parse size
        size_raw = row[size_idx] if size_idx is not None and size_idx < len(row) else ""
        size = parse_size_field(size_raw)

        # Get item number and color
        item_num_raw = row[item_idx] if item_idx < len(row) else ""
        color_raw = row[color_idx] if color_idx is not None and color_idx < len(row) else ""

        # Fix XLSX numeric style numbers (112.0 -> 112)
        item_num = item_num_raw.strip()
        if item_num and '.' in item_num:
            try:
                # If it's a number like "112.0", convert to "112"
                float_val = float(item_num)
                if float_val == int(float_val):  # Check if it's a whole number
                    item_num = str(int(float_val))
            except ValueError:
                pass  # Not a number, keep as-is

        color = color_raw.strip()

        if not item_num:
            warnings.append(f"Row {row_num}: Missing item number - skipped")
            continue

        items.append({
            "quantity": quantity,
            "size": size,
            "item_num": item_num.strip(),
            "color": color.strip(),
            "description": "",
            "_row_num": row_num,
            "_size_raw": size_raw,
        })

    return items, warnings


def process_tall_sizes(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process tall sizes: for each item with size ending in 'T' (except toddler sizes),
    create a duplicate with base size and " - Tall" appended to description.
    """
    processed = []

    for item in items:
        size = item["size"]

        if is_tall_size(size):
            # Create new item with base size and " - Tall" description
            tall_item = item.copy()
            tall_item["size"] = get_base_size(size)
            tall_item["description"] = (item.get("description") or "") + " - Tall"
            tall_item["_is_tall"] = True
            tall_item["_original_size"] = size
            processed.append(tall_item)
        else:
            # Keep non-tall items as-is
            processed.append(item)

    return processed


def sum_duplicates(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sum quantities for items with identical item_num, color, and size.
    This fixes the bug where duplicate rows would overwrite instead of sum.
    """
    # Group by (item_num, color, size)
    grouped = defaultdict(lambda: {"quantity": 0, "items": []})

    for item in items:
        key = (
            item["item_num"].strip().upper(),
            item["color"].strip().upper(),
            item["size"].strip().upper()
        )
        grouped[key]["quantity"] += item["quantity"]
        grouped[key]["items"].append(item)

    # Build summed items
    summed = []
    for key, group in grouped.items():
        # Use first item as template
        base_item = group["items"][0].copy()
        base_item["quantity"] = group["quantity"]

        # Track if this was a sum of multiple rows
        if len(group["items"]) > 1:
            base_item["_summed_from"] = [item["_row_num"] for item in group["items"]]

        summed.append(base_item)

    return summed


def consolidate_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Consolidate items by (item_num, color), combining multiple sizes.
    This creates the final structure needed for batch API calls.
    """
    grouped = {}

    for item in items:
        key = (item['item_num'].strip().upper(), item['color'].strip().upper())

        if key not in grouped:
            grouped[key] = {
                'item_num': item['item_num'],
                'color': item['color'],
                'description': item.get('description', ''),
                'sizes': [],
                'total_quantity': 0
            }

        # Add this size/quantity to the group
        grouped[key]['sizes'].append({
            'size': item['size'],
            'quantity': item['quantity']
        })
        grouped[key]['total_quantity'] += item['quantity']

    return list(grouped.values())


# ============================================================================
# SSActivewear Functions
# ============================================================================

def _load_ssactivewear_catalog(log_callback: Optional[Callable] = None) -> bool:
    """Load all styles from SSActivewear API into memory cache."""
    global _ssactivewear_cache, _ssactivewear_cache_attempted

    if _ssactivewear_cache_attempted:
        return _ssactivewear_cache is not None

    _ssactivewear_cache_attempted = True

    if not config.SSACTIVEWEAR_ACCOUNT or not config.SSACTIVEWEAR_API_KEY:
        return False

    try:
        url = f"{config.SSACTIVEWEAR_API_ENDPOINT}/styles"

        if log_callback:
            log_callback("  → Loading SSActivewear catalog (one-time operation)...")

        response = requests.get(
            url,
            auth=HTTPBasicAuth(config.SSACTIVEWEAR_ACCOUNT, config.SSACTIVEWEAR_API_KEY),
            timeout=30
        )

        if response.status_code == 401:
            if log_callback:
                log_callback("  ✗ Authentication failed! Check your credentials.")
            return False

        if response.status_code != 200:
            if log_callback:
                log_callback(f"  ✗ API error {response.status_code}")
            return False

        _ssactivewear_cache = response.json()

        if log_callback:
            log_callback(f"  ✓ Loaded {len(_ssactivewear_cache)} styles into cache\n")

        return True

    except Exception as e:
        if log_callback:
            log_callback(f"  ✗ Error loading catalog: {str(e)}")
        return False


def lookup_ssactivewear_description(style_number: str, log_callback: Optional[Callable] = None) -> Optional[str]:
    """Look up product description from SSActivewear API."""
    if not config.SSACTIVEWEAR_ACCOUNT or not config.SSACTIVEWEAR_API_KEY:
        return None

    if not _load_ssactivewear_catalog(log_callback):
        return None

    if not _ssactivewear_cache:
        return None

    try:
        if log_callback:
            log_callback(f"  → Searching SSActivewear for: {style_number}")

        style_upper = style_number.strip().upper()
        matches = []

        for style in _ssactivewear_cache:
            style_name = (style.get('styleName') or '').strip().upper()
            unique_name = (style.get('uniqueStyleName') or '').strip().upper()

            if style_name == style_upper or unique_name == style_upper:
                matches.append(style)

        if not matches:
            if log_callback:
                log_callback(f"  ✗ Style '{style_number}' not found in SSActivewear catalog\n")
            return None

        style = matches[0]
        brand = style.get('brandName', '')
        title = style.get('title', '')

        if log_callback:
            if len(matches) > 1:
                log_callback(f"  ℹ Found {len(matches)} matches, using: {brand} - {title}")
            log_callback(f"  ✓ Found: {brand} {title}\n")

        if brand and title:
            return f"{brand} {title}"
        elif title:
            return title
        elif brand:
            return brand
        else:
            return None

    except Exception as e:
        if log_callback:
            log_callback(f"  ✗ Error: {str(e)}\n")
        return None


# ============================================================================
# Sanmar Functions
# ============================================================================

def _get_sanmar_client():
    """Lazy-initialize Sanmar SOAP client"""
    global _sanmar_client

    if _sanmar_client is not None:
        return _sanmar_client

    if not config.SANMAR_CUSTOMER_NUMBER or not config.SANMAR_USERNAME or not config.SANMAR_PASSWORD:
        return None

    try:
        from zeep import Client
        wsdl_url = config.SANMAR_PRODUCTION_WSDL if config.SANMAR_USE_PRODUCTION else config.SANMAR_STAGE_WSDL
        _sanmar_client = Client(wsdl_url)
        return _sanmar_client
    except ImportError:
        return None
    except Exception:
        return None


def lookup_sanmar_description(style_number: str, log_callback: Optional[Callable] = None) -> Optional[str]:
    """Look up product description from Sanmar SOAP API."""
    if not config.SANMAR_CUSTOMER_NUMBER or not config.SANMAR_USERNAME or not config.SANMAR_PASSWORD:
        return None

    style_upper = style_number.strip().upper()
    if style_upper in _sanmar_cache:
        cached_data = _sanmar_cache[style_upper]
        if log_callback:
            log_callback(f"  ✓ Found in cache: {cached_data.get('title', '')}\n")
        return cached_data.get('description')

    client = _get_sanmar_client()
    if not client:
        if log_callback:
            log_callback("  ✗ Sanmar SOAP client not available (install zeep: pip install zeep)\n")
        return None

    try:
        if log_callback:
            log_callback(f"  → Searching Sanmar for: {style_number}")

        product_request = {
            'style': style_number.strip(),
            'color': '',
            'size': ''
        }

        auth = {
            'sanMarCustomerNumber': str(config.SANMAR_CUSTOMER_NUMBER),
            'sanMarUserName': str(config.SANMAR_USERNAME),
            'sanMarUserPassword': str(config.SANMAR_PASSWORD),
            'senderId': '',
            'senderPassword': ''
        }

        response = client.service.getProductInfoByStyleColorSize(
            arg0=product_request,
            arg1=auth
        )

        if hasattr(response, 'errorOccured') and response.errorOccured:
            if log_callback:
                error_msg = getattr(response, 'message', 'Unknown error')
                log_callback(f"  ✗ Sanmar API error: {error_msg}\n")
            return None

        if not hasattr(response, 'listResponse') or not response.listResponse:
            if log_callback:
                log_callback(f"  ✗ Style '{style_number}' not found in Sanmar catalog\n")
            return None

        item = response.listResponse[0]

        if hasattr(item, 'productBasicInfo'):
            basic = item.productBasicInfo
            title = getattr(basic, 'productTitle', '')
            description = getattr(basic, 'productDescription', '')
            brand = getattr(basic, 'brandName', '')

            product_data = {
                'title': title,
                'description': description,
                'brand': brand
            }

            _sanmar_cache[style_upper] = product_data

            if log_callback:
                log_callback(f"  ✓ Found: {title}\n")

            if brand and title:
                return f"{brand} - {title}"
            elif title:
                return title
            else:
                return None
        else:
            if log_callback:
                log_callback(f"  ✗ No product info in response\n")
            return None

    except Exception as e:
        if log_callback:
            log_callback(f"  ✗ Sanmar API error: {str(e)}\n")
        return None


# ============================================================================
# Unified Lookup Functions
# ============================================================================

def lookup_product_description(style_number: str, vendor: str = "auto",
                               log_callback: Optional[Callable] = None) -> Optional[str]:
    """Look up product description from vendor APIs."""
    if vendor == "ssactivewear":
        return lookup_ssactivewear_description(style_number, log_callback)
    elif vendor == "sanmar":
        return lookup_sanmar_description(style_number, log_callback)
    elif vendor == "auto":
        if config.SSACTIVEWEAR_ACCOUNT and config.SSACTIVEWEAR_API_KEY:
            desc = lookup_ssactivewear_description(style_number, log_callback)
            if desc:
                return desc

        if config.SANMAR_CUSTOMER_NUMBER and config.SANMAR_USERNAME and config.SANMAR_PASSWORD:
            desc = lookup_sanmar_description(style_number, log_callback)
            if desc:
                return desc

        return None
    else:
        if log_callback:
            log_callback(f"⚠ Unknown vendor: {vendor}")
        return None


def enrich_items_with_descriptions(items: List[Dict[str, Any]], vendor: str = "auto",
                                   log_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
    """Enrich items with product descriptions by looking up style numbers."""
    has_ssactivewear = bool(config.SSACTIVEWEAR_ACCOUNT and config.SSACTIVEWEAR_API_KEY)
    has_sanmar = bool(config.SANMAR_CUSTOMER_NUMBER and config.SANMAR_USERNAME and config.SANMAR_PASSWORD)

    if not has_ssactivewear and not has_sanmar:
        if log_callback:
            log_callback("\n⚠ No vendor credentials configured.")
            log_callback("Product descriptions will not be auto-filled.")
            log_callback("You can add credentials in Settings to enable this feature.\n")
        return items

    if vendor == "auto":
        vendor_list = []
        if has_ssactivewear:
            vendor_list.append("SSActivewear")
        if has_sanmar:
            vendor_list.append("Sanmar")
        vendor_str = " and ".join(vendor_list)
    elif vendor == "ssactivewear":
        vendor_str = "SSActivewear"
        if not has_ssactivewear:
            if log_callback:
                log_callback("\n⚠ SSActivewear credentials not configured.\n")
            return items
    elif vendor == "sanmar":
        vendor_str = "Sanmar"
        if not has_sanmar:
            if log_callback:
                log_callback("\n⚠ Sanmar credentials not configured.\n")
            return items
    else:
        if log_callback:
            log_callback(f"\n⚠ Unknown vendor: {vendor}\n")
        return items

    description_cache: Dict[str, Optional[str]] = {}
    unique_styles = set(item.get('item_num', '').strip() for item in items if item.get('item_num'))

    if log_callback:
        log_callback(f"\nLooking up descriptions from {vendor_str} for {len(unique_styles)} unique style number(s)...")

    for style_num in unique_styles:
        if style_num and style_num not in description_cache:
            description = lookup_product_description(style_num, vendor, log_callback)
            description_cache[style_num] = description

    enriched_count = 0
    for item in items:
        style_num = item.get('item_num', '').strip()
        if style_num in description_cache:
            description = description_cache[style_num]
            if description:
                # Preserve " - Tall" suffix if it exists
                existing_desc = item.get('description', '')
                if existing_desc.endswith(" - Tall"):
                    item['description'] = description + " - Tall"
                else:
                    item['description'] = description
                enriched_count += 1
            else:
                if not item.get('description'):
                    item['description'] = ""
        else:
            if not item.get('description'):
                item['description'] = ""

    if log_callback:
        log_callback(f"\n✓ Successfully enriched {enriched_count}/{len(items)} items with descriptions.\n")

    return items


# ============================================================================
# MAIN READ FUNCTION
# ============================================================================

def read_csv(filepath: str, vendor: str = "auto",
            log_callback: Optional[Callable[[str], None]] = None) -> List[Dict[str, Any]]:
    """
    Read CSV/XLSX and normalize fields with enhanced processing.

    NEW FEATURES:
    - XLSX file support
    - Tall size handling (LT -> L with " - Tall")
    - Spelled-out size normalization (Small -> S)
    - Size data extraction (2XL ($3.50) -> 2XL)
    - Duplicate summing (fixed bug)
    - Flexible column ordering (already supported)
    - Extra columns ignored (already supported)

    Returns consolidated items ready for API posting.
    """
    if log_callback:
        log_callback(f"Reading file: {filepath}")

    # Read raw file
    headers, rows = read_file_raw(filepath)

    # Detect columns
    column_map = detect_columns(headers)

    if log_callback:
        log_callback(f"Detected columns: {column_map}")

    # Parse rows to items
    items, warnings = parse_rows_to_items(headers, rows, column_map, log_callback)

    # Show warnings
    if warnings and log_callback:
        log_callback("\n⚠ Warnings during processing:")
        for warning in warnings:
            log_callback(f"  {warning}")
        log_callback("")

    if log_callback:
        log_callback(f"✓ Loaded {len(rows)} rows, parsed {len(items)} valid items")

    # Process tall sizes (must happen BEFORE summing duplicates)
    items = process_tall_sizes(items)
    if log_callback:
        log_callback(f"✓ Processed tall sizes ({len(items)} items after expansion)")

    # Sum duplicate items
    items = sum_duplicates(items)
    if log_callback:
        log_callback(f"✓ Summed duplicates ({len(items)} unique items)")

    # Consolidate for API
    consolidated = consolidate_items(items)
    if log_callback:
        log_callback(f"✓ Consolidated to {len(consolidated)} unique style/color combinations\n")

    # Enrich with descriptions
    consolidated = enrich_items_with_descriptions(consolidated, vendor, log_callback)

    return consolidated