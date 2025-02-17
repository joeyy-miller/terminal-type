import time
import random
import asyncio
import statistics
import sys
import argparse
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Static, Input
from textual import events
from textual.reactive import reactive

SENTENCES = [
    "The quick brown fox jumps over the lazy dog.",
    "A journey of a thousand miles begins with a single step.",
    "To be or not to be, that is the question.",
    "All that glitters is not gold.",
    "Where there's a will, there's a way.",
    "Actions speak louder than words.",
    "Knowledge is power.",
    "Practice makes perfect.",
    "Time flies like an arrow; fruit flies like a banana.",
    "Better late than never.",
]

DEFAULT_TIME = 60  # 60 seconds

class TypingTest(Static):
    words = reactive([])
    current_word_index = reactive(0)
    countdown = reactive(0)

    def __init__(self, test_duration, debug=False):
        super().__init__()
        self.debug = debug
        self.test_duration = test_duration
        self.countdown = test_duration  # Initialize without reactive()
        self.text = self.generate_text()
        self.words = self.text.split()
        self.start_time = None
        self.words_typed = 0
        self.timer_task = None
        self.correct_words = 0
        self.incorrect_words = 0
        self.total_keystrokes = 0

    def generate_text(self):
        return " ".join(random.sample(SENTENCES, k=len(SENTENCES)))

    def check_word(self, typed_word: str):
        self.total_keystrokes += len(typed_word) + 1  # +1 for space
        if not self.start_time:
            self.start_time = time.time()

        correct = typed_word.strip() == self.words[self.current_word_index]
        if correct:
            self.correct_words += 1
            self.words[self.current_word_index] = f"[green]{self.words[self.current_word_index]}[/green]"
        else:
            self.incorrect_words += 1
            self.words[self.current_word_index] = f"[red]{self.words[self.current_word_index]}[/red]"
        
        self.current_word_index += 1
        self.words_typed += 1

        if self.current_word_index >= len(self.words):
            self.words.extend(self.generate_text().split())

        self.update_content()
        if self.debug:
            self.notify("words")

    def update_content(self):
        content = ""
        if self.current_word_index < len(self.words):
            content = f"[gray]{self.words[self.current_word_index]}[/gray] "
        content += " ".join(self.words[self.current_word_index + 1:])
        if self.current_word_index > 0:
            content = " ".join(self.words[:self.current_word_index]) + " " + content
        self.update(content.strip())

    def calculate_wpm(self):
        if self.start_time:
            elapsed_time = time.time() - self.start_time
            minutes = elapsed_time / 60
            return int(self.words_typed / minutes)
        return 0

    async def start_countdown(self):
        if not self.start_time:
            self.start_time = time.time()
            self.timer_task = asyncio.create_task(self.countdown_timer())

    async def countdown_timer(self):
        while self.countdown > 0:
            await asyncio.sleep(1)
            self.update_countdown()

    def update_countdown(self):
        elapsed = int(time.time() - self.start_time)
        self.countdown = max(self.test_duration - elapsed, 0)
        if self.debug:
            self.notify("countdown")
        if self.countdown == 0:
            self.show_end_screen()

    def show_end_screen(self):
        final_wpm = self.calculate_wpm()
        total_words = self.correct_words + self.incorrect_words
        accuracy = (self.correct_words / total_words) * 100 if total_words > 0 else 0

        graph = self.create_percentile_graph(final_wpm)

        end_message = f"""
    Time's up! Here are your results:

    Final WPM: {final_wpm}
    Accuracy: {accuracy:.2f}%
    Correct words: {self.correct_words}
    Incorrect words: {self.incorrect_words}
    Total keystrokes: {self.total_keystrokes}

    {graph}
        """
        self.update(end_message)

    def create_percentile_graph(self, wpm):
        percentile = self.wpm_to_percentile(wpm)
        graph = "Your performance:\n"
        graph += "0    30   60   90   120 WPM\n"
        graph += "│    │    │    │    │\n"
        
        total_width = 24  # 24 characters to represent 0-120 WPM (5 WPM per character)
        filled = min(int(wpm / 5), total_width)
        
        bar = "█" * filled
        if filled < total_width:
            bar += "▒"
            bar += "░" * (total_width - filled - 1)
        
        graph += f"{bar}│\n"
        graph += "│    │    │    │    │\n"
        
        # Add marker for user's WPM
        marker_position = min(int(wpm / 5), total_width)
        marker = " " * marker_position + "▲"
        graph += f"{marker}\n"
        
        graph += f"Your WPM: {wpm} (Estimated {percentile:.0f}th percentile)\n\n"
        
        # Add performance interpretation
        if percentile < 25:
            graph += "Keep practicing! You're on your way to improvement."
        elif percentile < 50:
            graph += "Good effort! You're making progress."
        elif percentile < 75:
            graph += "Great job! You're above average."
        else:
            graph += "Excellent! You're among the top performers."
        
        return graph

    def wpm_to_percentile(self, wpm):
        # This is a rough estimation. You might want to use actual typing speed distribution data.
        if wpm < 30:
            return max(wpm / 30 * 25, 1)
        elif wpm < 60:
            return 25 + (wpm - 30) / 30 * 25
        elif wpm < 90:
            return 50 + (wpm - 60) / 30 * 25
        else:
            return min(75 + (wpm - 90) / 30 * 25, 99)

    def notify(self, message: str) -> None:
        if self.debug:
            super().notify(message)

class TerminalType(App):
    CSS = """
    Screen {
        align: center middle;
    }

    #test-container {
        width: 80%;
        height: 60%;
        border: solid green;
        padding: 1 2;
    }

    #typing-test {
        height: 100%;
        overflow-y: scroll;
    }

    Input {
        dock: bottom;
    }

    .help {
        width: 100%;
        height: 100%;
        background: $panel;
        color: $text;
        padding: 1 2;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+h", "toggle_help", "Toggle Help (c) Joey Miller 2024"),
    ]

    def __init__(self, test_duration, debug=False):
        super().__init__()
        self.typing_test = TypingTest(test_duration=test_duration, debug=debug)
        self.title = "Terminal Type"

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="test-container"):
            yield self.typing_test
            yield Input(placeholder="Type the highlighted word and press space...")
        yield Footer()

    def on_mount(self):
        self.typing_test.update_content()
        self.query_one(Input).focus()

    def action_quit(self):
        self.exit()

    def action_toggle_help(self):
        if self.query("HelpScreen"):
            self.query_one("HelpScreen").remove()
        else:
            self.mount(HelpScreen())

    def on_input_changed(self, event: Input.Changed) -> None:
        if not self.typing_test.start_time:
            asyncio.create_task(self.typing_test.start_countdown())

        if " " in event.value:
            word = event.value.strip()
            self.typing_test.check_word(word)
            event.input.value = ""
        
        self.update_header()

    def update_header(self):
        wpm = self.typing_test.calculate_wpm()
        countdown = self.typing_test.countdown  # Access countdown directly
        
        # Show debug mode in the title if enabled
        if (debug_mode := getattr(self.typing_test, "debug", False)):
            self.title = f"Terminal Type (Debug Mode: {debug_mode})"
        
        self.sub_title = f"WPM: {wpm} | Time Left: {countdown}s"

    def on_typing_test_countdown(self):
        self.update_header()

    def on_typing_test_words(self):
        self.update_header()

class HelpScreen(Static):
    def compose(self) -> ComposeResult:
        yield Static(
            "Terminal Type Help\n\n"
            "- Type the highlighted word in the input box\n"
            "- Press space to submit the word and move to the next one\n"
            "- Correct words turn green, incorrect words turn red\n"
            "- Your WPM (Words Per Minute) is displayed at the top\n"
            "- Press Ctrl+Q to quit the application\n"
            "- Press Ctrl+H to toggle this help screen\n\n"
            "Press any key to close this help screen\n"
            "Made by Joey Miller in 2024"
        )

    def on_key(self, event: events.Key):
        self.remove()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Terminal Type - A typing test application")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-t", "--time", type=int, default=DEFAULT_TIME, help="Test duration in seconds")
    args = parser.parse_args()

    app = TerminalType(test_duration=args.time, debug=args.debug)
    app.run()