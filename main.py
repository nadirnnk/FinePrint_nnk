from flask import Flask, request, jsonify
import PyPDF2
import os
import google.generativeai as genai

app = Flask(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("Fineprint"))
model = genai.GenerativeModel('gemini-1.5-pro')

def clean_analysis(text):
    satire_keywords = ["satirical", "teaching example", "demonstration", "how not to"]

    if any(keyword in text.lower() for keyword in satire_keywords):
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        purpose = ""
        positive_principles = []
        negative_examples = []

        for line in lines:
            if "**Teaching Purpose:**" in line:
                purpose = line.replace("**Teaching Purpose:**", "").strip()
            elif "**Key Lessons:**" in line:
                continue
            elif line.startswith("* ") and "**" in line:
                positive_principles.append(line[2:].replace("**", "").strip())
            elif "**Drafting Principles Demonstrated**" in line:
                continue
            elif line.startswith("* "):
                negative_examples.append(line[2:].replace("**", "").strip())

        return {
            "document_type": "educational",
            "summary": "Educational Content Detected",
            "key_insights": {
                "teaching_purpose": purpose,
                "key_principles": positive_principles,
                "anti_patterns": negative_examples
            }
        }
    else:
        unfair_clauses = []
        for clause in text.split("\n\n"):
            if clause.strip():
                parts = clause.split("\n")
                unfair_clauses.append({
                    "clause": parts[0].strip() if parts else "Not specified",
                    "risk": parts[1].strip() if len(parts) > 1 else "Not specified",
                    "fix": parts[2].strip() if len(parts) > 2 else "Not provided"
                })
        return {
            "document_type": "contract",
            "summary": "Contract Analysis Complete",
            "unfair_clauses": unfair_clauses
        }

def format_analysis_for_layman(analysis_result):
    if analysis_result["document_type"] == "educational":
        output = "This document appears to be for educational purposes.\n\n"
        output += f"**Teaching Objective:** {analysis_result['key_insights']['teaching_purpose']}\n\n"
        if analysis_result['key_insights']['key_principles']:
            output += "**Key Principles of Good Drafting:**\n"
            for principle in analysis_result['key_insights']['key_principles']:
                output += f"- {principle}\n"
            output += "\n"
        if analysis_result['key_insights']['anti_patterns']:
            output += "**Things to Avoid (Anti-Patterns):**\n"
            for anti_pattern in analysis_result['key_insights']['anti_patterns']:
                output += f"- {anti_pattern}\n"
        return output
    elif analysis_result["document_type"] == "contract":
        output = "This document appears to be a contract.\n\n"
        if analysis_result["unfair_clauses"]:
            output += "**Potentially Problematic Clauses Identified:**\n\n"
            for i, clause_analysis in enumerate(analysis_result["unfair_clauses"]):
                output += f"--- Clause {i+1} ---\n"
                output += f"**Quoted Text:** {clause_analysis['clause']}\n"
                output += f"**Potential Risk:** {clause_analysis['risk']}\n"
                output += f"**Suggested Fix:** {clause_analysis['fix']}\n\n"
        else:
            output += "No specific unfair clauses were identified in this initial analysis.\n"
        return output
    else:
        return "Analysis could not be formatted for layman's terms."

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        pdf_file = request.files['file']

        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Only PDF files are supported"}), 400

        try:
            text = PyPDF2.PdfReader(pdf_file).pages[0].extract_text()[:3000]
            if not text.strip():
                return jsonify({"error": "Empty PDF or no text extracted"}), 400
        except Exception as e:
            return jsonify({"error": f"PDF processing error: {str(e)}"}), 400

        prompt = """Analyze this contract. For each potentially unfair clause:
        1. [EXACT QUOTE] - Copy the full clause text
        2. [RISK] - Explain the legal/business risk (1-2 sentences)
        3. [FIX] - Suggest specific alternative wording

        Example:
        1. "Consultant may not replace staff without approval"
        2. Risk: Creates operational inflexibility if key staff leave
        3. Fix: "Consultant may replace staff with equally qualified personnel, with notice to Commission" 
        Pay special attention to:
- Termination clauses with unequal notice periods
- Overly broad indemnification language
- Intellectual property ownership clauses
- Insurance requirements that may be excessive"""

        response = model.generate_content(
            prompt + text,
            generation_config={"temperature": 0.2}
        )

        raw_output = response.text if hasattr(response, 'text') else str(response)
        cleaned = clean_analysis(raw_output)
        layman_output = format_analysis_for_layman(cleaned)

        return jsonify({"result_json": cleaned, "result_text": layman_output}), 200

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
