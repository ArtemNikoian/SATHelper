# SATHelper
SATHelper is a project that will provide you with AI-generated authentic SAT questions, and let you practice efficiently by calculating your knowledge score on each topic.

## How to use
Find video explanation at https://youtu.be/I4UQ7WphsjI
### Getting Started
1. On the project's main screen, go to **Code** and select **Download ZIP**
2. Find the downloaded ZIP file and extract it to create the "SAT Helper-main" folder
3. Open your IDE (Visual Studio Code recommended)
4. Go to **File** > **Open Folder** and select the extracted folder

### Setting Up Dependencies
1. Check if any libraries are highlighted in yellow (indicating they're missing)
2. Create a virtual environment:
  - Open terminal in VS Code
  - Select interpreter and create virtual environment (venv)
  - Activate the environment with `source .venv/bin/activate`
  - Install required libraries with `pip install [library-name]`
  - You'll likely need to install Anthropic: `pip install anthropic`

## Core Components

### claude_gen.py (Question Generator)
This script generates SAT questions and requires several configurations:

1. **API Key Setup**:
  - You'll need an Anthropic API key
  - Create an account on Anthropic Console and add funds (about $5, which can generate ~500 questions)
  - Insert your API key in the designated field in the claude_gen.py

2. **INPUT_DATA_FILE Configuration**:
  - Go to the official SAT question bank website
  - Select one skill/topic
  - Export questions without answers or headers as PDF
  - Convert PDF to text using a converter
  - Ensure consistent question separation (adjust QUESTIONS_SEPARATOR if needed)
  - Copy the file path to the "INPUT_DATA_FILE" variable

3. **Topic Name Configuration**:
  - Use the exact topic name format from the existing files
  - Match the format in claude_gen.py, questions.json, and skill_data.csv
  - For consistency, copy the name from skill_data.csv

4. **Additional Settings**:
  - Set the number of questions to generate
  - Batch size: 4 (balance between accuracy and cost)
  - Leave other parameters at default unless you know what you're doing

## Using the Application

### Starting the Application
1. Go to main.py
2. Go to **Run** > **Run Without Debugging**
3. The main interface will open showing topics and scores

### Interface Features
- **Topic List**: Shows all topics with normalized scores (0-100)
- **Quick Add Buttons**: E±, M±, H± buttons to track questions done outside the app
 - E (Easy), M (Medium), H (Hard)
 - Plus (+) means correct, Minus (-) means incorrect
- **Search Bar**: Filter topics by name
- **Score Tracking**: Automatically updates when you solve questions

### Practice Mode
1. Select a topic that has questions available in questions.json
2. Click **Practice** for your desired difficulty level
4. View your time per question and get immediate feedback
5. Results automatically update your skill data

### Generating Questions
1. Configure claude_gen.py with topic details
2. Run the script to generate questions
3. Questions are added to questions.json
4. When practicing, answer choices are randomized

## Limitations and Notes
- Works best for Reading/Writing questions
- Math questions are challenging due to PDF-to-text conversion limitations with graphs and tables
- Clear button refreshes scores and sorts topics in ascending order
- Scores are stored in skill_data.csv for progress tracking
