from flask import Flask, request, jsonify
import PyPDF2
import os
import google.generativeai as genai

app = Flask(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("Fineprint"))
model = genai.GenerativeModel('gemini-1.5-flash')

def clean_analysis(text):
    unfair_clauses = []
    clauses = text.split("\n\n")  # Split into clauses

    for clause in clauses:
        if clause.strip():
            parts = clause.split("|||")  # Expecting your new format
            if len(parts) == 3:
                clause_text = parts[0].strip()
                risk = parts[1].strip()
                fix = parts[2].strip()
                unfair_clauses.append({
                    "clause": clause_text,
                    "risk": risk,
                    "fix": fix
                })
            # Handle cases where the model doesn't perfectly follow the format
            elif len(parts) > 0:
              clause_text = parts[0].strip()
              unfair_clauses.append({
                  "clause": clause_text,
                  "risk": "Not specified",
                  "fix": "Not provided"
              })

    return {
        "document_type": "contract",
        "summary": "Contract Analysis Complete",
        "unfair_clauses": unfair_clauses
    }

def format_analysis_for_layman(analysis_result):
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

        prompt = """
        Analyze the following contract and identify potentially unfair clauses. 
        Focus on clauses that could disadvantage one party.
        For each such clause, provide:

        1.  [EXACT QUOTE] - Copy the full clause text.
        2.  [RISK] - Explain the legal/business risk in plain language (1-2 sentences).
        3.  [FIX] - Suggest specific alternative wording to make it fairer.

        Separate each part with "|||".  Separate each clause analysis with two newlines.

        Example:
        1.  "Consultant may not replace staff without approval" ||| 
        2.  Risk: This gives the client excessive control and could delay the project if approval is slow. ||| 
        3.  Fix: "Consultant may replace staff with equally qualified personnel, with notice to Client."

        Pay special attention to:
        -   Termination clauses (especially unequal notice)
        -   Indemnification (if one-sided or overly broad)
        -   Intellectual property ownership
        -   Liability limitations
        -   Payment terms
        """

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
