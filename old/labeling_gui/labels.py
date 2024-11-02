from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)

# Lade den Datensatz
with open(r'../../APIs/reddit/reddit_finance_posts.json', 'r') as f:
    data = json.load(f)

current_index = 0


@app.route('/')
def index():
    global current_index
    post = data[current_index]
    return render_template('index.html', post=post, index=current_index)


@app.route('/label', methods=['POST'])
def label():
    global current_index
    label = request.form['label']
    label_type = request.form.get('label_type')
    comment_index = request.form.get('comment_index')

    if label_type == 'post':
        data[current_index]['label'] = label
    elif label_type == 'comment' and comment_index is not None:
        comment_index = int(comment_index)
        if 'top_comments' in data[current_index] and comment_index < len(data[current_index]['top_comments']):
            data[current_index]['top_comments'][comment_index]['label'] = label

    # Speichere den aktualisierten Datensatz
    with open(r'../../APIs/reddit/reddit_finance_posts.json', 'w') as f:
        json.dump(data, f, indent=4)

    # Gehe zum nächsten Datensatz, wenn ein Post gelabelt wurde
    if label_type == 'post':
        current_index += 1
        if current_index >= len(data):
            current_index = 0  # Zurück zum Anfang, wenn das Ende erreicht ist

    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)