from tkinter import messagebox
import tkinter as tk
from datetime import datetime
import csv
from SkillTracker import SkillTracker
from QuestionManager import QuestionManager
import random
import time

# User Configuration
DATA_FILENAME = 'skill_data.csv'
QUESTIONS_FILENAME = 'questions.json'

MIN_WINDOW_WIDTH = 600
MIN_WINDOW_HEIGHT = 200
DEFAULT_TEXT_SIZE = 19
MIN_TEXT_SIZE = 8
MAX_TEXT_SIZE = 24
QUESTION_WRAP_LENGTH = 1000
CHOICE_WRAP_LENGTH = 1600
PRACTICE_WINDOW_SIZE = "2000x2000"

WINDOW_TITLE = "Skill Tracker"

class SkillTrackerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.tracker = SkillTracker(filename=DATA_FILENAME)
        
        self.root.attributes('-topmost', True)
        
        # Create search frame at the top
        self.search_frame = tk.Frame(self.root)
        self.search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create search entry
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.filter_topics)
        self.search_entry = tk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Create clear button
        self.clear_button = tk.Button(self.search_frame, text="Clear", command=self.clear_search)
        self.clear_button.pack(side=tk.RIGHT, padx=5)
        
        # Create main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=1)
        
        # Create canvas
        self.canvas = tk.Canvas(self.main_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        
        # Add scrollbar
        self.scrollbar = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Create frame inside canvas for topics
        self.topics_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.topics_frame, anchor='nw')
        
        # Update topics and create GUI elements
        self.update_topics()
        
        # Configure scrolling
        self.topics_frame.bind('<Configure>', self.on_frame_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Set minimum window size
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        
        self.root.mainloop()
        
    def clear_search(self):
        """Clear the search entry"""
        self.search_var.set('')
        self.update_topics()
        
    def filter_topics(self, *args):
        """Filter topics based on search text"""
        search_text = self.search_var.get().lower()
        
        # Show/hide frames based on search
        for frame in self.topics_frame.winfo_children():
            topic = frame.cget("text").lower()
            if search_text in topic:
                frame.pack(pady=5, padx=5, fill="x")
            else:
                frame.pack_forget()
                
    

    def on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """Make the inner frame the same width as the canvas"""
        width = event.width
        self.canvas.itemconfig(self.canvas.create_window((0, 0), window=self.topics_frame, anchor='nw'), width=width)

    def update_topics(self):
        data = self.tracker.load_data()
        topics = set(d['topic'] for d in data)
        
        # Sort topics by score
        topic_scores = [(topic, self.tracker.calculate_knowledge(topic)) for topic in topics]
        topics = [topic for topic, _ in sorted(topic_scores, key=lambda x: x[1])]
        
        # Clear existing topic frames
        for widget in self.topics_frame.winfo_children():
            widget.destroy()
        
        # Create frames for each topic
        for topic in topics:
            frame = tk.LabelFrame(self.topics_frame, text=topic)
            frame.pack(pady=5, padx=5, fill="x")
            
            # Score label
            score = self.tracker.calculate_knowledge(topic)
            score_label = tk.Label(frame, text=f"Score: {score:.2f}")
            score_label.pack()
            self.create_buttons(frame, topic, score_label)


    def create_buttons(self, frame, topic, score_label):
        difficulties = [('e', 'green'), ('m', 'orange'), ('h', 'red')]
        button_frame = tk.Frame(frame)
        button_frame.pack(pady=5)
        
        for diff, color in difficulties:
            wrong_btn = tk.Button(button_frame, text=f"{diff.title()} -", 
                                bg=color, 
                                command=lambda t=topic, d=diff, s=score_label: 
                                self.record_attempt(t, d, False, s))
            wrong_btn.pack(side=tk.LEFT, padx=5)
            
            right_btn = tk.Button(button_frame, text=f"{diff.title()} +", 
                                bg=color, 
                                command=lambda t=topic, d=diff, s=score_label: 
                                self.record_attempt(t, d, True, s))
            right_btn.pack(side=tk.LEFT, padx=5)
        
        def show_difficulty_menu(topic):
            menu = tk.Menu(self.root, tearoff=0)
            for diff, _ in difficulties:
                menu.add_command(label=diff.title(), 
                            command=lambda t=topic, d=diff: self.create_practice_window(t, d))
            menu.post(button_frame.winfo_pointerx(), button_frame.winfo_pointery())
        
        practice_btn = tk.Button(button_frame, text="Practice", 
                            command=lambda t=topic: show_difficulty_menu(t))
        practice_btn.pack(side=tk.LEFT, padx=5)

    def record_attempt(self, topic, difficulty, correct, score_label):
        data = self.tracker.load_data()
        
        new_attempt = {
            'topic': topic,
            'difficulty': difficulty,
            'correct': str(correct),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        data.append(new_attempt)
        
        with open(self.tracker.filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['topic', 'difficulty', 'correct', 'date'])
            writer.writeheader()
            writer.writerows(data)

        # Update the score display with timestamp
        score = self.tracker.calculate_knowledge(topic)
        current_time = datetime.now().strftime('%H:%M:%S')
        score_label.config(text=f"Score: {score:.2f} (Updated at {current_time})")
        
        # Flash the score label briefly to indicate update
        original_bg = score_label.cget("background")
        score_label.config(background="yellow")
        self.root.after(500, lambda: score_label.config(background=original_bg))
        
    def change_text_size(self, delta, question_label, choice_radios):
        """
        Change the text size of practice window elements
        delta: int - positive or negative value to change text size
        """
        min_size = MIN_TEXT_SIZE
        max_size = MAX_TEXT_SIZE
        
        new_size = self.current_text_size + delta
        if min_size <= new_size <= max_size:
            self.current_text_size = new_size
            
            # Update question text
            question_label.configure(font=('TkDefaultFont', self.current_text_size))
            
            # Update choice radio buttons
            for radio in choice_radios:
                radio.configure(font=('TkDefaultFont', self.current_text_size))
        
    def create_practice_window(self, topic, difficulty):
        practice_window = tk.Toplevel()
        practice_window.title(f"Practice - {topic} ({difficulty.title()})")
        practice_window.geometry(PRACTICE_WINDOW_SIZE)
        
        # Add text size tracking
        self.current_text_size = DEFAULT_TEXT_SIZE
        
        # Bind key events for text scaling
        practice_window.bind('<Command-plus>', lambda e: self.change_text_size(1, question_label, choice_radios))
        practice_window.bind('<Command-minus>', lambda e: self.change_text_size(-1, question_label, choice_radios))
        # For Windows/Linux support
        practice_window.bind('<Control-plus>', lambda e: self.change_text_size(1, question_label, choice_radios))
        practice_window.bind('<Control-minus>', lambda e: self.change_text_size(-1, question_label, choice_radios))
        # Additional bindings for the equals sign (since + requires shift)
        practice_window.bind('<Command-equal>', lambda e: self.change_text_size(1, question_label, choice_radios))
        practice_window.bind('<Control-equal>', lambda e: self.change_text_size(1, question_label, choice_radios))
        
        # Handle window close button (X)
        def on_closing():
            practice_window.destroy()
            self.root.deiconify()  # Show main window again
            self.update_topics()
        practice_window.protocol("WM_DELETE_WINDOW", on_closing)
        
        self.question_manager = QuestionManager(questions_file=QUESTIONS_FILENAME)
        
        # Create widgets
        question_frame = tk.Frame(practice_window)
        question_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Add a score display at the top of the practice window
        score = self.tracker.calculate_knowledge(topic)
        
        # Update question label creation
        question_label = tk.Label(question_frame, text="", 
                                wraplength=QUESTION_WRAP_LENGTH, 
                                justify=tk.LEFT,
                                font=('TkDefaultFont', self.current_text_size))
        question_label.pack(pady=20)
        
        choices_frame = tk.Frame(question_frame)
        choices_frame.pack(fill=tk.BOTH, expand=True)
        
        choice_var = tk.IntVar()
        choice_radios = []

        # Update radio button creation in the loop
        for i in range(4):
            # Create a frame to hold each radio button
            choice_frame = tk.Frame(choices_frame)
            choice_frame.pack(fill=tk.X, pady=5)
            
            radio = tk.Radiobutton(choice_frame, 
                                text="", 
                                variable=choice_var, 
                                value=i,
                                font=('TkDefaultFont', self.current_text_size),
                                wraplength=CHOICE_WRAP_LENGTH,  # Add wraplength
                                justify=tk.LEFT)  # Left-align the text
            radio.pack(anchor=tk.CENTER)
            choice_radios.append(radio)
        
        self.root.withdraw()
        
        self.timer_running = False
        self.start_time = 0
        self.timer_label = tk.Label(question_frame, text="Time: 0:00", 
                                font=('TkDefaultFont', self.current_text_size-2))
        self.timer_label.pack(pady=10)
        
        # Timer functions
        def start_timer():
            self.timer_running = True
            self.start_time = time.time()
            update_timer()
        
        def update_timer():
            if self.timer_running:
                elapsed = time.time() - self.start_time
                mins = int(elapsed // 60)
                secs = int(elapsed % 60)
                self.timer_label.config(text=f"Time: {mins}:{secs:02d}")
                practice_window.after(1000, update_timer)  # Update every second
        
        def reset_timer():
            self.timer_running = False
            self.timer_label.config(text="Time: 0:00")

        def load_new_question():
            question_data = self.question_manager.get_question(topic, difficulty)
            
            if not question_data:
                tk.messagebox.showinfo("No Questions", 
                                    "No more questions available for this topic and difficulty!")
                practice_window.destroy()
                self.root.deiconify()  # Show main window again
                return None
                
            question_label.config(text=question_data['question'])
            
            # Create a list of tuples containing (choice, is_correct)
            choices_with_answers = list(enumerate(question_data['choices']))
            
            # Shuffle the choices
            random.shuffle(choices_with_answers)
            
            # Update the correct answer index based on the shuffle
            new_correct_index = next(i for i, (old_index, _) in enumerate(choices_with_answers) 
                                if old_index == question_data['correct_answer'])
            
            # Update the choices in the GUI
            for i, (_, choice) in enumerate(choices_with_answers):
                choice_radios[i].config(text=choice)
            
            choice_var.set(-1)
            
            # Create a new question_data with updated correct_answer
            shuffled_question_data = {
                'question': question_data['question'],
                'choices': [choice for _, choice in choices_with_answers],
                'correct_answer': new_correct_index,
                'used': question_data.get('used', False)
            }
            
            return (shuffled_question_data, difficulty)
        
        def check_answer():
            if not hasattr(check_answer, 'current_question') or check_answer.current_question is None:
                return
                    
            self.timer_running = False
            question_data, current_diff = check_answer.current_question
            selected = choice_var.get()
            
            if selected == -1:
                result_label.config(text="Please select an answer!", fg="red")
                return
            
                    
            correct = selected == question_data['correct_answer']
            self.tracker.save_attempt(topic, current_diff, str(correct))
            
            self.question_manager.mark_question_as_used(topic, current_diff, question_data['question'])
            
            # Update result label instead of showing popup
            if correct:
                result_label.config(text="Correct!", fg="green")
            else:
                result_label.config(
                    text=f"Incorrect!",
                    fg="red"
                )
            
            # Update the knowledge score after each submission
            new_score = self.tracker.calculate_knowledge(topic)
            score_label.config(text=f"Score: {new_score:.2f}")
            
            # Flash the score label briefly to indicate update
            original_bg = score_label.cget("background")
            score_label.config(background="yellow")
            practice_window.after(500, lambda: score_label.config(background=original_bg))
            
            # Disable submit button and enable next question button
            submit_button.config(state='disabled')
            next_button.config(state='normal')
            
            # Disable radio buttons after submission
            for radio in choice_radios:
                radio.config(state='disabled')

        def next_question():
            # Enable submit button and disable next question button
            submit_button.config(state='normal')
            next_button.config(state='disabled')
            
            reset_timer()
            start_timer()
            
            # Enable radio buttons
            for radio in choice_radios:
                radio.config(state='normal')
            
            # Clear the result label
            result_label.config(text="")
            
            # Load new question
            check_answer.current_question = load_new_question()

        # Create button frame
        # Create button frame
        button_frame = tk.Frame(question_frame)
        button_frame.pack(pady=20)
        
        score_label = tk.Label(button_frame, 
                            text=f"Score: {score:.2f}", 
                            font=('TkDefaultFont', self.current_text_size-2),
                            fg="white")
        score_label.pack(side = tk.LEFT, padx=10)

        # Add submit button
        submit_button = tk.Button(button_frame, text="Submit", command=check_answer)
        submit_button.pack(side=tk.LEFT, padx=10)

        # Add next question button (initially disabled)
        next_button = tk.Button(button_frame, text="Next Question", command=next_question, state='disabled')
        next_button.pack(side=tk.LEFT, padx=10)

        # Add return button
        def return_to_main():
            practice_window.destroy()
            self.root.deiconify()  # Show main window again
            
        return_button = tk.Button(button_frame, text="Return to Topics", command=return_to_main)
        return_button.pack(side=tk.LEFT, padx=10)
        
        result_label = tk.Label(button_frame, text="", font=('TkDefaultFont', self.current_text_size))
        result_label.pack(side=tk.LEFT, padx=10)
        
        # Load the first question immediately
        start_timer()
        check_answer.current_question = load_new_question()

if __name__ == "__main__":
    app = SkillTrackerGUI()