"""REST API for the AI Ingredient Safety Analyzer.

Provides endpoints for mobile app integration.
"""

import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import google.genai as genai

import time
import uuid

from config.logging_config import setup_logging
from config.settings import get_settings
from graph import run_analysis

# Get settings
settings = get_settings()

# Initialize logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="AI Ingredient Safety Analyzer API",
    description="API for analyzing food and cosmetic ingredient safety",
    version="1.0.0",
)

# Enable CORS for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    """Request model for ingredient analysis."""
    product_name: Optional[str] = "Unknown Product"
    ingredients: str
    allergies: list[str] = []
    skin_type: str = "normal"
    expertise: str = "beginner"


class IngredientDetail(BaseModel):
    """Detailed ingredient information for mobile display."""
    name: str
    purpose: str
    safety_score: int  # 1-10
    risk_level: str  # low, medium, high
    concerns: str
    recommendation: str
    origin: str  # Natural, Synthetic, Semi-synthetic
    category: str  # Food, Cosmetics, Both
    allergy_risk: str  # High, Low
    is_allergen_match: bool
    alternatives: list[str]


class AnalysisResponse(BaseModel):
    """Response model for ingredient analysis."""
    success: bool
    product_name: str
    overall_risk: str
    average_safety_score: int
    summary: str
    allergen_warnings: list[str]
    ingredients: list[IngredientDetail]  # Structured ingredient data
    execution_time: float
    error: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "AI Ingredient Safety Analyzer API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


class OCRRequest(BaseModel):
    """Request model for OCR text extraction."""
    image: str  # Base64 encoded image


class OCRResponse(BaseModel):
    """Response model for OCR text extraction."""
    success: bool
    text: str
    error: Optional[str] = None


def _translate_ingredients_to_english(client: genai.Client, ingredients_text: str) -> str:
    """Translate non-English ingredient text to English.

    Args:
        client: Gemini client instance.
        ingredients_text: Ingredient text that may be in a non-English language.

    Returns:
        English translated ingredient list.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""You are an expert translator specializing in cosmetic and food ingredient terminology.

TASK: Translate the following ingredient list to English.

INSTRUCTIONS:
1. Translate each ingredient name to its standard English equivalent
2. Keep scientific/INCI names unchanged (e.g., "Aqua" stays "Aqua", "Sodium Lauryl Sulfate" stays the same)
3. Translate common ingredient names to English (e.g., "Eau" → "Water", "정제수" → "Purified Water")
4. Preserve the comma-separated format
5. Do not add any explanation or commentary
6. Return ONLY the translated ingredient list

INGREDIENT LIST TO TRANSLATE:
{ingredients_text}

TRANSLATED INGREDIENTS:"""
        )
        translated = response.text.strip()
        print(f"[DEBUG] Translated ingredients: {translated[:100]}...")
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        # Return original text if translation fails
        return ingredients_text


@app.post("/ocr", response_model=OCRResponse)
async def extract_text_from_image(request: OCRRequest):
    """Extract text from an image using Gemini Vision.

    Supports multi-language ingredient labels by automatically detecting
    and translating non-English text to English.

    Args:
        request: OCR request with base64 encoded image.

    Returns:
        Extracted text from the image (translated to English if needed).
    """
    try:
        # Initialize Gemini client
        client = genai.Client(api_key=settings.google_api_key)

        # Decode base64 image
        image_data = base64.b64decode(request.image)

        # Create image part for Gemini
        image_part = genai.types.Part.from_bytes(
            data=image_data,
            mime_type="image/jpeg"
        )

        # Use Gemini to extract ingredient text with focused prompt
        # Also detect language and indicate if translation is needed
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                image_part,
                """You are an expert at reading product ingredient labels in ANY language.

TASK: Find and extract ONLY the ingredient list from this product label image.

INSTRUCTIONS:
1. Look for ingredient list headers in ANY language:
   - English: "Ingredients:", "INGREDIENTS:"
   - French: "Ingrédients:", "COMPOSITION:"
   - Spanish: "Ingredientes:"
   - German: "Inhaltsstoffe:", "Zutaten:"
   - Italian: "Ingredienti:"
   - Korean: "성분:", "전성분:"
   - Japanese: "成分:", "全成分:"
   - Chinese: "成分:", "配料:"
   - Portuguese: "Ingredientes:"
   - And other languages...

2. Extract the complete list of ingredients that follows the header
3. Ingredients are typically comma-separated chemical/natural compound names
4. IGNORE everything else: brand names, product names, nutrition facts, directions, warnings, marketing text, barcodes

OUTPUT FORMAT:
First line: LANGUAGE_DETECTED: <language code or "en" for English>
Second line onwards: The extracted ingredients, comma-separated

- Do not include the "Ingredients:" header itself
- Do not add any explanation or commentary
- If multiple ingredient lists exist, extract all of them
- If no ingredient list is found, return:
  LANGUAGE_DETECTED: none
  NO_INGREDIENTS_FOUND

EXAMPLES:
For English label:
LANGUAGE_DETECTED: en
Water, Glycerin, Sodium Lauryl Sulfate, Fragrance

For Korean label:
LANGUAGE_DETECTED: ko
정제수, 글리세린, 나이아신아마이드, 부틸렌글라이콜

For French label:
LANGUAGE_DETECTED: fr
Eau, Glycérine, Parfum, Alcool"""
            ]
        )

        extracted_text = response.text.strip()

        # Parse the response to check language
        lines = extracted_text.split('\n', 1)
        detected_language = "en"
        ingredients_text = extracted_text

        if len(lines) >= 1 and lines[0].startswith("LANGUAGE_DETECTED:"):
            detected_language = lines[0].replace("LANGUAGE_DETECTED:", "").strip().lower()
            ingredients_text = lines[1].strip() if len(lines) > 1 else ""
            print(f"[DEBUG] Detected language: {detected_language}")

        if ingredients_text == "NO_INGREDIENTS_FOUND" or not ingredients_text:
            return OCRResponse(
                success=True,
                text="",
            )

        # Translate to English if non-English language detected
        if detected_language != "en" and detected_language != "none":
            print(f"[DEBUG] Non-English detected ({detected_language}), translating...")
            ingredients_text = _translate_ingredients_to_english(client, ingredients_text)

        return OCRResponse(
            success=True,
            text=ingredients_text,
        )

    except Exception as e:
        print(f"OCR error: {e}")
        return OCRResponse(
            success=False,
            text="",
            error=str(e),
        )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_ingredients_endpoint(request: AnalysisRequest):
    """Analyze ingredients for safety.

    Args:
        request: Analysis request with ingredients and user profile.

    Returns:
        Analysis results with safety assessment.
    """
    start_time = time.time()

    try:
        # Parse ingredients
        ingredients = [
            ing.strip()
            for ing in request.ingredients.replace("\n", ",").split(",")
            if ing.strip()
        ]

        if not ingredients:
            raise HTTPException(status_code=400, detail="No ingredients provided")

        # Generate session ID
        session_id = str(uuid.uuid4())

        # Run analysis with correct parameters
        result = run_analysis(
            session_id=session_id,
            product_name=request.product_name or "Unknown Product",
            ingredients=ingredients,
            allergies=request.allergies,
            skin_type=request.skin_type.lower(),
            expertise=request.expertise.lower(),
        )

        execution_time = time.time() - start_time

        # Check for errors
        if result.get("error"):
            return AnalysisResponse(
                success=False,
                product_name=request.product_name or "Unknown Product",
                overall_risk="unknown",
                average_safety_score=0,
                summary="",
                allergen_warnings=[],
                ingredients=[],
                execution_time=execution_time,
                error=result["error"],
            )

        # Extract report data
        report = result.get("analysis_report", {})
        ingredient_data = result.get("ingredient_data", [])
        assessments = report.get("assessments", [])

        # Debug logging
        print(f"[DEBUG] ingredient_data count: {len(ingredient_data)}")
        print(f"[DEBUG] assessments count: {len(assessments)}")
        print(f"[DEBUG] ingredient_data names: {[ing.get('name', 'UNNAMED') for ing in ingredient_data]}")

        # Get overall risk value
        overall_risk = report.get("overall_risk")
        if hasattr(overall_risk, "value"):
            overall_risk_str = overall_risk.value
        else:
            overall_risk_str = str(overall_risk) if overall_risk else "unknown"

        # Build structured ingredient details
        ingredients_list = []

        # Create a map of assessments by name for quick lookup
        assessment_map = {}
        for assessment in assessments:
            name = assessment.get("name", "").lower()
            assessment_map[name] = assessment

        # Combine ingredient_data with assessments
        for ing_data in ingredient_data:
            name = ing_data.get("name", "Unknown")
            name_lower = name.lower()

            # Find matching assessment
            assessment = assessment_map.get(name_lower, {})

            # Get risk level from assessment or derive from safety rating
            risk_level = assessment.get("risk_level")
            if hasattr(risk_level, "value"):
                risk_level_str = risk_level.value
            elif risk_level:
                risk_level_str = str(risk_level)
            else:
                # Derive from safety rating
                safety_rating = ing_data.get("safety_rating", 5)
                if safety_rating >= 7:
                    risk_level_str = "low"
                elif safety_rating >= 4:
                    risk_level_str = "medium"
                else:
                    risk_level_str = "high"

            # Get allergy risk flag
            allergy_risk = ing_data.get("allergy_risk_flag")
            if hasattr(allergy_risk, "value"):
                allergy_risk_str = allergy_risk.value
            else:
                allergy_risk_str = str(allergy_risk) if allergy_risk else "low"

            # Get recommendation, defaulting based on safety score
            recommendation = ing_data.get("recommendation", "")
            if not recommendation or recommendation == "None":
                safety_rating = ing_data.get("safety_rating", 5)
                if safety_rating >= 7:
                    recommendation = "SAFE"
                elif safety_rating >= 4:
                    recommendation = "CAUTION"
                else:
                    recommendation = "AVOID"

            # Get concerns
            concerns = ing_data.get("concerns", "")
            if not concerns or concerns == "None":
                concerns = "No specific concerns"

            ingredients_list.append(IngredientDetail(
                name=name,
                purpose=ing_data.get("purpose", "Unknown purpose"),
                safety_score=ing_data.get("safety_rating", 5),
                risk_level=risk_level_str,
                concerns=concerns,
                recommendation=recommendation,
                origin=ing_data.get("origin", "Unknown"),
                category=ing_data.get("category", "Unknown"),
                allergy_risk=allergy_risk_str,
                is_allergen_match=assessment.get("is_allergen_match", False),
                alternatives=assessment.get("alternatives", []),
            ))

        return AnalysisResponse(
            success=True,
            product_name=report.get("product_name", request.product_name),
            overall_risk=overall_risk_str,
            average_safety_score=report.get("average_safety_score", 5),
            summary=report.get("summary", ""),
            allergen_warnings=report.get("allergen_warnings", []),
            ingredients=ingredients_list,
            execution_time=execution_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
