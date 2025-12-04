"""
Printavo API client - GraphQL operations
"""
import datetime
import requests
from typing import List, Dict, Any, Optional

from config import PRINTAVO_API_ENDPOINT, make_headers
from data_processing import normalize_size


def graphql_post(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a GraphQL request to Printavo API"""
    payload = {"query": query, "variables": variables}
    resp = requests.post(PRINTAVO_API_ENDPOINT, json=payload, headers=make_headers(), timeout=30)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        body = resp.text
        raise RuntimeError(f"HTTP Error: {e}, response: {body}")
    data = resp.json()
    return data


def search_contacts(email: str) -> List[Dict[str, Any]]:
    """
    Search for contacts by email address.
    Returns list of matching contacts with id, name, and email.
    """
    query = """
    query ContactsSearch($query: String!) {
      contacts(query: $query) {
        data {
          id
          firstName
          lastName
          email
          companyName
        }
      }
    }
    """

    variables = {"query": email}
    data = graphql_post(query, variables)

    if "errors" in data:
        raise RuntimeError(f"ContactsSearch Error: {data['errors']}")

    contacts = data.get("data", {}).get("contacts", {}).get("data", [])
    return contacts


def create_quote(contact_id: str, note: Optional[str] = None) -> Dict[str, Any]:
    """Create a new quote for a contact"""
    mutation = """
    mutation QuoteCreate($input: QuoteCreateInput!) {
      quoteCreate(input: $input) {
        id
        url
        startAt
        dueAt
        customerDueAt
      }
    }
    """
    now = datetime.datetime.utcnow()
    start_at = now.isoformat() + "Z"
    due_at = (now + datetime.timedelta(days=7)).isoformat() + "Z"
    customer_due_at = (now + datetime.timedelta(days=14)).isoformat() + "Z"

    variables = {
        "input": {
            "contact": {"id": contact_id},
            "startAt": start_at,
            "dueAt": due_at,
            "customerDueAt": customer_due_at,
            "customerNote": note or ""
        }
    }

    data = graphql_post(mutation, variables)
    if "errors" in data:
        raise RuntimeError(f"QuoteCreate Error: {data['errors']}")
    return data["data"]["quoteCreate"]


def create_line_item_group(order_id: str, position: int = 1) -> Dict[str, Any]:
    """Create a line item group for an order"""
    mutation = """
    mutation LineItemGroupCreate($parentId: ID!, $input: LineItemGroupCreateInput!) {
      lineItemGroupCreate(parentId: $parentId, input: $input) {
        id
        position
      }
    }
    """

    input_payload = {}
    if position is not None:
        input_payload["position"] = position

    variables = {
        "parentId": order_id,
        "input": input_payload
    }

    data = graphql_post(mutation, variables)
    if "errors" in data:
        raise RuntimeError(f"LineItemGroupCreate error: {data['errors']}")

    return data["data"]["lineItemGroupCreate"]


def create_line_items_batch(group_id: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create multiple line items in a single batch request.
    Handles consolidated items with multiple sizes.
    """
    mutation = """
    mutation LineItemCreates($inputs: [LineItemCreatesInput!]!) {
      lineItemCreates(inputs: $inputs) {
        id
        itemNumber
        items
        color
      }
    }
    """

    print(f"\n=== DEBUG: create_line_items_batch called with {len(items)} items ===")
    for i, item in enumerate(items):
        print(f"Item {i}: {item.get('item_num')} - {item.get('color')}")
        print(f"  Keys: {list(item.keys())}")
        if 'sizes' in item:
            print(f"  ✓ HAS sizes array: {item['sizes']}")
        else:
            print(f"  ✗ NO sizes array")

    batch_inputs = []
    for idx, item in enumerate(items):
        # Debug: Check what we received
        print(f"DEBUG: Processing item {idx}: {item.get('item_num')}")
        print(f"  Has 'sizes' key: {'sizes' in item}")
        if 'sizes' in item:
            print(f"  Sizes array: {item['sizes']}")
        print(f"  Has 'size' key: {'size' in item}")

        # Build the inner input object - NO quantity field in input!
        item_input = {
            "itemNumber": item["item_num"],
            "color": item["color"],
            "price": 0.0,
            "position": idx + 1  # Required field!
        }

        # Add description if available
        if item.get("description"):
            item_input["description"] = item["description"]

        # Handle consolidated items with multiple sizes
        if "sizes" in item and item["sizes"]:
            # Consolidated format: sizes is a list of {size, quantity} dicts
            sizes_array = []
            for size_info in item["sizes"]:
                if size_info.get("size"):  # Only add if size is specified
                    size_enum = normalize_size(size_info["size"])
                    sizes_array.append({"size": size_enum, "count": size_info["quantity"]})
                else:
                    # No size specified, but still add the quantity
                    sizes_array.append({"size": "size_other", "count": size_info["quantity"]})

            item_input["sizes"] = sizes_array
            print(f"  ✓ Using CONSOLIDATED format with {len(sizes_array)} sizes: {sizes_array}")
        elif item.get("size"):
            # Old format: single size and quantity
            size_enum = normalize_size(item["size"])
            item_input["sizes"] = [{"size": size_enum, "count": item["quantity"]}]
            print(f"  ✓ Using OLD format with single size")

        # Wrap in the structure the API expects
        batch_inputs.append({
            "lineItemGroupId": group_id,
            "input": item_input
        })

    variables = {"inputs": batch_inputs}
    data = graphql_post(mutation, variables)

    if "errors" in data:
        raise RuntimeError({"batch_errors": data["errors"], "response": data})

    return data["data"]["lineItemCreates"]


def create_line_item_single(line_item_group_id: str, it: Dict[str, Any], position: int = 1) -> Dict[str, Any]:
    """
    Create a single line item.
    Handles consolidated items with multiple sizes.
    """
    mutation = """
    mutation LineItemCreate($lineItemGroupId: ID!, $input: LineItemCreateInput!) {
      lineItemCreate(lineItemGroupId: $lineItemGroupId, input: $input) {
        id
        itemNumber
        items
        color
      }
    }
    """

    # Build the input object - NO quantity field in input!
    item_input = {
        "itemNumber": it["item_num"],
        "color": it.get("color") or "",
        "price": 0.0,
        "position": position  # Required!
    }

    # Add description if available
    if it.get("description"):
        item_input["description"] = it["description"]

    # Handle consolidated items with multiple sizes
    if "sizes" in it and it["sizes"]:
        # Consolidated format: sizes is a list of {size, quantity} dicts
        sizes_array = []
        for size_info in it["sizes"]:
            if size_info["size"]:  # Only add if size is specified
                size_enum = normalize_size(size_info["size"])
                sizes_array.append({"size": size_enum, "count": size_info["quantity"]})
        if sizes_array:
            item_input["sizes"] = sizes_array
    elif it.get("size"):
        # Old format: single size and quantity
        size_enum = normalize_size(it["size"])
        item_input["sizes"] = [{"size": size_enum, "count": it["quantity"]}]

    variables = {
        "lineItemGroupId": line_item_group_id,
        "input": item_input
    }

    data = graphql_post(mutation, variables)
    if "errors" in data:
        raise RuntimeError(f"LineItemCreate error: {data['errors']}")

    return data["data"]["lineItemCreate"]