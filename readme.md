SociAble: Social Practice Sandbox for Kids
SociAble is an interactive web application designed as a "social practice sandbox" primarily for autistic children. It provides a safe, predictable environment where kids can rehearse real-world social moments, receive visual emotional feedback, and learn the cause and effect of their words without real-world consequences.

🌟 Key Features
Scenario-Based Learning: Choose from several realistic environments like a Grocery Store, Playground, or Classroom.

Visual Emotional Feedback: Characters change their facial expressions and moods (Happy, Sad, Angry, Neutral) in real-time based on the child's input.

Vibe Check AI: A preventative filter that gently flags unkind language and suggests rephrasing instead of harsh correction.

Gamification & Rewards: Children earn coins for "Kind Moments" and milestone achievements, which can be spent in a Reward Shop for items like a Rainbow Theme, Star Borders, or a "Kindness Badge".

Speech Integration: Supports Speech-to-Text (STT) for input and AI-generated Text-to-Speech (TTS) for character replies (via ElevenLabs or Browser TTS).

Parent/Educator Dashboard: Detailed analytics and full conversation transcripts allow adults to review progress and identify specific social challenges.

🛠️ Technology Stack
Backend: Django 5.2.6 & Django REST Framework.

Frontend: Vanilla HTML5, CSS3, and JavaScript.

AI Models: Mistral AI (via Mistral Small) for roleplay and vibe checks.

Database: SQLite (default for development).

Third-Party APIs:

Mistral AI: Natural language processing.

ElevenLabs: High-quality Text-to-Speech (optional).

📂 Project Structure
/simulator: The main Django app containing the logic for chat, analytics, and reward systems.

/sociable_backend: Project settings and URL configurations.

/static: Character sprites and scenario background images.

index.html: The main interactive sandbox interface.

dashboard.html: The parent/educator analytics view.

📝 License
This project is part of the Autistic-Kids-Helper initiative. All rights reserved.
