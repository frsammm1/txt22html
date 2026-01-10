
import sys
# Add the current directory to the path to import bot
sys.path.append('.')
from bot import generate_html, parse_txt_content

# Sample data
sample_txt_content = """
[Chapter 1: Introduction to Python]
Introduction Video: https://www.youtube.com/watch?v=1234
Chapter 1 Slides: https://example.com/chapter1.pdf
Sample Image: https://example.com/sample.jpg

[Chapter 2: Data Structures]
Lists and Tuples: https://www.youtube.com/watch?v=5678
Chapter 2 Notes: https://example.com/chapter2.pdf
Another File: https://example.com/another.zip
"""

password = "testpassword"
batch_name = "Test Batch"
credit_name = "Test Developer"

# Parse the content
categories = parse_txt_content(sample_txt_content)

# Generate the HTML
html_output = generate_html(categories, password, batch_name, credit_name)

# Save the HTML to a file
with open("test_output.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("test_output.html generated successfully.")
