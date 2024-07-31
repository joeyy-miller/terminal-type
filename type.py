import time
import random
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header as TextualHeader, Footer, Static, Input, Button
from textual import events
from textual.reactive import reactive
from textual.timer import Timer

EASY_WORDS = [
    "cat", "dog", "run", "jump", "play", "fast", "slow", "big", "small", "happy",
    "sad", "good", "bad", "hot", "cold", "wet", "dry", "up", "down", "left", "right"
]

NORMAL_SENTENCES = [
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

HARD_SENTENCES = [
    "The physicist's abstruse theory left the audience perplexed.",
    "The quintessential Renaissance man epitomized erudition and creativity.",
    "The cacophonous din of the metropolis assaulted her senses.",
    "The obsequious sycophant's flattery knew no bounds.",
    "The recalcitrant student's obstinacy frustrated the professor.",
    "The ephemeral nature of fame in the digital age is disconcerting.",
    "The juxtaposition of disparate elements created a surreal tableau.",
    "The loquacious raconteur regaled the crowd with anecdotes.",
    "The enigmatic artifact confounded archaeologists for decades.",
    "The palimpsest revealed layers of historical information.",
]

class Header(TextualHeader):
    """A header with updateable text."""

    def update_text(self, text: str) -> None:
        self.sub_title = text

class WPMHeader(Static):
    def __init__(self):
        super().__init__("WPM: 0 | Time left: 60s")

    def update_stats(self, wpm: int, time_left: int):
        self.update(f"WPM: {wpm} | Time left: {time_left}s")

class TypingTest(Static):
    words = reactive([])
    current_word_index = reactive(0)
    difficulty = reactive("normal")

    def __init__(self):
        super().__init__()
        self.reset()

    def generate_text(self):
        if self.difficulty == "easy":
            return " ".join(random.choices(EASY_WORDS, k=50))
        elif self.difficulty == "normal":
            return " ".join(random.sample(NORMAL_SENTENCES, k=len(NORMAL_SENTENCES)))
        else:  # hard
            return " ".join(random.sample(HARD_SENTENCES, k=len(HARD_SENTENCES)))

    def check_word(self, typed_word: str):
        if not self.start_time:
            self.start_time = time.time()

        correct = typed_word.strip() == self.words[self.current_word_index]
        self.words[self.current_word_index] = (
            f"[green]{self.words[self.current_word_index]}[/green]" if correct
            else f"[red]{self.words[self.current_word_index]}[/red]"
        )
        self.current_word_index += 1
        self.words_typed += 1

        if self.current_word_index >= len(self.words):
            self.words.extend(self.generate_text().split())

        self.update_content()

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

    def reset(self):
        self.words = []
        self.current_word_index = 0
        self.text = self.generate_text()
        self.words = self.text.split()
        self.start_time = None
        self.words_typed = 0
        self.update_content()

class TypingTestApp(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 1 4;
        grid-gutter: 1;
    }

    WPMHeader {
        content-align: center middle;
        background: $accent;
        color: $text;
        height: 3;
    }

    #difficulty-buttons {
        width: 100%;
        height: 3;
        layout: horizontal;
        content-align: center middle;
    }

    #test-container {
        width: 100%;
        height: 1fr;
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

    .help, .results {
        width: 100%;
        height: 100%;
        background: $panel;
        color: $text;
        padding: 1 2;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+h", "toggle_help", "Toggle Help"),
    ]

    def __init__(self):
        super().__init__()
        self.typing_test = TypingTest()
        self.time_left = 60
        self.wpm_header = WPMHeader()

    def compose(self) -> ComposeResult:
        yield self.wpm_header
        yield Container(
            Button("Easy", id="easy"),
            Button("Normal", id="normal"),
            Button("Hard", id="hard"),
            id="difficulty-buttons",
        )
        with Container(id="test-container"):
            yield self.typing_test
            yield Input(placeholder="Type the highlighted word and press space")
        yield Footer()

    def on_mount(self):
        self.typing_test.update_content()
        self.query_one(Input).focus()
        self.update_wpm_display()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.typing_test.difficulty = event.button.id
        self.typing_test.reset()
        self.time_left = 60
        self.update_wpm_display()

    def action_quit(self):
        self.exit()

    def action_toggle_help(self):
        if self.query("HelpScreen"):
            self.query_one("HelpScreen").remove()
        else:
            self.mount(HelpScreen())

    def on_input_changed(self, event: Input.Changed) -> None:
        if " " in event.value:
            word = event.value.strip()
            self.typing_test.check_word(word)
            event.input.value = ""
        self.update_wpm_display()

    def update_wpm_display(self):
        wpm = self.typing_test.calculate_wpm()
        self.wpm_header.update_stats(wpm, self.time_left)

    def on_input_submitted(self, event: Input.Submitted):
        if not hasattr(self, 'timer') or not self.timer.is_running:
            self.timer = self.set_interval(1, self.countdown)

    def countdown(self):
        self.time_left -= 1
        self.update_wpm_display()
        if self.time_left <= 0:
            self.timer.stop()
            self.show_results()

    def show_results(self):
        wpm = self.typing_test.calculate_wpm()
        percentile = self.calculate_percentile(wpm)
        self.query_one("#test-container").remove()
        self.mount(ResultsScreen(wpm, percentile))

    def calculate_percentile(self, wpm):
        # This is a simplified percentile calculation. You may want to use real typing speed data.
        if wpm < 30:
            return 10
        elif wpm < 50:
            return 25
        elif wpm < 70:
            return 50
        elif wpm < 90:
            return 75
        else:
            return 90
        
class HelpScreen(Static):
    def compose(self) -> ComposeResult:
        yield Static(
            "Typing Test Help\n\n"
            "- Choose difficulty: Easy, Normal, or Hard\n"
            "- Type the highlighted word in the input box\n"
            "- Press space to submit the word and move to the next one\n"
            "- Correct words turn green, incorrect words turn red\n"
            "- Your WPM (Words Per Minute) is displayed at the top\n"
            "- The timer counts down from 60 seconds\n"
            "- After time's up, you'll see your results and percentile\n"
            "- Press Ctrl+Q to quit the application\n"
            "- Press Ctrl+H to toggle this help screen\n\n"
            "Press any key to close this help screen",
            classes="help"
        )

    def on_key(self, event: events.Key):
        self.remove()

class ResultsScreen(Static):
    def __init__(self, wpm, percentile):
        super().__init__()
        self.wpm = wpm
        self.percentile = percentile

    def compose(self) -> ComposeResult:
        yield Static(
            f"""Typing Test Results

Your typing speed: {self.wpm} WPM
You are faster than {self.percentile}% of people

Graph:
{self.generate_graph()}

Press any key to start a new test""",
            classes="results"
        )

    def generate_graph(self):
        graph = "0   25   50   75   100\n"
        graph += "|----|----|----|----|\n"
        position = int(self.percentile / 100 * 20)
        graph += " " * position + "^"
        return graph

    def on_key(self, event: events.Key):
        self.app.query_one(TypingTest).reset()
        self.app.time_left = 60
        self.app.update_header()
        self.remove()
        self.app.query_one(Input).focus()

if __name__ == "__main__":
    app = TypingTestApp()
    app.run()