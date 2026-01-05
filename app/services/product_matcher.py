from typing import Dict, List, Any
import json
from app.services.embedding_service import get_openai_client

async def extract_product_attributes(product_text: str) -> Dict[str, Any]:
    """
    Extract product attributes using OpenAI.
    """
    client = get_openai_client()
    prompt = f"""
    Extract the following attributes from the product description: brand, item type, size, quantity, packaging, target users (school, grade), purpose.
    Return only a valid JSON object with these keys. If an attribute is not mentioned, use null or empty string.

    Product: {product_text}

    JSON format:
    {{
        "brand": "string or null",
        "item_type": "string or null",
        "size": "string or null",
        "quantity": "string or null",
        "packaging": "string or null",
        "target_users": "string or null",
        "purpose": "string or null"
    }}
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        # Remove markdown if present
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        attributes = json.loads(content)
        return attributes
    except Exception as e:
        print(f"Error extracting attributes: {e}")
        return {
            "brand": None,
            "item_type": None,
            "size": None,
            "quantity": None,
            "packaging": None,
            "target_users": None,
            "purpose": None
        }

def compare_attributes(attr1: Dict[str, Any], attr2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two attribute dictionaries and return confidence label and similarity score.
    """
    keys = ["brand", "item_type", "size", "quantity", "packaging", "target_users", "purpose"]
    match_attributes = []
    difference_attributes = []
    matches = 0
    total = len(keys)

    for key in keys:
        val1 = attr1.get(key)
        val2 = attr2.get(key)
        if val1 and val2 and str(val1).lower() == str(val2).lower():
            match_attributes.append(f"{key.replace('_', ' ')} match")
            matches += 1
        elif val1 != val2:
            difference_attributes.append(f"{key.replace('_', ' ')} difference")

    similarity_score = matches / total if total > 0 else 0.0

    # Determine confidence label based on similarity score
    if similarity_score > 0.90:
        confidence_label = "High Confidence Duplicate"
    elif 0.70 <= similarity_score <= 0.89:
        confidence_label = "Moderate Similarity - Review Required"
    else:
        confidence_label = "Low Similarity - New Product"

    return {
        "confidence_label": confidence_label,
        "similarity_score": similarity_score
    }

async def match_products(new_product_text: str, existing_product_text: str) -> Dict[str, Any]:
    """
    Match two products based on their text descriptions.
    """
    attr1 = await extract_product_attributes(new_product_text)
    attr2 = await extract_product_attributes(existing_product_text)
    result = compare_attributes(attr1, attr2)
    return {"confidence_label": result["confidence_label"]}

async def find_top_matches(new_product_text: str, existing_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Find top 3 matches for a new product against existing catalog products.
    """
    attr_new = await extract_product_attributes(new_product_text)
    matches = []

    for product in existing_products:
        existing_text = f"{product['name']} {product.get('description', '')}"
        attr_existing = await extract_product_attributes(existing_text)
        comparison = compare_attributes(attr_new, attr_existing)
        similarity_score = comparison['similarity_score']

        matches.append({
            "existing_product_id": product['id'],
            "name": product['name'],
            "similarity_score": similarity_score
        })

    # Sort by similarity score descending and take top 3
    matches.sort(key=lambda x: x['similarity_score'], reverse=True)
    return matches[:3]

async def recommend_merge(new_product_text: str, matched_product_text: str) -> Dict[str, Any]:
    """
    AI Product Merge Advisor for ICCS.
    Recommend if the new product should merge into the matched catalog item.
    """
    attr_new = await extract_product_attributes(new_product_text)
    attr_matched = await extract_product_attributes(matched_product_text)
    comparison = compare_attributes(attr_new, attr_matched)
    similarity_score = comparison['similarity_score']

    # Determine merge recommendation based on similarity
    if similarity_score > 0.90:
        merge_recommendation = "merge"
        merge_reason = "High similarity indicates these are the same product"
        fields_to_copy = ["description", "seo_keywords", "brand", "warranty"]
    elif 0.70 <= similarity_score <= 0.89:
        merge_recommendation = "keep_separate"
        merge_reason = "Moderate similarity suggests they are related but distinct products"
        fields_to_copy = ["brand", "category"]
    else:
        merge_recommendation = "keep_separate"
        merge_reason = "Low similarity indicates they are different products"
        fields_to_copy = []

    return {
        "merge_recommendation": merge_recommendation,
        "merge_reason": merge_reason,
        "fields_to_copy": fields_to_copy
    }
