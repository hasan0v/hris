import os
from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document as DocxDocument
from flask import current_app

def parse_cv(filepath):
    """
    Parses text content from a CV file (PDF or DOCX).

    Args:
        filepath (str): The absolute path to the CV file.

    Returns:
        str: The extracted text content, or None if parsing fails or file type is unsupported.
    """
    _, file_extension = os.path.splitext(filepath)
    file_extension = file_extension.lower()

    try:
        if file_extension == '.pdf':
            current_app.logger.info(f"Parsing PDF: {filepath}")
            text = extract_pdf_text(filepath)
            current_app.logger.info(f"Successfully parsed PDF: {filepath}")
            return text
        elif file_extension == '.docx':
            current_app.logger.info(f"Parsing DOCX: {filepath}")
            document = DocxDocument(filepath)
            full_text = [para.text for para in document.paragraphs]
            text = '\n'.join(full_text)
            current_app.logger.info(f"Successfully parsed DOCX: {filepath}")
            return text
        else:
            current_app.logger.warning(f"Unsupported file type for parsing: {filepath}")
            return None
    except Exception as e:
        current_app.logger.error(f"Error parsing file {filepath}: {e}", exc_info=True)
        return None

# Added imports for OpenAI API call
import json
from openai import OpenAI

def get_openai_score(cv_text, vacancy_description):
    """
    Sends CV text and vacancy description to OpenAI for scoring.

    Args:
        cv_text (str): The parsed text from the CV.
        vacancy_description (str): The description of the vacancy.

    Returns:
        dict: A dictionary containing the score breakdown (e.g., {'experience': 4.5, ...}),
              or None if API call fails.
    """
    current_app.logger.info("Attempting to call OpenAI API...")

    # 1. Check for API Key in config
    api_key = current_app.config.get('OPENAI_API_KEY')
    if not api_key:
        current_app.logger.error("OpenAI API Key not configured.")
        return None

    # 2. Initialize OpenAI client
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
         current_app.logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
         return None

    # 3. Construct the prompt for GPT-4o JSON mode with detailed sections
    prompt = f"""
    Analyze the following CV text based on the job vacancy description.
    Provide a score from 0.0 to 5.0 (float) for EACH of the following sections:
    - relevant_experience_years: Years of experience directly relevant to the vacancy.
    - technical_skills_match: Alignment and proficiency of technical skills mentioned in the CV with those required by the vacancy.
    - education_level_relevance: Relevance of educational background (degree, field) to the vacancy requirements.
    - project_portfolio_quality: Quality and relevance of described projects or portfolio (if mentioned). Score lower if not mentioned or irrelevant.
    - keyword_alignment: Degree of relevant keyword overlap between CV and vacancy, but slightly penalize score if CV appears unnaturally stuffed with keywords.
    - communication_clarity: Inferred score based on the CV's structure, grammar, spelling, and overall clarity.

    Respond ONLY with a valid JSON object containing these keys and their corresponding float scores.

    Vacancy Description:
    ---
    {vacancy_description if vacancy_description else 'Not specified'}
    ---

    CV Text:
    ---
    {cv_text}
    ---

    JSON Output Format Example:
    {{
      "relevant_experience_years": 4.5,
      "technical_skills_match": 4.8,
      "education_level_relevance": 3.5,
      "project_portfolio_quality": 3.0,
      "keyword_alignment": 4.2,
      "communication_clarity": 4.0
    }}
    """

    # 4. Make the API call using client.chat.completions.create
    try:
        current_app.logger.info("Sending request to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o", # As specified in PRD
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are an expert CV analyst providing section scores from 0.0 to 5.0 in JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2 # Lower temperature for more deterministic scoring
        )
        json_response_str = response.choices[0].message.content
        current_app.logger.info(f"Raw response from OpenAI: {json_response_str}")

        # Parse the JSON string response
        score_data = json.loads(json_response_str)

        # Validate response structure against the new detailed keys
        expected_keys = [
            "relevant_experience_years", "technical_skills_match",
            "education_level_relevance", "project_portfolio_quality",
            "keyword_alignment", "communication_clarity"
        ]
        if not all(key in score_data for key in expected_keys):
             current_app.logger.error(f"OpenAI response missing expected keys: {score_data}")
             # Attempt to return partial data? Or fail? Failing for now.
             return None
        if not all(isinstance(score_data.get(key), (int, float)) for key in expected_keys):
             current_app.logger.error(f"OpenAI response contains non-numeric scores or missing keys: {score_data}")
             # Attempt to return partial data? Or fail? Failing for now.
             return None

        current_app.logger.info(f"Successfully received and parsed detailed score data from OpenAI: {score_data}")
        return score_data

    except Exception as e:
        current_app.logger.error(f"Error calling OpenAI API or parsing response: {e}", exc_info=True)
        return None
