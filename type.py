import time
import random
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header as TextualHeader, Footer, Static, Input
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

class Header(TextualHeader):
    """A header with updateable text."""

    def update_text(self, text: str) -> None:
        self.sub_title = "terminal-type"

class TypingTest(Static):
    words = reactive([])
    current_word_index = reactive(0)

    def __init__(self):
        super().__init__()
        self.text = self.generate_text()
        self.words = self.text.split()
        self.start_time = None
        self.words_typed = 0

    def generate_text(self):
        return " ".join(random.sample(SENTENCES, k=len(SENTENCES)))

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

class TypingTestApp(App):
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
        ("ctrl+h", "toggle_help", "Toggle Help (c) Joey.com 2024"),
    ]

    def __init__(self):
        super().__init__()
        self.typing_test = TypingTest()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="test-container"):
            yield self.typing_test
            yield Input(placeholder="Type the highlighted word and press space")
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
        if " " in event.value:
            word = event.value.strip()
            self.typing_test.check_word(word)
            event.input.value = ""
        self.query_one(Header).update_text(f"WPM: {self.typing_test.calculate_wpm()}")

class HelpScreen(Static):
    def compose(self) -> ComposeResult:
        yield Static(
            "Typing Test Help\n\n"
            "- Type the highlighted word in the input box\n"
            "- Press space to submit the word and move to the next one\n"
            "- Correct words turn green, incorrect words turn red\n"
            "- Your WPM (Words Per Minute) is displayed at the top\n"
            "- Press Ctrl+Q to quit the application\n"
            "- Press Ctrl+H to toggle this help screen\n\n"
            "Press any key to close this help screen",
            classes="help"
        )

    def on_key(self, event: events.Key):
        self.remove()

if __name__ == "__main__":
    app = TypingTestApp()
    app.run()