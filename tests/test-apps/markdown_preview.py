
import os
import markdown

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QKeySequence, QShortcut

mark = """

## Install

`pip install labmate`

## Installation in dev mode

`pip install -e .[dev]`

or

`python setup.py develop`

## Usage

Start by looking inside
`docs/examples/acquisition_and_analysis_notebook.ipynb`

and don't be afraid by the other examples

```mermaid
%%{init: {'theme': 'neutral' } }%%
graph TB
    classDef changed fill:#f96;
    in3[in3: fluxo-readout] --> in3_4k
    in6[in6: TWPA] --> in6_4k
    in10[in10: DC-flux] --> in10_4k
    in12[in12: fluxo-charge] --> in12_4k
    out16[out16] -.-|"ᐱ"| out16_4k 


    subgraph 4K[4K]
        in3_4k(20dB)-->in3_800mk
        in6_4k(20dB)-->in6_800mk
        in10_4k(20dB)-->in10_800mk
        in12_4k(20dB)-->in12_800mk
        out16_4k(ampli) -.-|"ᐱ"| out16_800mk
        subgraph 800[800mK]
            in3_800mk(10dB)-->in3_100mk
            in6_800mk(10dB)-->in6_100mk
            in10_800mk(0dB)-->in10_100mk
            in12_800mk(10dB)-->in12_100mk
            out16_800mk(0dB) -.-|"ᐱ"| out16_100mk
            subgraph 100[100mK]
                in3_100mk(0dB) --> in3_10mk
                in6_100mk(0dB) --> in6_10mk
                in10_100mk(0dB) --> in10_10mk
                in12_100mk(0dB) --> in12_10mk
                out16_100mk(0dB) -.-|"ᐱ"| out16_10mk 
                subgraph 10[10mK]
                    out16_10mk_twpa(TWPA) -.- 10mk_dir_coupler(DC 20dB)
                    out16_10mk("↻\n↻") -.- out16_10mk_knl
                    out16_10mk_knl("KnL") -.- out16_10mk_twpa
                    in3_10mk(20dB):::changed --> in3_10mk_2
                    in3_10mk_2(20dB) --> in3_10mk_circ("↻\n↻")
                    in3_10mk_circ ---> jaws1
                    in3_10mk_circ --> 10mk_dir_coupler 
                    
                    in6_10mk ----> 10mk_dir_coupler
                    in10_10mk(VLFX500) --> in10_10mk_2
                    in10_10mk_2(SLP1.9+) ----> jaws5
                    in12_10mk(40dB) -----> jaws6
                    subgraph JAWS[JAWS]
                        jaws1(jaw1: readout fluxo)
                        jaws5(jaw5: fluxo flux)
                        jaws6(jaw6: drive flux)
                    end
                end
            end
        end
    end
```
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown Preview")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)

        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)

        self.text_edit.textChanged.connect(self.update_preview)
        self.preview_html = ""

        # Ctrl+R shortcut to refresh the preview
        shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut.activated.connect(self.update_preview)

        self.update_preview()

    def update_preview(self):
        markdown_text = self.text_edit.toPlainText()
        self.preview_html = self.convert_markdown_to_html(markdown_text)
        self.web_view.setHtml(self.preview_html)

    def convert_markdown_to_html(self, markdown_text):
        extensions = ["markdown.extensions.codehilite",
                      "markdown.extensions.fenced_code"]
        html = markdown.markdown(markdown_text, extensions=extensions)
        html_with_mermaid = self.inject_mermaid_code(html)
        return html_with_mermaid

    def inject_mermaid_code(self, html):
        mermaid_code = self.extract_mermaid_code()
        if mermaid_code:
            js_code = f"""
            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            <script>
                mermaid.initialize({{startOnLoad: true}});
            </script>
            <div class="mermaid">{mermaid_code}</div>
            """
            html = html.replace("</body>", js_code + "</body>")
        return html

    def extract_mermaid_code(self):
        import re

        mermaid_pattern = re.compile(
            r"<pre><code\s+class=\"language-mermaid\">(.*?)</code></pre>", re.DOTALL)
        matches = re.findall(mermaid_pattern, self.preview_html)
        mermaid_code = "\n".join(matches)
        return mermaid_code


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()

    app.exec()
